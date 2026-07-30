import joblib
import pandas as pd
from celery import Celery
from pathlib import Path
from .config import CELERY_BROKER_URL, CELERY_RESULT_URL, REDIS_URL, CACHE_TTL_SECONDS
import redis
import json

celery_app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_URL
)

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "fraud-detection.joblib"

_model = None

def get_model():
    # keep model alive inside worker process' memory
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model

@celery_app.task(name="predict_async_task")
def predict_async_task(transaction_data: dict, cache_key: str) -> dict:
    model = get_model()
    X_input = pd.DataFrame([transaction_data])

    pred = model.predict(X_input)
    proba = model.predict_proba(X_input)

    result = {
        "is_fraud": pred.item(),
        "fraud_proba": float(proba[0][1])
    }

    # store in cache if key provided
    if cache_key:
        r = redis.Redis.from_url(REDIS_URL)
        r.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(result))

    return result