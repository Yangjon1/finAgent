from collections.abc import Callable

import boto3
from qdrant_client import QdrantClient
from redis import Redis
from sqlalchemy import text

from app.core.config import Settings
from app.db import engine


def check_dependencies(settings: Settings) -> dict[str, str]:
    checks: dict[str, str] = {}
    probes: dict[str, Callable[[], None]] = {
        "mysql": lambda: _check_mysql(),
        "redis": lambda: _check_redis(settings),
        "object_storage": lambda: _check_object_storage(settings),
        "qdrant": lambda: _check_qdrant(settings),
    }
    for name, probe in probes.items():
        try:
            probe()
            checks[name] = "ok"
        except Exception as exc:  # readiness should report all dependencies at once
            checks[name] = f"unavailable: {type(exc).__name__}"
    return checks


def _check_mysql() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def _check_redis(settings: Settings) -> None:
    Redis.from_url(settings.redis_url, socket_connect_timeout=1).ping()


def _check_object_storage(settings: Settings) -> None:
    scheme = "https" if settings.s3_secure else "http"
    client = boto3.client(
        "s3",
        endpoint_url=f"{scheme}://{settings.s3_endpoint}",
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name="us-east-1",
    )
    client.list_buckets()


def _check_qdrant(settings: Settings) -> None:
    QdrantClient(url=settings.qdrant_url, timeout=2).get_collections()
