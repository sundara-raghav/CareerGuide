"""
Application configuration classes for different environments.

Pattern: Environment-specific classes inherit from BaseConfig.
Selected via FLASK_ENV environment variable.
"""

import os
from datetime import timedelta


class BaseConfig:
    """Shared settings across all environments."""

    APP_NAME: str = os.getenv("APP_NAME", "CareerGuide India")
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-prod")

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")

    # Google Maps
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")

    # Email
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    MAIL_DEFAULT_SENDER: str = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@careerguide.in")

    # Twilio (SMS + WhatsApp)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    TWILIO_WHATSAPP_FROM: str = os.getenv("TWILIO_WHATSAPP_FROM", "")

    # Redis / Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # Sentry
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")

    # ML
    ML_ARTIFACTS_DIR: str = os.getenv("ML_ARTIFACTS_DIR", "app/ml/artifacts")
    ML_MODEL_VERSION: str = os.getenv("ML_MODEL_VERSION", "v1")

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Rate limiting
    RATELIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "200 per hour")
    RATELIMIT_STORAGE_URL = os.getenv("REDIS_URL", "memory://")

    # File uploads
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_SIZE_MB", 5)) * 1024 * 1024
    UPLOAD_FOLDER = "app/static/uploads"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

    # i18n
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")
    SUPPORTED_LANGUAGES: list[str] = os.getenv("SUPPORTED_LANGUAGES", "en,ta,hi").split(",")

    # WTF CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600


class DevelopmentConfig(BaseConfig):
    """Local development — verbose, SQLite fallback."""

    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///careerguide_dev.db")
    WTF_CSRF_ENABLED = False  # Easier API testing locally
    SESSION_COOKIE_SECURE = False


class TestingConfig(BaseConfig):
    """Isolated test environment — in-memory SQLite."""

    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SENTRY_DSN = ""  # Never send errors from tests


class ProductionConfig(BaseConfig):
    """Production — strict security, PostgreSQL required."""

    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    @classmethod
    def validate(cls) -> None:
        required = [
            "DATABASE_URL",
            "FLASK_SECRET_KEY",
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY",
        ]
        missing = [k for k in required if not os.getenv(k)]
        if missing:
            raise OSError(f"Missing required environment variables: {', '.join(missing)}")


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(env: str = "development") -> type[BaseConfig]:
    return CONFIG_MAP.get(env, DevelopmentConfig)
