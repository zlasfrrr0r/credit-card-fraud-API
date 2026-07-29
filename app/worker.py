import joblib
import pandas as pd
from celery import Celery
from pathlib import Path
from .config import CELERY_BROKER_URL, CELERY_RESULT_URL

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

@celery_app.task(name="predict_task_async")
def predict_task_async(transaction_data: dict) -> dict:
    model = get_model()
    X_input = pd.DataFrame([transaction_data])

    pred = model.predict(X_input)
    proba = model.predict_proba(X_input)

    return {
        "is_fraud": pred.item(),
        "fraud_proba": float(proba[0][1])
    }