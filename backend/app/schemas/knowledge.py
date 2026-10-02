from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=512)


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    source_type: str = "TEXT"
    file_id: str | None = None


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    knowledge_base_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
