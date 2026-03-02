
#to run, type "fastapi dev main.py" in console whilst in web folder

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import struct

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
async def serve_index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connected")
    try:
        while True:
            # Receive 8 bytes: two 32-bit signed integers (slider1, slider2), big-endian
            raw = await websocket.receive_bytes()
            if len(raw) != 8:
                print("Unexpected binary length:", len(raw))
                continue

            slider1, slider2 = struct.unpack("!ii", raw)
            print(f"Received from client: slider1={slider1}, slider2={slider2}")

            # Echo back the same two integers as binary
            reply = struct.pack("!ii", slider1, slider2)
            await websocket.send_bytes(reply)
            print("Sent to client (binary):", reply)
    except WebSocketDisconnect:
        print("WebSocket disconnected")