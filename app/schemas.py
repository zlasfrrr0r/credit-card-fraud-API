from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Any
import math

class Transaction(BaseModel):
    Time: float = Field(..., ge=0.0, description="seconds elapsed since first transaction") # Time >= 0.0s...
    V1: float
    V2: float
    V3: float
    V4: float
    V5: float
    V6: float
    V7: float
    V8: float
    V9: float
    V10: float
    V11: float
    V12: float
    V13: float
    V14: float
    V15: float
    V16: float
    V17: float
    V18: float
    V19: float
    V20: float
    V21: float
    V22: float
    V23: float
    V24: float
    V25: float
    V26: float
    V27: float
    V28: float
    Amount: float = Field(..., ge=0.0, description="transaction amount in currency units")

    # reject all NaN, Inf, etc
    @field_validator("*", mode="after")
    @classmethod
    def check_nan_inf(cls, value: Any) -> Any:
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                raise ValueError("Input contains invalid float (NaN or Infinity)")
        return value

class Prediction(BaseModel):
    is_fraud: bool
    fraud_proba: float
    cached: bool = False

class TransactionBatch(BaseModel):
    transactions: List[Transaction] = Field(..., min_length=1, max_length=1000)

class BatchPrediction(BaseModel):
    predictions: List[Prediction]
    total_predicted: int
    cached: bool = False