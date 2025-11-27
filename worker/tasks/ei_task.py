import requests

from worker.celery_app import celery_app


@celery_app.task(bind=True)
def upload_to_edge(self, data_id: str):
    API_KEY = "ei_1df40caea3a8ff4b9869f87c5fef6f3408a7e89982cac9ddd017e964fcbca70a"
    try:
        json_data = {
            "protected": {"ver": "v1", "alg": "HS256", "iat": 1564128599},
            "signature": "b0ee0572a1984b93b6bc56e6576e2cbbd6bccd65d0c356e26b31bbc9a48210c6",
            "payload": {
                "device_name": "ac:87:a3:0a:2d:1b",
                "device_type": "DISCO-L475VG-IOT01A",
                "interval_ms": 10,
                "sensors": [
                    {"name": "accX", "units": "m/s2"},
                    {"name": "accY", "units": "m/s2"},
                    {"name": "accZ", "units": "m/s2"},
                ],
                "values": [
                    [-9.81, 0.03, 1.21],
                    [-9.83, 0.04, 1.27],
                    [-9.12, 0.03, 1.23],
                    [-9.14, 0.01, 1.25],
                ],
            },
        }
        with requests.Session() as s:
            res = s.post(
                "https://ingestion.edgeimpulse.com/api/training/data",
                headers={
                    "x-label": "test",
                    "x-file-name": "test.json",
                    "x-api-key": API_KEY,
                    "Content-Type": "application/json",
                },
                json=json_data,
                timeout=30,
            )
            res.raise_for_status()
        return {"status": "success", "data_id": data_id}
    except Exception as e:
        # Celery auto retry
        raise self.retry(exc=e, countdown=5, max_retries=3)
