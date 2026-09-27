import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.asyncio
async def test_missions_crud():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create
        response = await ac.post("/api/missions", json={
            "name": "Test Mission",
            "description": "Test Desc",
            "waypoints": [
                {"sequence_order": 1, "latitude": 10.0, "longitude": 20.0, "altitude": 50.0}
            ]
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Mission"
        assert len(data["waypoints"]) == 1
        mission_id = data["id"]
        
        # List
        response = await ac.get("/api/missions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Get
        response = await ac.get(f"/api/missions/{mission_id}")
        assert response.status_code == 200
        assert response.json()["id"] == mission_id
        
        # Update
        response = await ac.put(f"/api/missions/{mission_id}", json={
            "name": "Updated Mission",
            "description": "Updated Desc",
            "waypoints": []
        })
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Mission"
        
        # Start
        response = await ac.post(f"/api/missions/{mission_id}/start")
        assert response.status_code == 200
        assert response.json()["status"] == "active"
        
        # Pause
        response = await ac.post(f"/api/missions/{mission_id}/pause")
        assert response.status_code == 200
        assert response.json()["status"] == "paused"
        
        # Abort
        response = await ac.post(f"/api/missions/{mission_id}/abort")
        assert response.status_code == 200
        assert response.json()["status"] == "aborted"
        
        # Delete
        response = await ac.delete(f"/api/missions/{mission_id}")
        assert response.status_code == 204
