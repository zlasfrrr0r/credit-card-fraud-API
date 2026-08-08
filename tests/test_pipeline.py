import pytest
import numpy as np
import pandas as pd
import time

from pydantic import ValidationError
from app.schemas import Transaction, TransactionBatch
from app.pipeline import FEATURE_ORDER, preprocess_single, preprocess_batch_vectorized

# schema tests

def test_reject_nan_value(sample_payload):
    invalid_data = sample_payload.copy()
    invalid_data["V1"] = float("nan")

    with pytest.raises(ValidationError) as err_info:
        Transaction(**invalid_data)

    assert "Input contains invalid float (NaN or Infinity)" in str(err_info.value)

def test_reject_inf_value(sample_payload):
    invalid_data = sample_payload.copy()
    invalid_data["Amount"] = float("inf")

    with pytest.raises(ValidationError) as err_info:
        Transaction(**invalid_data)

    assert "Input contains invalid float (NaN or Infinity)" in str(err_info.value)

def test_reject_negative_amount_time(sample_payload):
    invalid_data = sample_payload.copy()
    invalid_data["Amount"] = -10.0

    with pytest.raises(ValidationError):
        Transaction(**invalid_data)

# preprocess & vector tests

def test_preprocess_single(sample_payload):
    transaction = Transaction(**sample_payload)
    df = preprocess_single(transaction)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == FEATURE_ORDER
    assert df.shape == (1, 30)


def test_preprocess_batch_vectorized(sample_batch_payload):
    # Extract the transactions list from sample batch 
    transactions_list = [Transaction(**tx) for tx in sample_batch_payload["transactions"]]
    expected_rows = len(transactions_list)

    df, matrix = preprocess_batch_vectorized(transactions_list)

    assert isinstance(df, pd.DataFrame)
    assert isinstance(matrix, np.ndarray)
    assert df.shape == (expected_rows, 30)
    assert matrix.shape == (expected_rows, 30)
    assert list(df.columns) == FEATURE_ORDER

# performance tests
"""
We want to know if our vectorisation method has 
better performance than our old legacy method when 
there are 1,000 transactions to predict
"""

def test_benchmark_vectorized_vs_iterrows(sample_payload):

    sample_count = 1000
    transactions = [Transaction(**sample_payload) for _ in range(sample_count)]

    # (.iterrows) Performance
    start_time = time.perf_counter()

    batch_dicts = [t.model_dump() for t in transactions]
    temp_df = pd.DataFrame(batch_dicts, columns=FEATURE_ORDER)

    extracted_rows = []
    for index, row in temp_df.iterrows():
        extracted_rows.append(row.to_numpy())
    legacy_matrix = np.array(extracted_rows)

    iterrows_duration = time.perf_counter() - start_time

    # (to_numpy) Performance
    start_time = time.perf_counter()

    vectorized_df, vectorized_matrix = preprocess_batch_vectorized(transactions)

    vectorized_duration = time.perf_counter() - start_time

    # Assert parity
    np.testing.assert_array_almost_equal(legacy_matrix, vectorized_matrix)

    # Find Speedup
    speedup = iterrows_duration / max(vectorized_duration, 1e-9)

    # Assert vectorized pipeline higher performance than row-by-row iteration time
    assert vectorized_duration < iterrows_duration
