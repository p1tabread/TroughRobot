
# to run in dev mode, type "fastapi dev main.py" in console whilst in web folder
# to run in normal mode, uvicorn main:app --host 0.0.0.0 --port 8000 --reload

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from control.drive import update_motor_currents
import struct # for binary packing/unpacking

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
async def serve_index():
    return FileResponse(BASE_DIR / "static" / "index.html")

SCALE = 10  # Ensure this is updated in JS as well

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connected")
    try:
        while True:
            raw = await websocket.receive_bytes()

            if len(raw) != 8:
                print("Unexpected binary length:", len(raw))
                continue

            # # '!ff' = network (big-endian), two 32-bit floats [web:58]
            # v1, v2 = struct.unpack("!ff", raw)

            # v1 and v2 are Python floats in the original range, with float32 precision
            # print(f"Received floats: slider1={v1}, slider2={v2}")

            await update_motor_currents(raw[0:4],raw[4:8])
            # print(f"Received floats: slider1={list(raw[0:4])}, slider2={list(raw[4:8])}")
        
            # Echo back the same two float32 values
            # reply = struct.pack("!ff", v1, v2)
            # await websocket.send_bytes(reply)
    except WebSocketDisconnect:
        print("WebSocket disconnected")