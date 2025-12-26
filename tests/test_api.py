from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app=app)

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == { "Health": "OK" }