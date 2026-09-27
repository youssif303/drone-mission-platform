import asyncio
import base64
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import aiofiles
from backend.config import settings

router = APIRouter(prefix="/ws", tags=["WebSockets"])

@router.websocket("/video-feed")
async def video_feed_websocket(websocket: WebSocket):
    await websocket.accept()
    
    # Simple simulated video feed if demo mode
    try:
        if settings.DEMO_MODE:
            # We will just generate a dummy image or send a pre-existing one
            # For simplicity, sending a blank/dummy base64 frame if dir doesn't exist
            # Real implementation reads from settings.DEMO_DATA_DIR
            frame_delay = 1.0 / settings.WS_FRAME_RATE
            while True:
                # In a real demo, this reads images sequentially from DEMO_DATA_DIR
                # Since we don't have images here, we'll send a 1x1 pixel base64 jpeg
                dummy_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" 
                await websocket.send_text(f"data:image/jpeg;base64,{dummy_b64}")
                await asyncio.sleep(frame_delay)
        else:
            # Live camera feed logic
            while True:
                await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Video feed client disconnected")
    except Exception as e:
        print(f"Video feed error: {e}")
