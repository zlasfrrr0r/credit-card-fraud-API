from fastapi.testclient import TestClient
from app.config import API_PREFIX
from app.main import app

client = TestClient(app)

def test_rate_limit(client, sample_payload):

    # Rate Limited Endpoint
    endpoint = f"{API_PREFIX}/predict"
    limit = 7

    responses = []
    for _ in range(limit + 2):
        res = client.post(endpoint, json=sample_payload)
        responses.append(res.status_code)

    # First Request is OK
    assert responses[0] == 200

    # Request after limit should get 429
    assert 429 in responses