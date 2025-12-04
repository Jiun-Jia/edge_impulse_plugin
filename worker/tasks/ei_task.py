import requests

from common.models import UploadRequest
from app.services.converter import weda_to_edgeimpulse

from logs import worker_logger as logger
from worker import celery_app


@celery_app.task(bind=True, queue="EI_ingestion")
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


@celery_app.task(bind=True, queue="EI_ingestion")
def convert_and_upload(self, upload_request: UploadRequest):
    try:
        upload_request = UploadRequest.model_validate(upload_request)
        weda = upload_request.weda
        metadata = upload_request.metadata

        # Convert WEDA to EI format
        ei_data = weda_to_edgeimpulse(weda, hmac_key=metadata.hmac_key)

        with requests.Session() as s:
            res = s.post(
                f"https://ingestion.edgeimpulse.com/api/{metadata.dataset_type.value}/data",
                headers={
                    "Content-Type": "application/json",
                    "x-file-name": metadata.file_name or "data.json",
                    "x-label": metadata.label,
                    "x-no-label": "1" if metadata.no_label else "0",
                    "x-api-key": metadata.api_key,
                },
                data=ei_data,
                timeout=30,
            )
            res.raise_for_status()
        return {
            "status": "success",
            "message": "Data ingested to Edge Impulse",
            "task_id": self.request.id,
        }
    except Exception as e:
        # Celery auto retry
        raise self.retry(exc=e, countdown=5, max_retries=3)
