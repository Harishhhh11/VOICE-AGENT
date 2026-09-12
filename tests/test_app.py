from fastapi.testclient import TestClient

from app.main import app


def test_root():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_lead_endpoint():
    with TestClient(app) as client:
        response = client.post(
            "/api/leads",
            json={
                "session_id": "test-session",
                "name": "Test User",
                "phone": "9999999999",
                "course_interest": "AI",
            },
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
