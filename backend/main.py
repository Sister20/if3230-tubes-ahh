from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def get():
    return {"message": "WebSocket endpoint available at /log"}

@app.websocket("/log/{port}")
async def websocket_endpoint(websocket: WebSocket, port: int):
    await websocket.accept()
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(f"http://localhost:{port}")
                await websocket.send_json({"log": response.text})
            except httpx.RequestError as e:
                await websocket.send_json({"error": str(e)})
            await asyncio.sleep(1)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)