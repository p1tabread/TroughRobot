# tests/test_fan.py

import sys
import os

# Go up one level from tests/ to TroughRobot/ so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from hardware.fan import set_speed, fan_data, _read_blocking

async def main():
    # for speed in [0, 25, 50, 75, 100]:
    #     await set_speed(speed)
    #     await asyncio.sleep(5) 

    #     loop = asyncio.get_event_loop()
    #     data = await loop.run_in_executor(None, _read_blocking)
    #     fan_data.update(data)

    #     print(f"Set: {speed}% | RPM: {fan_data['rpm']} | Temp: {fan_data['temp_internal']}°C")

    await set_speed(100)

asyncio.run(main())