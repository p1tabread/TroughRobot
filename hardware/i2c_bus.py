# hardware/i2c_bus.py
#
# Provides an asynchronous wrapper around smbus2  for I2C comms.

import asyncio
from smbus2 import SMBus
import struct

def float2bytesMSB(val: float) -> list:
    return list(struct.pack('>f', val))

def bytes2floatMSB(data: list) -> float:
    return struct.unpack('>f', bytes(data))[0]

class I2CBus:
    def __init__(self, bus_number: int = 1):
        self._smbus = SMBus(bus_number)
        self._lock = asyncio.Lock()

    async def read_byte(self, address: int, register: int) -> int:
        async with self._lock:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self._smbus.read_byte_data, address, register
            )

    async def read_block(self, address: int, register: int, length: int) -> list[int]:
        async with self._lock:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self._smbus.read_i2c_block_data, address, register, length
            )

    async def write_byte(self, address: int, register: int, value: int):
        async with self._lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self._smbus.write_byte_data, address, register, value
            )

    async def write_block(self, address: int, register: int, data: list[int]):
        async with self._lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self._smbus.write_i2c_block_data, address, register, data
            )

    def close(self):
        self._smbus.close()

bus = I2CBus(bus_number=1)