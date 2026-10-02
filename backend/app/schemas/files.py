from pydantic import BaseModel, Field


ALLOWED_FILE_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_FILE_SIZE = 20 * 1024 * 1024


class FilePresignRequest(BaseModel):
    owner_type: str = Field(pattern=r"^[a-z_]+$")
    owner_id: str
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str
    size_bytes: int = Field(ge=1, le=MAX_FILE_SIZE)


class FileCompleteRequest(BaseModel):
    sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")


class FileView(BaseModel):
    id: str
    status: str
    ocr_status: str
    object_key: str
    file_name: str
    size_bytes: int
    job_id: str | None = None
