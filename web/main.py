
# to run in dev mode, type "fastapi dev main.py" in console whilst in web folder
# to run in normal mode, uvicorn main:app --host 0.0.0.0 --port 8000 --reload

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from control.drive import update_motor_currents, send_watchdogs_checks
import struct # for binary packing/unpacking

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(BASE_DIR / "static" / "index.html")

# Controlling user slot - others are observers
active_controller: WebSocket | None = None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global active_controller
    await websocket.accept()
    is_controller = active_controller is None
    if is_controller:
        active_controller = websocket
    await websocket.send_text("control" if is_controller else "observe")
    print("WebSocket connected")

    try:
        while True:
            msg = await websocket.receive()

            if msg.get("type") == "websocket.disconnect":
                break  # clean exit, falls into finally

            if "text" in msg:
                if msg["text"] == "wd" and is_controller:
                    await send_watchdogs_checks()
                    # print("en")
                continue

            raw = msg.get("bytes", b"")
            if len(raw) != 8:
                print("Unexpected binary length:", len(raw))
                continue

            if is_controller:
                await update_motor_currents(raw[0:4], raw[4:8])
                # print("senddata")

    except WebSocketDisconnect:
        zero = struct.pack("!f", 0.0)
        print("WebSocket disconnected")
        await update_motor_currents(list(zero), list(zero))

    finally:
        zero = struct.pack("!f", 0.0)
        await update_motor_currents(list(zero), list(zero))
        print("Motors zeroed on Disconnect")
        if is_controller and active_controller is websocket:  # ← only release if still ours
            active_controller = None

