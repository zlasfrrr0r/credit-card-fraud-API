# rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# cache 
import json
import hashlib
import redis.asyncio as aioredis

# async tasks
from celery.result import AsyncResult
from .worker import predict_async_task
from fastapi import status

# API startup & model loading
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

# instantiate asyn redis connection pool
redis_client = aioredis.Redis.from_url(REDIS_URL, decode_responses=True)
CACHE_TTL_SECONDS = 3600 # 1 hour exp

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

# sync endpoint
@router.post("/predict")
@limiter.limit("7/minute")
async def predict(request: Request, input: Transaction):
    cache_key = gen_cache_key(input)

    try:
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            response_data = json.loads(cached_result)
            response_data["cached"] = True
            return response_data
    except Exception as e:
        print(f"redis cache get error: {e}")

    # cache miss
    TRANSACTION = input.model_dump()
    X_input = pd.DataFrame([TRANSACTION])
    pred = model.predict(X_input)
    proba = model.predict_proba(X_input)
    response_data = {
        "is_fraud": pred.item(),
        "fraud_proba": float(proba[0][1])
        }

    try:
        await redis_client.setex(
            name=cache_key,
            time=CACHE_TTL_SECONDS,
            value=json.dumps(response_data)
        )
    except Exception as e:
        print(f"Redis cache store error: {e}")

    response_data["cached"] = False
    return response_data

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
    task = predict_async_task.delay(input.model_dump())

    return {
        "task_id": task.id,
        "status": "PENDING",
        "poll_url": F"{API_PREFIX}/tasks/{task.id}"
    }

@router.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    task_result = AsyncResult(task_id)
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