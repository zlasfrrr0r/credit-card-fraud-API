import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
import pytest

"""
Load sample transaction from `fixtures/sample_transaction.json` and makes it available for all /tests
"""

@pytest.fixture(scope='session')
def client():
    with TestClient(app=app) as test_client:
        yield test_client

@pytest.fixture
def sample_payload():
    fixture_path = Path(__file__).parent / "fixtures" / "sample_transaction.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)