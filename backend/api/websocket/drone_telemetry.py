import asyncio
import json
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.config import settings

router = APIRouter(prefix="/ws", tags=["WebSockets"])

@router.websocket("/drone-telemetry")
async def drone_telemetry_websocket(websocket: WebSocket):
    await websocket.accept()
    
    try:
        if settings.DEMO_MODE:
            # 5Hz updates
            frame_delay = 1.0 / 5.0
            demo_file = os.path.join(settings.DEMO_DATA_DIR, "drone_telemetry.jsonl")
            
            if os.path.exists(demo_file):
                with open(demo_file, "r") as f:
                    lines = f.readlines()
                    while True:
                        for line in lines:
                            await websocket.send_text(line.strip())
                            await asyncio.sleep(frame_delay)
            else:
                import time
                while True:
                    dummy_state = {
                        "latitude": 34.0522,
                        "longitude": -118.2437,
                        "altitude_m": 50.0,
                        "heading_deg": 90.0,
                        "speed_mps": 5.0,
                        "battery_percent": 85.0,
                        "gps_fix": True,
                        "gimbal_pitch_deg": -45.0,
                        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    }
                    await websocket.send_text(json.dumps(dummy_state))
                    await asyncio.sleep(frame_delay)
        else:
            while True:
                await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Telemetry client disconnected")
    except Exception as e:
        print(f"Telemetry error: {e}")
