from fastapi import FastAPI
from .schemas import Transaction, Prediction
from contextlib import asynccontextmanager
from pathlib import Path
import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "fraud-detection.joblib"

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    # model = load(MODEL_PATH) # load model on startup to avoid loading on every request
    model = joblib.load(MODEL_PATH)
    print("Model loaded. Ready for inference!")
    yield
    del model   # delete model in shutdown
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {
        "Message": "Root"
    }

@app.get("/health")
def health():
    return {
        "Health": "OK"
    }

@app.post("/predict")
def predict(input: Transaction):
    TRANSACTION = input.model_dump()
    X_input = pd.DataFrame([TRANSACTION])
    pred = model.predict(X_input)
    proba = model.predict_proba(X_input)
    return {
        "is_fraud": pred.item(),
        "fraud_proba": float(proba[0][1])
    }