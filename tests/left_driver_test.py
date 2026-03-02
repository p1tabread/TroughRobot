# tests/left_driver_test.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from hardware.motor_driver_left import poll_loop, set_motor_current, read_velocity, read_status, left_driver_data, read_motor_current

async def main():
    # Start poll loop as a background task
    poll_task = asyncio.create_task(poll_loop())

    # Give it a moment to populate data before reading
    await asyncio.sleep(0.5)
    
    # Test status read first - good connection check
    status = left_driver_data["status"]
    print(f"Status: 0x{status:02X}")

    # # Test setting motor current
    # for current in [0.0, 0.5, 1.0, 1.5, 2.0]:
    #     await set_motor_current(current)
    #     await asyncio.sleep(0.5)
    #     velocity = left_driver_data["velocity"]
    #     new_current = left_driver_data["motor_current"]
    #     print(f"Current: {current}A | Velocity: {velocity:.3f} rad/s | Read back: {new_current:.3f}A")

    await set_motor_current(-1.0)
    await asyncio.sleep(0.5)

    velocity = left_driver_data["velocity"]
    new_current = left_driver_data["motor_current"]
    print(f"Current: -0.5A | Velocity: {velocity:.3f} rad/s | Read back: {new_current:.3f}A")

    # Print velocity continuously for 5 seconds
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < 3:
        velocity = left_driver_data["velocity"]
        print(f"Velocity: {velocity:.3f} rad/s")
        await asyncio.sleep(0.1)  # adjust print rate here

    await set_motor_current(0)
    await asyncio.sleep(0.5)

    velocity = left_driver_data["velocity"]
    new_current = left_driver_data["motor_current"]
    print(f"Current: 0.0A | Velocity: {velocity:.3f} rad/s | Read back: {new_current:.3f}A")


    poll_task.cancel()
    
asyncio.run(main())