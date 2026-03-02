#!/usr/bin/env python3
import smbus2
import time

import struct

I2C_ADDR = 0x21
I2C_BUS = 1

REG_MOTOR_CURRENT     = 0x01 # write - float 4 bytes MSB
REG_ENCODER_VELOCITY  = 0x02 # read  - float 4 bytes MSB
REG_STATUS            = 0x05 # read  - single byte

REG_LED = 0x03

bus = smbus2.SMBus(I2C_BUS)
x = 0

def float2bytesMSB(val: float) -> list:
    return list(struct.pack('>f', val))

def bytes2floatMSB(data: list) -> float:
    return struct.unpack('>f', bytes(data))[0]

def set_motor_current(current: float):
    """
    Set motor current as a float encoded to 4 bytes MSB.
    e.g. 1.5 -> bytes -> write to STM32DriverRegs.MOTOR_CURRENT
    """
    data = float2bytesMSB(current)
    # await bus.write_block(I2C_ADDR, STM32DriverRegs.MOTOR_CURRENT, data)
    bus.write_i2c_block_data(I2C_ADDR, REG_MOTOR_CURRENT, data)
    print(f"Sent motor current data: {[hex(i) for i in data]}")

def loop():
    global x
    
    try:
        # Read from REG_HELLO (returns "hello\n")
        data = bus.read_i2c_block_data(I2C_ADDR, REG_ENCODER_VELOCITY, 4)
        print(data)
        velocity = bytes2floatMSB(data)
        print(f"Encoder velocity: {velocity}")
        
        time.sleep(0.01)
        
        # # Read status byte from REG_STATUS
        # status = bus.read_byte_data(I2C_ADDR, REG_STATUS)
        # print(f"Status: 0x{status:02X}")
        
        # time.sleep(0.01)
        
        # # Write to REG_RECEIVE
        # message = "x is " + chr(x)
        # message_bytes = [ord(c) for c in message]
        # bus.write_i2c_block_data(I2C_ADDR, REG_RECEIVE, message_bytes)
        
        # x = (x + 1) % 256
        # time.sleep(0.5)

        # try:
        #     message_byte = int(input("LED State (0 or 1): "))
        #     if message_byte in [0, 1]:
        #         bus.write_byte_data(I2C_ADDR, REG_LED, message_byte)
        #         print(f"LED {'ON' if message_byte == 1 else 'OFF'} sent to {hex(I2C_ADDR)}")
        #     else:
        #         print("Error: Please enter only 0 or 1")
        # except ValueError:
        #     print("Error: Please enter a valid number")
    
    except Exception as e:
        print(f"I2C Error: {e}")
        time.sleep(0.5)

def main():
    print("I2C Master with register protocol")
    try:
        # while True:
        #     loop()
        set_motor_current(1.5)
        time.sleep(0.5)
        try:
            data = bus.read_i2c_block_data(I2C_ADDR, REG_ENCODER_VELOCITY, 4)
            print(data)
            velocity = bytes2floatMSB(data)
            print(f"Encoder velocity: {velocity}")
        except Exception as e:
            print(f"I2C Error: {e}")
            time.sleep(0.5)
        print("\nExiting...")
        bus.close()
    except KeyboardInterrupt:
        print("\nExiting...")
        bus.close()

if __name__ == "__main__":
    main()