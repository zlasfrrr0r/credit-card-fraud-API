# Credit Card Fraud Detection API

An ML Inference API for detecting fraudulent credit card transactions.

Exposes a REST API built with FastAPI, loads a pre-trained scikit-learn pipeline which I trained beforehand, and returns a fraud prediction (0 = legitimate, 1 = fraud) as well as the probability of the transaction being fraudulent. 

Navigate:
- [Model](#model-used)
- [API Endpoints](#api-endpoints)
  - [Health](#health-check)
  - [Root](#root)
  - [Predict](#predict)
- [API Docs](#api-documentations)

## Model Used

- **Algorithm**: Logistic Regression
- **Preprocessing**: StandardScaler
- **Dataset**: [Kaggle- Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
- **Probability Calibration**: *Isotonic* regression via *CalibratedClassifierCV*

## API Endpoints

**Note**: Since the API is hosted on Render, the first request *may* take **30-60** seconds to respond due cold start.

### Health Check

#### GET `/health`

#### Request

```bash
curl https://credit-card-fraud-api-n78c.onrender.com/api/v1/health
```

#### Response

```json
{
    "Health": "OK"
}
```

### Root

#### GET `/`

#### Request

```bash
curl https://credit-card-fraud-api-n78c.onrender.com/api/v1/
```

#### Response

```json
{
 "Message": "Root"
}
```

### Predict

#### POST `/predict`

Predict whether a transaction is fraudulent.

### Request Body

```bash
curl -X POST \
https://credit-card-fraud-api-n78c.onrender.com/api/v1/predict \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
-d '{ ... }'
```

API expects a single transaction and **only accepts JSON requests**, with the following body:

```json
{
  "Time": 406,    
  "V1": -2.312226542,
  "V2": 1.951992011,
  "V3": -1.609850732,
  "V4": 3.997905588,
  "V5": -0.522187865,
  "V6": -1.426545319,
  "V7": -2.537387306,
  "V8": 1.391657248,
  "V9": -2.770089277,
  "V10": -2.772272145,
  "V11": 3.202033207,
  "V12": -2.899907388,
  "V13": -0.595221881,
  "V14": -4.289253782,
  "V15": 0.38972412,
  "V16": -1.14074718,
  "V17": -2.830055674,
  "V18": -0.016822468,
  "V19": 0.416955705,
  "V20": 0.126910559,
  "V21": 0.517232371,
  "V22": -0.035049369,
  "V23": -0.465211076,
  "V24": 0.320198199,
  "V25": 0.044519167,
  "V26": 0.177839798,
  "V27": 0.261145003,
  "V28": -0.143275874,
  "Amount": 149.62
}
```

## Response

All responses are returned in **JSON format** only.

```json
{
    "is_fraud": 1,
    "fraud_proba": 0.7457997909255049
}
```

## API Documentations

This API is built with [FastAPI](https://fastapi.tiangolo.com/), which automatically generates interactive docs for ease of use. Feel free to explore the endpoints and test requests through the following interfaces:

  - Swagger UI (Interactive Docs): `https://credit-card-fraud-api-n78c.onrender.com/api/v1/docs`

  - ReDoc (Alternative Docs): `https://credit-card-fraud-api-n78c.onrender.com/api/v1/redoc`

  - OpenAPI Schema (Machine-readable): `https://credit-card-fraud-api-n78c.onrender.com/api/v1/openapi.json`

These interfaces allow you to understand the API endpoints, required inputs, and expected responses (without reading source code).


Please reach out for any questions or feedback
