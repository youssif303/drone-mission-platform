import asyncio
import json
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws", tags=["WebSockets"])

SAMPLE_ALERTS = [
    {"type": "detection", "severity": "info", "message": "Autonomous patrol pattern initiated. 4 waypoints queued."},
    {"type": "detection", "severity": "info", "message": "Target #1 (CAR) detected in sector ALPHA. Speed: 35 km/h."},
    {"type": "geofence", "severity": "warning", "message": "Target #1 (CAR) approaching perimeter boundary."},
    {"type": "detection", "severity": "info", "message": "Target #2 (PERSON) visual tracking confirmed in zone BRAVO."},
    {"type": "detection", "severity": "info", "message": "Target #3 (TRUCK) tracked on secondary route."},
    {"type": "system", "severity": "info", "message": "EO/IR Gimbal telemetry nominal. Signal link: 98%."}
]

@router.websocket("/alerts")
async def alerts_websocket(websocket: WebSocket):
    await websocket.accept()
    alert_idx = 0
    try:
        while True:
            alert = SAMPLE_ALERTS[alert_idx % len(SAMPLE_ALERTS)]
            payload = {
                "id": alert_idx + 1,
                "type": alert["type"],
                "severity": alert["severity"],
                "message": alert["message"],
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            await websocket.send_text(json.dumps(payload))
            alert_idx += 1
            await asyncio.sleep(6.0)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Alerts WS exception: {e}")
