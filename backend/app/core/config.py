from functools import lru_cache
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./elimuquest.db"
    jwt_secret: str = "local-development-secret-change-before-deploy-12345"
    jwt_issuer: str = "elimuquest-api"
    access_token_minutes: int = 60
    cors_origins: str = "http://localhost:8081,http://localhost:19006"
    log_level: str = "INFO"

    @model_validator(mode="after")
    def require_deployment_secret(self) -> "Settings":
        if self.app_env.lower() == "production":
            if len(self.jwt_secret) < 32 or self.jwt_secret.startswith("local-development"):
                raise ValueError(
                    "JWT_SECRET must be a unique secret of at least 32 characters in production"
                )
            if self.database_url == "sqlite:///./elimuquest.db":
                raise ValueError(
                    "DATABASE_URL must be explicitly configured for production persistence"
                )
            origins = self.allowed_origins
            if not origins or any(
                urlparse(origin).scheme != "https"
                or urlparse(origin).hostname in {"localhost", "127.0.0.1", "::1"}
                for origin in origins
            ):
                raise ValueError(
                    "CORS_ORIGINS must contain explicit HTTPS origins in production"
                )
        return self

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
