#include <Arduino.h>
#include "stm32g4xx_hal.h"    // needed for HAL_DeInit

#include <SPI.h>

#include <SimpleFOC.h>
#include <SimpleFOCDrivers.h>

#include "encoders/as5048a/MagneticSensorAS5048A.h"
#include "drivers/drv8316/drv8316.h"
#include "utilities/stm32math/STM32G4CORDICTrigFunctions.h"

#include "i2c_register_map.h"

#define CONN_WATCHDOG_TIMEOUT 1000

#define POLE_PAIRS 7

#define SPI1_SCK   PA5
#define SPI1_MISO  PA6   
#define SPI1_MOSI  PA7

#define DRV_CS     PB2 
#define ENC_CS     PB1

#define PHA_H   PA10
#define PHA_L   PB15

#define PHB_H   PA9
#define PHB_L   PB14

#define PHC_H   PA8
#define PHC_L   PB13

#define SO_A    PA0
#define SO_B    PA1
#define SO_C    PA2


SPIClass SPI_1(SPI1_MOSI, SPI1_MISO, SPI1_SCK);

// BLDC motor & driver instance
// BLDCMotor( pp number , phase resistance, KV rating)
BLDCMotor motor = BLDCMotor(POLE_PAIRS, 1.53, 290);
//BLDCMotor motor = BLDCMotor(POLE_PAIRS);

//  BLDCDriver6PWM( int phA_h, int phA_l, int phB_h, int phB_l, int phC_h, int phC_l, int en)
//  - phA_h, phA_l - A phase pwm pin high/low pair 
//  - phB_h, phB_l - B phase pwm pin high/low pair
//  - phB_h, phC_l - C phase pwm pin high/low pair
DRV8316Driver6PWM driver = DRV8316Driver6PWM(PHA_H, PHA_L, PHB_H, PHB_L, PHC_H, PHC_L, DRV_CS, false);

LowsideCurrentSense current_sense  = LowsideCurrentSense(600.0,  SO_A, SO_B, SO_C);

MagneticSensorAS5048A sensor(ENC_CS, false, SPISettings(5'000'000, MSBFIRST, SPI_MODE1));

float target_current = 0.0;

float voltage_limit = 10;  // driver voltage limit
float PSU_voltage = 12.0;

char serialBuff[32];

bool FOC_started = false;

uint32_t lastConnWatchdogMsg;

bool connectionWatchdog = HIGH;

volatile uint8_t currentRegister = 0;
volatile bool registerSet = false;

void receiveEvent(int howMany);
void requestEvent();

void float2bytesMSB(float val, uint8_t *bytes) {
    // Copy the raw bits of val into an integer so can perform
    // bitwise operations
    uint32_t valAsInt;
    memcpy(&valAsInt, &val, sizeof(float));

    // Extract the bytes in big-endian (MSB-first) order
    bytes[0] = (valAsInt >> 24) & 0xFF;
    bytes[1] = (valAsInt >> 16) & 0xFF;
    bytes[2] = (valAsInt >> 8)  & 0xFF;
    bytes[3] = (valAsInt >> 0)  & 0xFF;
}

float bytes2floatMSB(const uint8_t *bytes) {
    // Readt the bytes in big-endian (MSB-first) order
    uint32_t valAsInt = 
        ((uint32_t)bytes[0] << 24) |
        ((uint32_t)bytes[1] << 16) |
        ((uint32_t)bytes[2] << 8)  |
        ((uint32_t)bytes[3]);

    // Copy the raw bits to a float and return
    float val;
    memcpy(&val, &valAsInt, sizeof(float));

    return val;
}


void rebootToDFU() {
    __disable_irq();

    // Stop SysTick
    SysTick->CTRL = 0;

    // Deinit HAL (shuts down peripherals & interrupts)
    HAL_RCC_DeInit();
    HAL_DeInit();

    // ---- Disable USB (STM32G431 version) ----

    // Disable USB clock
    RCC->APB1ENR1 &= ~RCC_APB1ENR1_USBEN;

    // Reset USB peripheral
    RCC->APB1RSTR1 |=  RCC_APB1RSTR1_USBRST;
    RCC->APB1RSTR1 &= ~RCC_APB1RSTR1_USBRST;

    // Reset USB pins PA11/PA12 to analog
    __HAL_RCC_GPIOA_CLK_ENABLE();
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    GPIO_InitStruct.Pin = GPIO_PIN_11 | GPIO_PIN_12;
    GPIO_InitStruct.Mode = GPIO_MODE_ANALOG;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    // Remap system memory to 0x00000000
    SYSCFG->MEMRMP = SYSCFG_MEMRMP_MEM_MODE_0;

    // System memory bootloader start
    uint32_t bootAddr = 0x1FFF0000;

    // Load stack pointer and reset vector
    uint32_t sp = *(__IO uint32_t*)(bootAddr);
    uint32_t rv = *(__IO uint32_t*)(bootAddr + 4);

    // Set main stack pointer
    __set_MSP(sp);

    // Jump to bootloader
    ((void (*)(void))rv)();
}

void printDRV8316Status() {
  DRV8316Status status = driver.getStatus();
	Serial.println("DRV8316 Status:");
	Serial.print("Fault: ");
	Serial.println(status.isFault());
	Serial.print("Buck Error: ");
	Serial.print(status.isBuckError());
	Serial.print("  Undervoltage: ");
	Serial.print(status.isBuckUnderVoltage());
	Serial.print("  OverCurrent: ");
	Serial.println(status.isBuckOverCurrent());
	Serial.print("Charge Pump UnderVoltage: ");
	Serial.println(status.isChargePumpUnderVoltage());
	Serial.print("OTP Error: ");
	Serial.println(status.isOneTimeProgrammingError());
	Serial.print("OverCurrent: ");
	Serial.print(status.isOverCurrent());
	Serial.print("  Ah: ");
	Serial.print(status.isOverCurrent_Ah());
	Serial.print("  Al: ");
	Serial.print(status.isOverCurrent_Al());
	Serial.print("  Bh: ");
	Serial.print(status.isOverCurrent_Bh());
	Serial.print("  Bl: ");
	Serial.print(status.isOverCurrent_Bl());
	Serial.print("  Ch: ");
	Serial.print(status.isOverCurrent_Ch());
	Serial.print("  Cl: ");
	Serial.println(status.isOverCurrent_Cl());
	Serial.print("OverTemperature: ");
	Serial.print(status.isOverTemperature());
	Serial.print("  Shutdown: ");
	Serial.print(status.isOverTemperatureShutdown());
	Serial.print("  Warning: ");
	Serial.println(status.isOverTemperatureWarning());
	Serial.print("OverVoltage: ");
	Serial.println(status.isOverVoltage());
	Serial.print("PowerOnReset: ");
	Serial.println(status.isPowerOnReset());
	Serial.print("SPI Error: ");
	Serial.print(status.isSPIError());
	Serial.print("  Address: ");
	Serial.print(status.isSPIAddressError());
	Serial.print("  Clock: ");
	Serial.print(status.isSPIClockFramingError());
	Serial.print("  Parity: ");
	Serial.println(status.isSPIParityError());
	if (status.isFault())
		driver.clearFault();
	delayMicroseconds(1); // ensure 400ns delay
	DRV8316_PWMMode val = driver.getPWMMode();
	Serial.print("PWM Mode: ");
	Serial.println(val);
	delayMicroseconds(1); // ensure 400ns delay
	bool lock = driver.isRegistersLocked();
	Serial.print("Lock: ");
	Serial.println(lock);
}

void setupFOC() {
    // initialise magnetic sensor hardware
    sensor.init(&SPI_1);
    // link the motor to the sensor
    motor.linkSensor(&sensor);

    driver.voltage_power_supply = PSU_voltage;
    driver.voltage_limit = voltage_limit;

    driver.init(&SPI_1);

    // small delay to allow SPI response
    delay(10);

    // Set the buck output to 3.3V
    driver.setBuckVoltage(VB_3V3);
    // Wait some time for everything to stabilise
    delay(500);

    // It's advised to have at least 400ns between read and write calls
    driver.setOCPLevel(Curr_16A);
    delayMicroseconds(1);
    driver.setOCPMode(AutoRetry_Fault);
    delayMicroseconds(1);
    driver.setOCPRetryTime(Retry500ms);
    delayMicroseconds(1);
    driver.setSlew(Slew_200Vus);
    delayMicroseconds(1);
    driver.setPWM100Frequency(FREQ_20KHz);
    delayMicroseconds(1);
    //driver.setCurrentSenseGain(Gain_0V15); // Set the current sense gain to 150 mV/A
    driver.setCurrentSenseGain(Gain_0V25); // Set the current sense gain to 600 mV/A
    //driver.setCurrentSenseGain(Gain_0V375); // Set the current sense gain to 1200 mV/A
    delayMicroseconds(1);
    // Serial.print("Current gain:");
    // Serial.println("here 1");
    // Serial.println(driver.getCurrentSenseGain()); 
    // Serial.println("here 2");
    // delayMicroseconds(1);
    //driver.setPWMMode(PWM6_Mode);
    driver.setPWMMode(PWM6_Mode);
    delayMicroseconds(1);

    Serial.println("Init complete...");

    delay(100);
    printDRV8316Status();


    motor.current_limit = 5;   // [Amps]

    current_sense.linkDriver(&driver);

    // Link driver to the motor
    motor.linkDriver(&driver);

    // aligning voltage 
    motor.voltage_sensor_align = 4.5;
    // choose FOC modulation 
    motor.foc_modulation = FOCModulationType::SinePWM;

    //motor.controller = MotionControlType::velocity;


    motor.torque_controller = TorqueControlType::foc_current;
    //motor.torque_controller = TorqueControlType::voltage;
    
    motor.controller = MotionControlType::torque;
    
    // setting target velocity
    //motor.target = target_current;
    motor.target = 0;

    //  // calculate the filter time constant 
    // // based on the max velocity you need 
    // // and the rule of thumb for the cutoff frequency
    // float max_velocity = 5.0;                       // rad/s
    // float motor_frequency_hz = max_velocity / (2 * PI); 
    // // velocity low pass filtering time constant
    // motor.LPF_velocity.Tf = 1.0 / (2.0 * PI * motor_frequency_hz * 5); 

    //   // default P=0.5 I = 10 D =0
    // motor.PID_velocity.P = 0.1;
    // motor.PID_velocity.I = 0.008;

    // // limiting motor current (provided resistance)
    // motor.updateCurrentLimit(4);   // [Amps]
    // motor.updateVelocityLimit(5);  // [rad/s]

    
    // // comment out if not needed
    motor.useMonitoring(Serial);

}

void startFOC() {
    // initialize motor
    motor.init();

    if (current_sense.init())  Serial.println("Current sense init success!");
    else{
        Serial.println("Current sense init failed!");
        return;
    }
      // link the current sense to the motor
    motor.linkCurrentSense(&current_sense);


     // align encoder and start FOC
    motor.initFOC();


    // add target command T
    // command.add('T', doTarget, "target voltage");

    Serial.println(F("Motor ready."));
    // Serial.println(F("Set the target voltage: - command T"));

    //enabled = true;
    
    _delay(1000);
}

void setup() {
    
    pinMode(LED_BUILTIN, OUTPUT);

    pinMode(DRV_CS, OUTPUT);
    pinMode(ENC_CS, OUTPUT);

    pinMode(SO_A, INPUT);
    pinMode(SO_B, INPUT);
    pinMode(SO_C, INPUT);

    SimpleFOCDebug::enable(&Serial);

    SimpleFOC_CORDIC_Config();

    Serial.begin(115200);

    Wire.begin(I2C_ADDR);
    Wire.setClock(400000);
    Wire.onRequest(requestEvent);
    Wire.onReceive(receiveEvent);

    // while (!Serial) {
    //     digitalWrite (LED_BUILTIN, !digitalRead (LED_BUILTIN)) ;
    //     delay (50) ;
    // }

    delay(5000);


    setupFOC();

    //startFOC();

    //target_current = 0.1;
}

void loop() {
    // --------------------------------------------------------- //
    //                    DFU Reset Triggers                     //
    // --------------------------------------------------------- //

    // Trigger dfu if "dfu" received from Serial
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();

        if (cmd == "dfu") {
            Serial.println("Entering DFU mode...");
            delay(10);        // let USB send the message
            rebootToDFU();
        }
    }

    uint32_t currentTime = millis();
    if (currentTime - lastConnWatchdogMsg > CONN_WATCHDOG_TIMEOUT) {
      target_current = 0.0;
    }

    // while (Serial.available() > 0) {
    //     // Clear the buffer
    //     memset(serialBuff, 0, sizeof(serialBuff) / sizeof(char));

    //     Serial.readBytesUntil('\n', serialBuff, sizeof(serialBuff) / sizeof(char));
    //     Serial.println(serialBuff);

    //     // Tokenize the received char array to split at the whitespaces
    //     char* token = strtok(serialBuff, " ");
    //     uint8_t idx = 0;

    //     char *outArray[10];
    //     while (token != NULL) {
    //         outArray[idx] = token;
    //         idx++;
    //         token = strtok(NULL, " ");
    //     }
    //     uint8_t outArrayLength = idx;

    //     if (!strcmp(outArray[0], "dfu")) {
    //         Serial.println("Entering DFU mode...");
    //         delay(10);        // let USB send the message
    //         rebootToDFU();
    //     }

    //     else if (!strcmp(outArray[0], "C")) {
    //         target_current = atof(outArray[1]);
    //         if (abs(target_current) <= 8 ) {
    //             motor.target = target_current;
    //         }
    //     }    
    // }

  // --------------------------------------------------------- //
  //                         SimpleFOC                         //
  // --------------------------------------------------------- //

  // Run the FOC loop commands

  motor.loopFOC();
  motor.move(target_current);
  //motor.move();


  // --------------------------------------------------------- //
  //                       End of Loop()                       //
  // --------------------------------------------------------- //
}

// function that executes whenever data is received from master
void receiveEvent(int howMany) {
  if (howMany < 1) return;
  
  // First byte is always the register address
  currentRegister = Wire.read();
  registerSet = true;
  
  // If there's more data, it's a write to that register
  if (howMany > 1) {
    Serial.print("Write to register 0x");
    Serial.print(currentRegister, HEX);
    Serial.print(": ");
    
    uint8_t buffer[32];  // Max I2C buffer size
    memset(buffer, 0, sizeof(buffer));  // Clear the buffer
    
    uint8_t index = 0;
    while(Wire.available() && index < sizeof(buffer)) {
      buffer[index++] = Wire.read();
    }

    switch(currentRegister) {
      case REG_MOTOR_CURRENT:
        target_current = bytes2floatMSB(buffer);
        Serial.println("Received MOTOR_CURRENT: " + String(target_current, 3));
        break;

      case REG_STARTFOC:
        if (buffer[0] == 0x01) {
          if (!FOC_started) {
            startFOC();
            FOC_started = true;
            Serial.println("FOC started.");
          } else {
            Serial.println("FOC already started.");
          }
        } else {
          Serial.println("Invalid value for STARTFOC. Use 0x01 to start.");
        }
        break;

        case REG_CONN_WATCHDOG:
          if (buffer[0] == 0x01) {
            lastConnWatchdogMsg = millis();
          }
    //   case REG_LED:
    //       digitalWrite(LED_BUILTIN, buffer[0]);

    //       Serial.printf("LED %s\n", buffer[0] ? "ON" : "OFF");
    //       break;
    }
  }
}

// function that executes whenever data is requested by master
void requestEvent() {
  if (!registerSet) {
    Wire.write("ERR");
    return;
  }
  
  // Respond based on the register that was set
  switch(currentRegister) {
      
    case REG_STATUS:
      Wire.write(0x42);  // Example status byte
      break;

    case REG_MOTOR_CURRENT: {
      float current = target_current;
      uint8_t data[4];
      float2bytesMSB(current, data);
      Serial.printf("Sending MOTOR_CURRENT: %#x %#x %#x %#x\n", data[0], data[1], data[2], data[3]);
      Wire.write(data, 4);
      break;
    }

    case REG_ENCODER_VELOCITY: {
      float velocity = motor.shaftVelocity();
      uint8_t data[4];
      float2bytesMSB(velocity, data);
      Serial.printf("Sending ENCODER_VELOCITY: %#x %#x %#x %#x\n", data[0], data[1], data[2], data[3]);
      Wire.write(data, 4);
      break;
    }

    case REG_STARTFOC:
      if (FOC_started) {
        Wire.write(0x01);  // FOC started
      } else {
        Wire.write(0x00);  // Not started
      }
      break;
      
    default:
      Wire.write("???");
      break;
  }
  
  registerSet = false;  // Reset after read
}
