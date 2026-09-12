from fastapi.testclient import TestClient

from app.main import app


def test_root():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_health_contract():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "llm_available" in body
        assert "knowledge_documents" in body


def test_voice_capabilities_contract():
    with TestClient(app) as client:
        response = client.get("/api/voice-capabilities")
        assert response.status_code == 200
        body = response.json()
        assert body["stt"]["provider"] == "faster-whisper"
        assert body["languages"] == ["en", "te", "hi", "auto"]
        assert body["audio_upload"] is True


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


def test_audio_type_rejected():
    with TestClient(app) as client:
        response = client.post(
            "/api/voice/transcribe",
            files={"file": ("payload.exe", b"not-audio", "application/octet-stream")},
        )
        assert response.status_code == 415
