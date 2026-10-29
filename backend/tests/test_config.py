import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_the_development_signing_secret():
    with pytest.raises(ValidationError, match="JWT_SECRET must be a unique secret"):
        Settings(
            _env_file=None,
            app_env="production",
            database_url="postgresql+psycopg://user:password@database:5432/elimuquest",
            jwt_secret="local-development-secret-change-before-deploy-12345",
        )


def test_production_rejects_the_default_database_url():
    with pytest.raises(ValidationError, match="DATABASE_URL must be explicitly configured"):
        Settings(
            _env_file=None,
            app_env="production",
            jwt_secret="unique-production-signing-secret-with-adequate-length",
            cors_origins="https://learn.example.test",
        )


def test_production_rejects_development_cors_origins():
    with pytest.raises(ValidationError, match="CORS_ORIGINS must contain explicit HTTPS origins"):
        Settings(
            _env_file=None,
            app_env="production",
            database_url="postgresql+psycopg://user:password@database:5432/elimuquest",
            jwt_secret="unique-production-signing-secret-with-adequate-length",
        )


def test_production_accepts_explicit_persistence_and_a_unique_secret():
    settings = Settings(
        _env_file=None,
        app_env="production",
        database_url="postgresql+psycopg://user:password@database:5432/elimuquest",
        jwt_secret="unique-production-signing-secret-with-adequate-length",
        cors_origins="https://learn.example.test",
    )

    assert settings.app_env == "production"
    assert settings.database_url.startswith("postgresql+psycopg://")
