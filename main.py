# main.py
# Sets up the the thread and process pools and starts the task loops.
import asyncio

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from hardware import imu_loop, gps_loop, left_driver_loop, right_driver_loop

thread_pool   = ThreadPoolExecutor(max_workers=4)   # I2C, serial
process_pool  = ProcessPoolExecutor(max_workers=3)  # 3 workers across cores 1-3

async def main():
    await asyncio.gather(
        # # Hardware - asyncio + thread pool for blocking I2C
        # imu.poll_loop(thread_pool),           # fast, ~100Hz
        # gps.poll_loop(thread_pool),
        # power.power_loop(thread_pool),
        # cameras.rgb.capture_loop(),           # feeds synchroniser
        # cameras.tof.capture_loop(),           # feeds synchroniser
        left_driver_loop(thread_pool),
        right_driver_loop(thread_pool),

        # # Processing - offloaded to process pool
        # processing.slam.pipeline.slam_loop(process_pool),    # Core 1
        # processing.vision.rgb_stream.encode_loop(process_pool),  # Core 2
        # processing.vision.depth_stream.encode_loop(process_pool), # Core 3

        # Web
        # web_server.serve(),
    )