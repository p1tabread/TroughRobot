# tests/left_driver_test.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from hardware.motor_driver_left import start_foc

async def main():

    response = await start_foc()
     # Give it a moment to populate data before reading
    await asyncio.sleep(0.5)
    print(f"Start FOC response: 0x{response:02X}")
    
asyncio.run(main())