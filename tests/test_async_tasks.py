from fastapi.testclient import TestClient
from app.main import app
from app.config import API_PREFIX
import time

client = TestClient(app=app)

def test_async_tasks(client, sample_payload):
    """
    Workflow:
    1. Enqueue Task -> 202 Accepted
    2. Poll Task -> status goes from PENDING to SUCCESS
    """

    # Task Enqueued
    response = client.post(f"{API_PREFIX}/predict/async", json=sample_payload)
    assert response.status_code == 202

    body = response.json()
    assert "task_id" in body
    assert body["status"] == "PENDING"

    task_id = body["task_id"]

    # Polling to Complete Task
    max_retries = 10
    task_completed = False

    for _ in range(max_retries):
        poll_response = client.get(f"{API_PREFIX}/tasks/{task_id}")
        assert poll_response.status_code == 200

        poll_body = poll_response.json()
        if poll_body["status"] == "SUCCESS":
            task_completed = True
            assert "result" in poll_body
            assert "is_fraud" in poll_body["result"]
            assert "fraud_proba" in poll_body["result"]
            break

        time.sleep(0.5)

    assert task_completed, f"Task ID: {task_id} not 'SUCCESS' within timeout"