from locust import HttpUser, task, between
import random
from app.config import API_PREFIX

API_PREFIX_STR = str(API_PREFIX).strip("/")

class InferenceUser(HttpUser):
    wait_time = between(0.01, 0.1)

    def _generate_single_transaction(self) -> dict:
        payload = {
            "Time": round(random.uniform(0.0, 172800.0), 2),
            "Amount": round(random.uniform(50.0, 2500.0), 2)
        }
        for i in range(1,29):
            payload[f"V{i}"] = round(random.gauss(0.0, 2.0), 4)

        return payload

    def _generate_batch_transactions(self, batch_size: int = 50) -> dict:
        return {
            "transactions": [
                self._generate_single_transaction() for _ in range(batch_size)
            ]
        }

    def _generate_spoofed_headers(self) -> dict:
        fake_ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        return {
            "Content-Type": "application/json",
            "X-Forwarded-For": str(fake_ip)
        }

    @task(5)
    def predict_sync(self):
        payload = self._generate_single_transaction()
        headers = self._generate_spoofed_headers()
        self.client.post(
            f"/{API_PREFIX_STR}/predict",
            json=payload,
            headers=headers,
            name=f"/{API_PREFIX_STR}/predict (Sync Inference)"
        )

    @task(3)
    def predict_async(self):
        payload = self._generate_single_transaction()
        headers = self._generate_spoofed_headers()
        self.client.post(
            f"/{API_PREFIX_STR}/predict/async",
            json=payload,
            headers=headers,
            name=f"/{API_PREFIX_STR}/predict/async (Task Queue)"
        )

    @task(1)
    def predict_batch_sync(self):
        payload = self._generate_batch_transactions(batch_size=random.randint(10,50))
        headers = self._generate_spoofed_headers()
        self.client.post(
            f"/{API_PREFIX_STR}/predict/batch",
            json=payload,
            headers=headers,
            name=f"/{API_PREFIX_STR}/predict/batch (Sync Batch)"
        )

    @task(1)
    def predict_batch_async(self):
        payload = self._generate_batch_transactions(batch_size=random.randint(10,50))
        headers = self._generate_spoofed_headers()
        self.client.post(
            f"/{API_PREFIX_STR}/predict/batch/async",
            json=payload,
            headers=headers,
            name=f"/{API_PREFIX_STR}/predict/batch/async (Async Batch)" 
        )
