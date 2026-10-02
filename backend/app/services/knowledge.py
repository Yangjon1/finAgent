import hashlib
import json
import math
import re
from uuid import uuid4

from qdrant_client import QdrantClient, models
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.knowledge import KnowledgeBase, KnowledgeChunk, KnowledgeDocument

VECTOR_SIZE = 384


def collection_name(tenant_id: str) -> str:
    return f"finagent_knowledge_{tenant_id.replace('-', '_')}"


def embed_text(text: str) -> list[float]:
    """Deterministic local embedding fallback; replace with FastEmbed in production."""
    vector = [0.0] * VECTOR_SIZE
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower()) or [text]
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for offset in range(0, len(digest), 2):
            index = int.from_bytes(digest[offset:offset + 2], "big") % VECTOR_SIZE
            vector[index] += 1.0 if digest[offset] % 2 else -1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def qdrant_client() -> QdrantClient:
    return QdrantClient(url=get_settings().qdrant_url, timeout=5)


def ensure_collection(client: QdrantClient, tenant_id: str) -> str:
    name = collection_name(tenant_id)
    existing = {item.name for item in client.get_collections().collections}
    if name not in existing:
        client.create_collection(name, vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE))
    return name


def split_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    normalized = re.sub(r"\r\n?", "\n", text).strip()
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        if end < len(normalized):
            paragraph_break = normalized.rfind("\n", start, end)
            if paragraph_break > start + chunk_size // 2:
                end = paragraph_break
        chunks.append(normalized[start:end].strip())
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)
    return [chunk for chunk in chunks if chunk]


def index_document(db: Session, document: KnowledgeDocument, content: str) -> int:
    chunks = split_text(content)
    client = qdrant_client()
    collection = ensure_collection(client, document.tenant_id)
    db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document.id).delete()
    points = []
    for index, chunk_text in enumerate(chunks):
        vector_id = str(uuid4())
        chunk = KnowledgeChunk(tenant_id=document.tenant_id, document_id=document.id, chunk_index=index, text=chunk_text, vector_id=vector_id, metadata_json=json.dumps({"title": document.title, "knowledge_base_id": document.knowledge_base_id}, ensure_ascii=False))
        db.add(chunk)
        points.append(models.PointStruct(id=vector_id, vector=embed_text(chunk_text), payload={"tenant_id": document.tenant_id, "knowledge_base_id": document.knowledge_base_id, "document_id": document.id, "chunk_id": vector_id, "title": document.title, "text": chunk_text, "chunk_index": index}))
    if points:
        client.upsert(collection, points=points, wait=True)
    document.chunk_count = len(chunks)
    document.status = "INDEXED"
    return len(chunks)


def search_knowledge(tenant_id: str, query: str, knowledge_base_id: str | None = None, top_k: int = 5) -> list[dict]:
    client = qdrant_client()
    collection = ensure_collection(client, tenant_id)
    conditions = [models.FieldCondition(key="tenant_id", match=models.MatchValue(value=tenant_id))]
    if knowledge_base_id:
        conditions.append(models.FieldCondition(key="knowledge_base_id", match=models.MatchValue(value=knowledge_base_id)))
    hits = client.query_points(collection, query=embed_text(query), query_filter=models.Filter(must=conditions), limit=top_k, with_payload=True).points
    return [{"score": hit.score, **(hit.payload or {})} for hit in hits]
