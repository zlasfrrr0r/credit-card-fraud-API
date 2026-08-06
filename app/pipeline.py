import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from .schemas import Transaction

FEATURE_ORDER = [
    "Time", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10",
    "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19", "V20",
    "V21", "V22", "V23", "V24", "V25", "V26", "V27", "V28", "Amount"
]

def preprocess_single(transaction: Transaction) -> pd.DataFrame:
    # Convert single Transaction object to 1 row DF
    data = transaction.model_dump()
    return pd.DataFrame([data], columns=FEATURE_ORDER)

def proprocess_batch_vectorized(transactions: List[Transaction]) -> Tuple[pd.DataFrame, np.ndarray]:
    # Extract feature values into single contiguous 2D NumPY float matrix to eliminate row-by-row iteration (O(N))
    matrix = np.array(
        [[getattr(t, feature) for feature in FEATURE_ORDER] for t in transactions],
        dtype=np.float64
    )
    df = pd.DataFrame(matrix, columns=FEATURE_ORDER)
    return df, matrix

def run_vectorized_inference(model: Any, X_input: pd.DataFrame) -> List[Dict[str, Any]]:
    # Exectue model prediction / batch inference using vectorised ops
    preds = model.predict(X_input)
    probas = model.predict_proba(X_input)[:, 1]

    results = [
        {"is_fraud": bool(is_fraud), "fraud_proba": float(proba)}
        for is_fraud, proba in zip(preds, probas)
    ]
    return results