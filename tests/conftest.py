import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
import pytest

"""
Load sample transaction from `fixtures/sample_transaction.json` and makes it available for all /tests
"""

FIXTURE_PATH = Path(__file__).parent / "fixtures"

@pytest.fixture(scope='session')
def client():
    with TestClient(app=app) as test_client:
        yield test_client

@pytest.fixture
def sample_payload():
    with open(FIXTURE_PATH / "sample_transaction.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def sample_batch_payload():
    with open(FIXTURE_PATH / "sample_batch_transactions.json", "r", encoding="utf-8") as f:
        return json.load(f)