import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from hardware.i2c_bus import bytes2floatMSB

from hardware.motor_driver_left import set_motor_current as set_motor_current_left
from hardware.motor_driver_right import set_motor_current as set_motor_current_right

motor_currents = {
    "left": 0.0,
    "right": 0.0,
}

async def update_motor_currents(current_left: list[int], current_right: list[int]):
    motor_currents["left"] = bytes2floatMSB(current_left)
    motor_currents["right"] = bytes2floatMSB(current_right)

    print(f"Updated motor currents: {motor_currents}")

    await set_motor_current_left(motor_currents["left"])
    await set_motor_current_right(motor_currents["right"])

    



