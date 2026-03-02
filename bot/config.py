from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(default="", alias="BOT_TOKEN")
    bot_parse_mode: str = Field(default="HTML", alias="BOT_PARSE_MODE")
    webhook_url: str = Field(default="", alias="WEBHOOK_URL")
    webhook_secret: str = Field(default="", alias="WEBHOOK_SECRET")

    database_url: str = Field(alias="DATABASE_URL")
    database_pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/1", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        alias="CELERY_RESULT_BACKEND",
    )

    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket_photos: str = Field(default="jambot-photos", alias="MINIO_BUCKET_PHOTOS")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    ollama_url: str = Field(default="http://localhost:11434", alias="OLLAMA_URL")
    ollama_model: str = Field(default="mistral", alias="OLLAMA_MODEL")

    admin_secret_key: str = Field(default="change-me", alias="ADMIN_SECRET_KEY")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password_hash: str = Field(default="", alias="ADMIN_PASSWORD_HASH")

    proxy_list_url: str = Field(default="", alias="PROXY_LIST_URL")
    max_concurrent_parsers: int = Field(default=3, alias="MAX_CONCURRENT_PARSERS")
    parse_delay_min: float = Field(default=3.0, alias="PARSE_DELAY_MIN")
    parse_delay_max: float = Field(default=8.0, alias="PARSE_DELAY_MAX")

    prometheus_port: int = Field(default=9090, alias="PROMETHEUS_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    parser_enabled: bool = Field(default=True, alias="PARSER_ENABLED")
    ai_enabled: bool = Field(default=True, alias="AI_ENABLED")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    default_timezone: str = Field(default="Europe/Moscow", alias="DEFAULT_TIMEZONE")


@lru_cache
def get_settings() -> Settings:
    return Settings()
