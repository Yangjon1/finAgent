import re
from uuid import uuid4

import boto3
from botocore.config import Config

from app.core.config import Settings


def s3_client(settings: Settings, endpoint_url: str | None = None):
    scheme = "https" if settings.s3_secure else "http"
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url or f"{scheme}://{settings.s3_endpoint}",
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name="us-east-1",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def safe_file_name(file_name: str) -> str:
    name = file_name.replace("\\", "/").split("/")[-1]
    name = re.sub(r"[^\w.\-\u4e00-\u9fff ]", "_", name).strip()
    return name[:180] or "upload"


def make_object_key(tenant_id: str, owner_type: str, owner_id: str, file_name: str) -> str:
    return f"tenants/{tenant_id}/{owner_type}/{owner_id}/{uuid4()}-{safe_file_name(file_name)}"


def presign_put(settings: Settings, object_key: str, content_type: str) -> str:
    client = s3_client(settings, settings.s3_public_endpoint)
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.s3_bucket, "Key": object_key, "ContentType": content_type},
        ExpiresIn=900,
        HttpMethod="PUT",
    )


def presign_get(settings: Settings, object_key: str) -> str:
    return s3_client(settings, settings.s3_public_endpoint).generate_presigned_url(
        "get_object", Params={"Bucket": settings.s3_bucket, "Key": object_key}, ExpiresIn=600
    )
