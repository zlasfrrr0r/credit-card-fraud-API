# Credit Card Fraud Detection API

An ML Inference API for detecting fraudulent credit card transactions.

Exposes a REST API built with FastAPI, loads a pre-trained scikit-learn pipeline which I trained beforehand, and returns a fraud prediction (0 = legitimate, 1 = fraud) as well as the probability of the transaction being fraudulent. 

## Model Used

- **Algorithm**: Logistic Regression
- **Preprocessing**: StandardScaler
- **Dataset**: [Kaggle- Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
- **Probability Calibration**: *Isotonic* regression via *CalibratedClassifierCV*

## API Endpoints

### Health Check

#### GET `/health`

#### Request

```bash
GET http://localhost:8000/api/v1/health
```

#### Response

```json
{
    "Health": "OK"
}
```

#### GET `/`

#### Request

```bash
GET http://localhost:8000/api/v1
```

#### Response

```json
{
 "Message": "Root"
}
```

## Predict Fraud

### POST `/predict`

Predict whether a transaction is fraudulent.

### Request Body

```bash
POST http://localhost:8000/api/v1/predict
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

##### Response fields

- `"is_fraud"`: Model prediction (0/1)
- `"fraud_proba"`: Probability of fraud

### Running locally (Docker)

Run the following (Docker Engine must be on):

```bash
docker build -t fraud-detection-api .
docker run -p 8000:8000 fraud-detection-api
```

API will be available at:

```bash
http://localhost:8000/api/v1
```

### Dependencies

Found at requirements.txt

###### Next?

- CI to be added soon.
- Following that will be deployment.
- CI/CD follows that.