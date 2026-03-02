#include <Wire.h>
#include "stm32g4xx_hal.h"

#include "i2c_register_map.h"


#define REG_LED      0x03  // Set LED state

volatile uint8_t currentRegister = 0;
volatile bool registerSet = false;

float target_current = 0.0;

void receiveEvent(int howMany);
void requestEvent();

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

void setup() {
    Serial.begin(115200);

    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);


    Wire.begin(I2C_ADDR);
    Wire.setClock(400000);
    Wire.onRequest(requestEvent);
    Wire.onReceive(receiveEvent);

  
}

void loop() {
  // --- SERIAL trigger ---
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();

        if (cmd == "dfu") {
            Serial.println("Entering DFU mode...");
            delay(10);        // let USB send the message
            rebootToDFU();
        }
    }
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
      case REG_LED:
          digitalWrite(LED_BUILTIN, buffer[0]);

          Serial.printf("LED %s\n", buffer[0] ? "ON" : "OFF");
          break;
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
      float velocity = 3.14;  // Example velocity
      uint8_t data[4];
      float2bytesMSB(velocity, data);
      Serial.printf("Sending ENCODER_VELOCITY: %#x %#x %#x %#x\n", data[0], data[1], data[2], data[3]);
      Wire.write(data, 4);
      break;
    }
      
    default:
      Wire.write("???");
      break;
  }
  
  registerSet = false;  // Reset after read
}