// firmware/stm32_motor_drivers/include/i2c_register_map.h
#define REG_MOTOR_CURRENT     0x01  // write - float 4 bytes MSB
#define REG_ENCODER_VELOCITY  0x02  // read  - float 4 bytes MSB
#define REG_STATUS            0x05  // read  - single byte