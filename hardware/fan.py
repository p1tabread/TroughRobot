# hardware/fan.py 
# 
# EMC2101 PWM Fan Controller, uses Adafruit CircuitPython library with it's own I2C bus instance.

import asyncio
import board
import busio
from adafruit_emc2101 import EMC2101

from config import PollRates
POLL_RATE = PollRates.FAN

# Create I2C instance and EMC2101 object
_i2c = busio.I2C(board.SCL, board.SDA)
_emc = EMC2101(_i2c)

# Dict to hold latest fan data
fan_data = {"rpm": 0, "duty": 0, "temp_internal": 0.0}

# Returrn the fan data
def _read_blocking():
    return {
        "rpm":           _emc.fan_speed,
        "duty":          _emc.manual_fan_speed,
        "temp_internal": _emc.internal_temperature,
        #"temp_external": _emc.external_temperature,
    }

# Set the fan speed
async def set_speed(percent: int):
    percent = max(0, min(100, percent))
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, setattr, _emc, "manual_fan_speed", percent)

# Update fan data at POLL_RATE
async def poll_loop():
    while True:
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, _read_blocking)
            fan_data.update(data)
            # await _auto_thermal() // Uncomment for automatic fan curve
        except Exception as e:
            print(f"Fan error: {e}")
        await asyncio.sleep(1.0 / POLL_RATE)

# Automatic fan curve
# async def _auto_thermal():
#     temp = fan_data["temp_internal"]
#     if   temp < 40: await set_speed(20)
#     elif temp < 55: await set_speed(50)
#     elif temp < 70: await set_speed(80)
#     else:           await set_speed(100)