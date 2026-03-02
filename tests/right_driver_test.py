# tests/left_driver_test.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from hardware.motor_driver_right import poll_loop, set_motor_current, read_velocity, read_status, right_driver_data, read_motor_current

async def main():
    # Start poll loop as a background task
    poll_task = asyncio.create_task(poll_loop())

    # Give it a moment to populate data before reading
    await asyncio.sleep(0.5)
    
    # Test status read first - good connection check
    status = right_driver_data["status"]
    print(f"Status: 0x{status:02X}")

    # Test setting motor current
    for current in [0.0, 0.5, 1.0, 1.5, 2.0]:
        await set_motor_current(current)
        await asyncio.sleep(0.5)
        velocity = right_driver_data["velocity"]
        new_current = right_driver_data["motor_current"]
        print(f"Current: {current}A | Velocity: {velocity:.3f} m/s | Read back: {new_current:.3f}A")

    poll_task.cancel()
    
asyncio.run(main())