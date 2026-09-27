import asyncio
import json
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.config import settings

router = APIRouter(prefix="/ws", tags=["WebSockets"])

@router.websocket("/detections")
async def detections_websocket(websocket: WebSocket):
    await websocket.accept()
    
    try:
        if settings.DEMO_MODE:
            frame_delay = 1.0 / settings.WS_FRAME_RATE
            demo_file = os.path.join(settings.DEMO_DATA_DIR, "detections.jsonl")
            
            if os.path.exists(demo_file):
                with open(demo_file, "r") as f:
                    lines = f.readlines()
                    while True:
                        for line in lines:
                            await websocket.send_text(line.strip())
                            await asyncio.sleep(frame_delay)
            else:
                # Fallback to sending dummy data
                import time
                while True:
                    dummy_detection = [{
                        "track_id": 1,
                        "class_name": "person",
                        "latitude": 34.0522,
                        "longitude": -118.2437,
                        "speed_mps": 1.5,
                        "heading_deg": 45.0,
                        "confidence": 0.95,
                        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    }]
                    await websocket.send_text(json.dumps(dummy_detection))
                    await asyncio.sleep(frame_delay)
        else:
            while True:
                await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Detections client disconnected")
    except Exception as e:
        print(f"Detections error: {e}")
