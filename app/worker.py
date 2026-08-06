import joblib
import pandas as pd
from celery import Celery
from pathlib import Path
from .config import CELERY_BROKER_URL, CELERY_RESULT_URL, REDIS_URL, CACHE_TTL_SECONDS
import redis
import json
from .pipeline import preprocess_single, run_vectorized_inference

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

@celery_app.task(name="predict_batch_async_task")
def predict_batch_async_task(transactions_list: list) -> list:
    if not transactions_list:
        return {"predictions": [], "total_predicted": 0}

    model = get_model()

    df_input = pd.DataFrame(transactions_list)

    preds = model.predict(df_input)
    probas = model.predict_proba(df_input)[:, 1]

    return [
        {"is_fraud": int(is_fraud), "fraud_proba": float(proba)}
        for is_fraud, proba in zip(preds, probas)
    ]