from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FinAgent API"
    app_env: str = "dev"
    secret_key: str = "change-me-change-me-change-me-change-me"
    api_prefix: str = "/api/v1"
    database_url: str = "mysql+pymysql://finagent:password@localhost:3306/finagent"
    redis_url: str = "redis://localhost:6379/0"
    s3_endpoint: str = "localhost:8333"
    s3_access_key: str = "finagent"
    s3_secret_key: str = "change-me"
    s3_bucket: str = "finagent"
    s3_secure: bool = False
    s3_public_endpoint: str = "http://localhost:8333"
    qdrant_url: str = "http://localhost:6333"
    llm_provider: str = "ollama"
    ocr_provider: str = "paddleocr"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
