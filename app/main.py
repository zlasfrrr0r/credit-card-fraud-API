from fastapi import FastAPI, APIRouter
from .schemas import Transaction
from .config import API_PREFIX
from contextlib import asynccontextmanager
from pathlib import Path
import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "fraud-detection.joblib"

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

router = APIRouter(prefix=API_PREFIX)

@router.get("/")
def root():
    return {
        "Message": "Root"
    }

@router.get("/health")
def health():
    return {
        "Health": "OK"
    }

@router.post("/predict")
def predict(input: Transaction):
    TRANSACTION = input.model_dump()
    X_input = pd.DataFrame([TRANSACTION])
    pred = model.predict(X_input)
    proba = model.predict_proba(X_input)
    return {
        "is_fraud": pred.item(),
        "fraud_proba": float(proba[0][1])
    }

app.include_router(router=router)