# to attach slowapi properly
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import json
import hashlib

from fastapi import FastAPI, APIRouter, Request
from .schemas import Transaction
from .config import API_PREFIX, REDIS_URL
from contextlib import asynccontextmanager
from pathlib import Path
import joblib
import pandas as pd

def gen_cache_key(payload: Transaction):
    payload_json = json.dumps(payload.model_dump(), sort_keys=True)
    hash_digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    return f"cache:prediction:{hash_digest}"

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "fraud-detection.joblib"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=REDIS_URL
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    model = joblib.load(MODEL_PATH) # load model on startup to avoid loading on every request
    print("Model loaded. Ready for inference!")
    yield
    del model   # delete model in shutdown
    print("Shutting down...")

app = FastAPI(lifespan=lifespan,
              docs_url=f"{API_PREFIX}/docs",
              redoc_url=f"{API_PREFIX}/redoc",
              openapi_url=f"{API_PREFIX}/openapi.json")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

router = APIRouter(prefix=API_PREFIX)

@router.get("/")
@limiter.limit("30/minute")
def root(request: Request):
    return {
        "Message": "Root"
    }

# unlimited for docker/LB ping
@router.get("/health")
def health():
    return {
        "Health": "OK"
    }

@router.post("/predict")
@limiter.limit("7/minute")
def predict(request: Request, input: Transaction):
    TRANSACTION = input.model_dump()
    X_input = pd.DataFrame([TRANSACTION])
    pred = model.predict(X_input)
    proba = model.predict_proba(X_input)
    return {
        "is_fraud": pred.item(),
        "fraud_proba": float(proba[0][1])
    }

app.include_router(router=router)