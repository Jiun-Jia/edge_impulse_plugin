from celery import Celery
from app.config import settings
from app.ei_client import EdgeImpulseClient
from app.models import DataSample, TrainingJob, InferenceLog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
import asyncio
from datetime import datetime
import httpx

from worker.celery_app import celery_app

# 資料庫設定
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def run_async(coro):
    """Helper to run async functions in Celery"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


@celery_app.task(name="upload_to_edge_impulse")
def upload_to_edge_impulse(sample_id: int):
    """
    將資料樣本上傳到 Edge Impulse
    """
    db = SessionLocal()
    try:
        sample = db.query(DataSample).filter(DataSample.id == sample_id).first()
        if not sample:
            logger.error(f"找不到樣本 ID: {sample_id}")
            return {"status": "error", "message": "Sample not found"}

        ei_client = EdgeImpulseClient()

        result = run_async(
            ei_client.upload_sample(
                device_id=sample.device_id,
                sensor_type=sample.sensor_type,
                sample_rate=sample.sample_rate,
                data=sample.data,
                label=sample.label,
            )
        )

        # 更新資料庫
        sample.uploaded_to_ei = True
        sample.ei_sample_id = result.get("id")
        db.commit()

        logger.info(f"樣本 {sample_id} 已上傳到 Edge Impulse")

        # 檢查是否達到自動訓練閾值
        check_auto_training.delay()

        return {"status": "success", "ei_sample_id": result.get("id")}

    except Exception as e:
        logger.error(f"上傳樣本失敗: {e}")
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="check_auto_training")
def check_auto_training():
    """
    檢查是否達到自動訓練條件
    """
    db = SessionLocal()
    try:
        # 計算未用於訓練的新樣本數量
        new_samples_count = (
            db.query(DataSample).filter(DataSample.uploaded_to_ei == True).count()
        )

        logger.info(f"目前有 {new_samples_count} 個新樣本")

        if new_samples_count >= settings.AUTO_TRAINING_THRESHOLD:
            logger.info("達到自動訓練閾值，觸發訓練")
            trigger_training.delay(triggered_by="auto")

        return {"new_samples": new_samples_count}

    except Exception as e:
        logger.error(f"檢查自動訓練失敗: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="trigger_training")
def trigger_training(triggered_by: str = "manual"):
    """
    觸發 Edge Impulse 訓練
    """
    db = SessionLocal()
    try:
        ei_client = EdgeImpulseClient()

        samples_count = (
            db.query(DataSample).filter(DataSample.uploaded_to_ei == True).count()
        )

        result = run_async(ei_client.trigger_training(samples_count=samples_count))

        # 記錄訓練任務
        job = TrainingJob(
            ei_job_id=result.get("id"),
            status="pending",
            triggered_by=triggered_by,
            samples_count=samples_count,
            started_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()

        logger.info(f"訓練任務已觸發: {result.get('id')}")

        # 開始監控訓練狀態
        monitor_training.delay(job.id)

        return {"status": "success", "job_id": result.get("id")}

    except Exception as e:
        logger.error(f"觸發訓練失敗: {e}")
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="monitor_training")
def monitor_training(job_id: int):
    """
    監控訓練狀態
    """
    db = SessionLocal()
    try:
        job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if not job:
            logger.error(f"找不到訓練任務 ID: {job_id}")
            return

        ei_client = EdgeImpulseClient()
        status_result = run_async(ei_client.get_training_status(job.ei_job_id))

        job.status = status_result.get("status")

        if job.status == "completed":
            job.completed_at = datetime.utcnow()
            job.accuracy = status_result.get("accuracy")
            db.commit()

            logger.info(f"訓練完成: {job.ei_job_id}, 準確率: {job.accuracy}")

            # 自動部署模型
            deploy_model.delay(job.id)

        elif job.status == "failed":
            job.completed_at = datetime.utcnow()
            job.error_message = status_result.get("error")
            db.commit()

            logger.error(f"訓練失敗: {job.ei_job_id}, 錯誤: {job.error_message}")

        elif job.status in ["pending", "running"]:
            db.commit()
            # 繼續監控（每 30 秒檢查一次）
            monitor_training.apply_async(args=[job_id], countdown=30)

        return {"status": job.status}

    except Exception as e:
        logger.error(f"監控訓練狀態失敗: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="deploy_model")
def deploy_model(job_id: int):
    """
    部署訓練好的模型
    """
    db = SessionLocal()
    try:
        job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if not job:
            logger.error(f"找不到訓練任務 ID: {job_id}")
            return

        ei_client = EdgeImpulseClient()
        result = run_async(ei_client.deploy_model(target=settings.SIMULATE_PLATFORM))

        logger.info(f"模型已部署: {result}")

        return {"status": "success", "deployment": result}

    except Exception as e:
        logger.error(f"部署模型失敗: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="fetch_virtual_device_data")
def fetch_virtual_device_data(device_id: str):
    """
    從 Virtual Device 獲取資料
    """
    db = SessionLocal()
    try:
        url = f"{settings.VIRTUAL_DEVICE_URL}/api/devices/{device_id}/data"
        headers = {}

        if settings.VIRTUAL_DEVICE_API_KEY:
            headers["Authorization"] = f"Bearer {settings.VIRTUAL_DEVICE_API_KEY}"

        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()

        # 儲存到資料庫
        for item in data.get("samples", []):
            sample = DataSample(
                device_id=device_id,
                sensor_type=item.get("sensor_type"),
                sample_rate=item.get("sample_rate"),
                data=item.get("data"),
                metadata=item.get("metadata", {}),
                label=item.get("label"),
            )
            db.add(sample)

        db.commit()

        # 上傳到 Edge Impulse
        samples = (
            db.query(DataSample)
            .filter(
                DataSample.device_id == device_id, DataSample.uploaded_to_ei == False
            )
            .all()
        )

        for sample in samples:
            upload_to_edge_impulse.delay(sample.id)

        logger.info(
            f"從 Virtual Device {device_id} 獲取了 {len(data.get('samples', []))} 個樣本"
        )

        return {"status": "success", "samples_count": len(data.get("samples", []))}

    except Exception as e:
        logger.error(f"從 Virtual Device 獲取資料失敗: {e}")
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
