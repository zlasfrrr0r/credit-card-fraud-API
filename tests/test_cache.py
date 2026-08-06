from fastapi.testclient import TestClient
from app.config import API_PREFIX
from app.main import app
import time

client = TestClient(app=app)

def test_caching_behavior(client, sample_payload):

    # 1. First Request - Cache Miss
    start_time = time.time()
    res_1 = client.post(f"{API_PREFIX}/predict", json=sample_payload)
    dur_1 = (time.time() - start_time) * 1000  # ms

    assert res_1.status_code == 200
    data_1 = res_1.json()
    assert "is_fraud" in data_1
    assert "fraud_proba" in data_1

    # 2. Second Request - Cache Hit
    start_time = time.time()
    res_2 = client.post(f"{API_PREFIX}/predict", json=sample_payload)
    dur_2 = (time.time() - start_time) * 1000  # ms

    assert res_2.status_code == 200
    data_2 = res_2.json()

    # Predictions must match
    assert data_1["is_fraud"] == data_2["is_fraud"]
    assert data_1["fraud_proba"] == data_2["fraud_proba"]

    # Cache hit must be faster
    assert dur_2 < dur_1