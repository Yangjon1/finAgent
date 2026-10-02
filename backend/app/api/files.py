import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.response import ok
from app.core.security import CurrentUser, DataScopeDependency, require_permission
from app.db import get_db
from app.models.expense import ExpenseReport, JobRecord, StoredFile
from app.schemas.files import ALLOWED_FILE_TYPES, FileCompleteRequest, FilePresignRequest
from app.services.storage import make_object_key, presign_get, presign_put, s3_client

router = APIRouter(prefix="/files", tags=["files"])
settings = get_settings()


def ensure_owner(payload: FilePresignRequest, user: CurrentUser, scope: DataScopeDependency, db: Session) -> None:
    if payload.owner_type != "expense_report":
        raise HTTPException(status_code=422, detail="当前只支持报销单附件")
    report = db.scalar(select(ExpenseReport).where(ExpenseReport.id == payload.owner_id))
    if not report or not scope.allows(tenant_id=report.tenant_id, user_id=report.applicant_id):
        raise HTTPException(status_code=404, detail="业务单据不存在")


@router.post("/presign", dependencies=[Depends(require_permission("file:presign"))])
def presign_file(payload: FilePresignRequest, request: Request, user: CurrentUser, scope: DataScopeDependency, db: Session = Depends(get_db)):
    if payload.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=422, detail="只支持 JPG、PNG 和 PDF 文件")
    ensure_owner(payload, user, scope, db)
    object_key = make_object_key(user.tenant_id, payload.owner_type, payload.owner_id, payload.file_name)
    file = StoredFile(tenant_id=user.tenant_id, object_key=object_key, status="PRESIGNED", ocr_status="NOT_STARTED", **payload.model_dump())
    db.add(file)
    db.commit()
    db.refresh(file)
    return ok({"file_id": file.id, "object_key": object_key, "upload_url": presign_put(settings, object_key, payload.content_type), "expires_in": 900}, request)


@router.post("/{file_id}/complete", dependencies=[Depends(require_permission("file:complete"))])
def complete_file(file_id: str, payload: FileCompleteRequest, request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    file = db.scalar(select(StoredFile).where(StoredFile.id == file_id, StoredFile.tenant_id == user.tenant_id))
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    try:
        metadata = s3_client(settings).head_object(Bucket=settings.s3_bucket, Key=file.object_key)
    except Exception as exc:
        raise HTTPException(status_code=409, detail="对象存储中尚未发现上传文件") from exc
    if metadata.get("ContentLength", 0) > file.size_bytes:
        raise HTTPException(status_code=422, detail="上传文件大小超过预声明大小")
    file.status = "UPLOADED"
    file.ocr_status = "QUEUED"
    file.sha256 = payload.sha256
    file.uploaded_at = datetime.now(timezone.utc)
    job = JobRecord(tenant_id=user.tenant_id, job_type="OCR", resource_type="file", resource_id=file.id, status="QUEUED", payload_json=json.dumps({"file_id": file.id}, ensure_ascii=False))
    db.add(job)
    db.flush()
    Redis.from_url(settings.redis_url).rpush("finagent:jobs:ocr", json.dumps({"job_id": job.id}))
    db.commit()
    return ok({"file_id": file.id, "job_id": job.id, "status": file.status, "ocr_status": file.ocr_status}, request)


@router.get("/{file_id}")
def get_file(file_id: str, request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    file = db.scalar(select(StoredFile).where(StoredFile.id == file_id, StoredFile.tenant_id == user.tenant_id))
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    return ok({"id": file.id, "file_name": file.file_name, "content_type": file.content_type, "size_bytes": file.size_bytes, "status": file.status, "ocr_status": file.ocr_status, "ocr_result": json.loads(file.ocr_result_json) if file.ocr_result_json else None, "error_message": file.error_message}, request)


@router.get("/{file_id}/download")
def download_file(file_id: str, request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    file = db.scalar(select(StoredFile).where(StoredFile.id == file_id, StoredFile.tenant_id == user.tenant_id))
    if not file or file.status != "UPLOADED":
        raise HTTPException(status_code=404, detail="可下载文件不存在")
    return ok({"download_url": presign_get(settings, file.object_key), "expires_in": 600}, request)
