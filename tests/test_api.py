from app.main import app
from app.config import API_PREFIX
from fastapi.testclient import TestClient

client = TestClient(app=app)

def test_health():
    response = client.get(f"{API_PREFIX}/health")
    assert response.status_code == 200
    assert response.json() == { "Health": "OK" }