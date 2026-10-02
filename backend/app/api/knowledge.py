from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.response import ok
from app.core.security import CurrentUser, require_permission
from app.db import get_db
from app.models.knowledge import KnowledgeBase, KnowledgeDocument
from app.schemas.knowledge import KnowledgeBaseCreate, KnowledgeDocumentCreate, KnowledgeSearchRequest
from app.services.knowledge import index_document, search_knowledge

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/bases")
def list_bases(request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    bases = db.scalars(select(KnowledgeBase).where(KnowledgeBase.tenant_id == user.tenant_id).order_by(KnowledgeBase.name)).all()
    return ok([{"id": item.id, "code": item.code, "name": item.name, "description": item.description, "status": item.status} for item in bases], request)


@router.post("/bases", dependencies=[Depends(require_permission("knowledge:base:create"))])
def create_base(payload: KnowledgeBaseCreate, request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    if db.scalar(select(KnowledgeBase).where(KnowledgeBase.tenant_id == user.tenant_id, KnowledgeBase.code == payload.code)):
        raise HTTPException(status_code=409, detail="知识库编码已存在")
    base = KnowledgeBase(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(base)
    db.commit()
    db.refresh(base)
    return ok({"id": base.id, "code": base.code, "name": base.name}, request)


@router.post("/bases/{knowledge_base_id}/documents", dependencies=[Depends(require_permission("knowledge:document:index"))])
def index_document_api(knowledge_base_id: str, payload: KnowledgeDocumentCreate, request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    base = db.scalar(select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id, KnowledgeBase.tenant_id == user.tenant_id))
    if not base:
        raise HTTPException(status_code=404, detail="知识库不存在")
    document = KnowledgeDocument(tenant_id=user.tenant_id, knowledge_base_id=base.id, title=payload.title, source_type=payload.source_type, file_id=payload.file_id, status="INDEXING")
    db.add(document)
    db.flush()
    try:
        chunk_count = index_document(db, document, payload.content)
        db.commit()
    except Exception as exc:
        document.status = "FAILED"
        document.error_message = str(exc)[:512]
        db.commit()
        raise HTTPException(status_code=503, detail="知识库索引失败") from exc
    return ok({"document_id": document.id, "status": document.status, "chunk_count": chunk_count}, request)


@router.post("/search")
def search(payload: KnowledgeSearchRequest, request: Request, user: CurrentUser):
    return ok({"query": payload.query, "hits": search_knowledge(user.tenant_id, payload.query, payload.knowledge_base_id, payload.top_k)}, request)
