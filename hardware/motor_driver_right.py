# hardware/motor_driver_left.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from hardware.i2c_bus import bus, float2bytesMSB, bytes2floatMSB

from config import Addresses, PollRates, STM32DriverRegs
I2C_ADDR  = Addresses.RIGHT_DRIVER
POLL_RATE = PollRates.DRIVERS

right_driver_data = {
    "motor_current": 0.0,
    "velocity": 0.0,
    "status": 0,
}

async def set_motor_current(current: float):
    """
    Set motor current as a float encoded to 4 bytes MSB.
    e.g. 1.5 -> bytes -> write to STM32DriverRegs.MOTOR_CURRENT
    """
    data = float2bytesMSB(current)
    await bus.write_block(I2C_ADDR, STM32DriverRegs.MOTOR_CURRENT, data)
    print(f"Sent motor current data: {[hex(i) for i in data]}")

async def read_motor_current() -> float:
    """Read motor current setpoint as a float encoded as 4 bytes MSB"""
    raw = await bus.read_block(I2C_ADDR, STM32DriverRegs.MOTOR_CURRENT, 4)
    #print(f"Raw motor current data: {[hex(i) for i in raw]}")
    current = bytes2floatMSB(raw)
    #print(f"Motor current setpoint: {current}")
    return current

async def read_velocity() -> float:
    """Read encoder velocity as a float encoded as 4 bytes MSB"""
    raw = await bus.read_block(I2C_ADDR, STM32DriverRegs.ENCODER_VELOCITY, 4)
    #print(f"Raw velocity data: {[hex(i) for i in raw]}")
    velocity = bytes2floatMSB(raw)
    #print(f"Encoder velocity: {velocity}")
    return velocity

async def read_status() -> int:
    return await bus.read_byte(I2C_ADDR, STM32DriverRegs.STATUS)

async def poll_loop():
    interval = 1.0 / POLL_RATE
    while True:
        try:
            #print(await read_velocity())
            right_driver_data["motor_current"] = await read_motor_current()
            right_driver_data["velocity"] = await read_velocity()
            right_driver_data["status"]   = await read_status()
        except Exception as e:
            print(f"Right driver error: {e}")
        await asyncio.sleep(interval)