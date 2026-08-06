from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_rate_limit(client, sample_payload):

    # Rate Limited Endpoint
    endpoint = "api/v1/predict"
    limit = 7

    responses = []
    for _ in range(limit + 2):
        res = client.post(endpoint, json=sample_payload)
        responses.append(res.status_code)

    # First Request is OK
    assert responses[0] == 200

    # Request after limit should get 429
    assert 429 in responses