# config.py
# Define various constants and configuration parameters.

class Addresses:
    LEFT_DRIVER   = 0x20
    RIGHT_DRIVER  = 0x21

    BATTERY1      = 0x40
    BATTERY2      = 0x41
    MAIN_BUS      = 0x44

    EMC2101       = 0x4C

class STM32DriverRegs:
    MOTOR_CURRENT     = 0x01 # write - float 4 bytes MSB
    ENCODER_VELOCITY  = 0x02 # read  - float 4 bytes MSB
    STARTFOC          = 0x03 # read request - starts FOC, returns 0x00 if started successfully, 0x01 if already started
    STATUS            = 0x05 # read  - single byte
    CONN_WATCHDOG     = 0x22

class PollRates:
    IMU     = 100
    GPS     = 1
    BATTERY = 1
    FAN     = 1
    DRIVERS  = 10