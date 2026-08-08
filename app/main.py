# rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_ipaddr
from slowapi.errors import RateLimitExceeded

# cache 
import json
import hashlib
import redis.asyncio as aioredis

# async tasks
from .worker import predict_async_task, celery_app, predict_batch_async_task
from fastapi import status

# API startup & model loading
from fastapi import FastAPI, APIRouter, Request
from .config import API_PREFIX, REDIS_URL, CACHE_TTL_SECONDS
from contextlib import asynccontextmanager
from pathlib import Path
import joblib
import pandas as pd

# model prediction
from .pipeline import (
    preprocess_single,
    preprocess_batch_vectorized,
    run_vectorized_inference
)
from .schemas import Transaction, TransactionBatch, Prediction, BatchPrediction

from prometheus_fastapi_instrumentator import Instrumentator

def gen_cache_key(payload: Transaction):
    payload_json = json.dumps(payload.model_dump(), sort_keys=True)
    hash_digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    return f"cache:prediction:{hash_digest}"

# instantiate asyn redis connection pool
redis_client = aioredis.Redis.from_url(REDIS_URL, decode_responses=True)

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "fraud-detection.joblib"

limiter = Limiter(
    key_func=get_ipaddr,
    storage_uri=REDIS_URL
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    # Load and warmp up model on startup
    model = joblib.load(MODEL_PATH)
    dummy_transaction = Transaction(
        Time=0.0, V1=0.0, V2=0.0, V3=0.0, V4=0.0, V5=0.0, V6=0.0, V7=0.0, V8=0.0, V9=0.0,
        V10=0.0, V11=0.0, V12=0.0, V13=0.0, V14=0.0, V15=0.0, V16=0.0, V17=0.0, V18=0.0, V19=0.0,
        V20=0.0, V21=0.0, V22=0.0, V23=0.0, V24=0.0, V25=0.0, V26=0.0, V27=0.0, V28=0.0, Amount=0.0
    )
    df_dummy = preprocess_single(dummy_transaction)
    _ = run_vectorized_inference(model, df_dummy)
    print("Model loaded and warmed up. Ready for inference!")
    yield
    del model   # delete model in shutdown
    print("Shutting down...")

app = FastAPI(lifespan=lifespan,
              docs_url=f"{API_PREFIX}/docs",
              redoc_url=f"{API_PREFIX}/redoc",
              openapi_url=f"{API_PREFIX}/openapi.json")

Instrumentator().instrument(app=app).expose(app=app, endpoint="/metrics")

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

# sync endpoint
@router.post("/predict", response_model=Prediction)
@limiter.limit("7/minute")
async def predict(request: Request, input: Transaction):
    cache_key = gen_cache_key(input)

    try:
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            response = json.loads(cached_result)
            response["cached"] = True
            return response
    except Exception as e:
        print(f"redis cache get error: {e}")

    # cache miss
    df_input = preprocess_single(input)
    results = run_vectorized_inference(model, df_input)
    response = results[0]

    try:
        await redis_client.setex(
            name=cache_key,
            time=CACHE_TTL_SECONDS,
            value=json.dumps(response)
        )
    except Exception as e:
        print(f"Redis cache store error: {e}")

    response["cached"] = False
    return response

# async endpoint (task queueing)
@router.post("/predict/async", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/minute")
async def predict_async(request: Request, input: Transaction):

    cache_key = gen_cache_key(input)

    try:
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            response_data = json.loads(cached_result)
            response_data["cached"] = True
            return {
                "status": "COMPLETED_VIA_CACHE",
                "result": response_data
            }
    except Exception as e:
        print(f"redis cache get error: {e}")

    # cache miss -> enqueue to celery workers
    task = predict_async_task.delay(input.model_dump(), cache_key)

    return {
        "task_id": task.id,
        "status": "PENDING",
        "poll_url": f"{API_PREFIX}/tasks/{task.id}"
    }

@router.post("/predict/batch", response_model=BatchPrediction)
@limiter.limit("7/minute")
async def predict_batch(request: Request, batch: TransactionBatch):
    """
    Processes up to 1,000 transactions executing vectorised 
    operations on a single pass
    """
    df_input, _ = preprocess_batch_vectorized(batch.transactions)
    results = run_vectorized_inference(model, df_input)

    return {
        "predictions": results,
        "total_predicted": len(results)
    }

@router.post("/predict/batch/async", status_code=202)
@limiter.limit("5/minute")
async def predict_batch_async(request: Request, batch: TransactionBatch):
    """
    Accepts up to 1,000 transactions, returns instant results for cache hits, 
    and offloads cache misses to a single optimized vectorized worker task.
    """
    batch_data = [tx.model_dump() for tx in batch.transactions]

    task = predict_batch_async_task.delay(batch_data)

    return {
        "task_id": task.id,
        "status": "PENDING",
        "poll_url": f"{API_PREFIX}/tasks/{task.id}"
    }

@router.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    task_result = celery_app.AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "status": task_result.status
    }
    if task_result.status == "SUCCESS":
        response["result"] = task_result.result
    if task_result.status == "FAILURE":
        response["error"] = str(task_result.result)

    return response

app.include_router(router=router)