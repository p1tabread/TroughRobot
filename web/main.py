from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

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
            data = await websocket.receive_json()
            print("Received from client:", data)
            reply = {
                "message": "Sliders updated",
                "slider1": data.get("slider1"),
                "slider2": data.get("slider2"),
            }
            await websocket.send_json(reply)
            print("Sent to client:", reply)
    except WebSocketDisconnect:
        print("WebSocket disconnected")