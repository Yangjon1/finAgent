import json
import logging
from datetime import datetime, timezone

from redis import Redis
from sqlalchemy import select

from app.core.config import get_settings
from app.db import SessionLocal
from app.models.expense import JobRecord, StoredFile
from app.services.ocr import get_ocr_provider, result_json
from app.services.storage import s3_client

logger = logging.getLogger(__name__)


def process_job(job_id: str) -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        job = db.scalar(select(JobRecord).where(JobRecord.id == job_id))
        if not job:
            return
        file = db.scalar(select(StoredFile).where(StoredFile.id == job.resource_id))
        if not file:
            job.status = "FAILED"
            job.error_message = "文件记录不存在"
            db.commit()
            return
        job.status = "RUNNING"
        job.attempts += 1
        job.started_at = datetime.now(timezone.utc)
        file.ocr_status = "PROCESSING"
        db.commit()
        content = s3_client(settings).get_object(Bucket=settings.s3_bucket, Key=file.object_key)["Body"].read()
        result = get_ocr_provider(settings.ocr_provider).extract(content, file.content_type)
        file.ocr_result_json = result_json(result)
        file.ocr_status = "COMPLETED"
        job.result_json = file.ocr_result_json
        job.status = "SUCCEEDED"
        job.ended_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        logger.exception("OCR job failed", extra={"request_id": "worker"})
        job = db.scalar(select(JobRecord).where(JobRecord.id == job_id))
        if job:
            job.status = "FAILED"
            job.error_message = str(exc)[:512]
            job.ended_at = datetime.now(timezone.utc)
        file = db.scalar(select(StoredFile).where(StoredFile.id == job.resource_id)) if job else None
        if file:
            file.ocr_status = "FAILED"
            file.error_message = str(exc)[:512]
        db.commit()
    finally:
        db.close()


def main() -> None:
    settings = get_settings()
    queue = Redis.from_url(settings.redis_url, decode_responses=True)
    logger.info("OCR worker started")
    while True:
        item = queue.brpop("finagent:jobs:ocr", timeout=5)
        if item:
            process_job(json.loads(item[1])["job_id"])


if __name__ == "__main__":
    main()
