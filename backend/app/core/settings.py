import pathlib
from pathlib import Path

from dotenv import find_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.fs import ensure_dir

APP_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = APP_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent


if Path.exists(BACKEND_DIR / ".env"):
    ENV_FILE = BACKEND_DIR / ".env"
elif Path.exists(PROJECT_DIR / ".env"):
    ENV_FILE = PROJECT_DIR / ".env"
else:
    env_file = find_dotenv()
    ENV_FILE = Path(env_file) if env_file else None

SETTINGS_MODEL_CONFIG = SettingsConfigDict(
    env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore"
)


class LogSettings(BaseSettings):
    model_config = SETTINGS_MODEL_CONFIG.copy()
    model_config["env_prefix"] = "log_"

    DIR_PATH: str = "logs"
    STREAM_LEVEL: str = "INFO"
    FILE_LEVEL: str = "INFO"
    FILE_ROTATION_MB: int = 10
    FILE_RETENTION_DAYS: int = 10

    @property
    def validated_dir_path(self) -> pathlib.Path:
        return ensure_dir(self.DIR_PATH)


class DBSettings(BaseSettings):
    model_config = SETTINGS_MODEL_CONFIG.copy()
    model_config["env_prefix"] = "db_"

    HOST: str = "localhost"
    PORT: int = 5432
    NAME: str = "postgres"
    USER: str = "postgres"
    PASSWORD: str = ""

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@"
            f"{self.HOST}:{self.PORT}/{self.NAME}"
        )


class RedisSettings(BaseSettings):
    model_config = SETTINGS_MODEL_CONFIG.copy()
    model_config["env_prefix"] = "redis_"

    HOST: str = "localhost"
    PORT: int = 6379
    DB: int = 0
    USERNAME: str = ""
    PASSWORD: str = ""
    EXPIRE_SECONDS: int = 3600

    @property
    def url(self) -> str:
        return (
            "redis://"
            f"{self.USERNAME}"
            f"{':' if self.PASSWORD else ''}{self.PASSWORD}"
            f"{'@' if self.USERNAME or self.PASSWORD else ''}"
            f"{self.HOST}:{self.PORT}/{self.DB}"
        )


class AuthSettings(BaseSettings):
    model_config = SETTINGS_MODEL_CONFIG.copy()
    model_config["env_prefix"] = "auth_"

    SECRET_KEY: str = ""  # Generate with: openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @field_validator("SECRET_KEY", mode="after")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if v == "":
            raise ValueError("Please set the auth secret key")

        return v


class Settings(BaseSettings):
    model_config = SETTINGS_MODEL_CONFIG.copy()

    PROJECT_NAME: str = "Expense Tracker"
    APP_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    BACKEND_CORS_ORIGINS: list[str] = []

    NUMERIC_PRECISION: int = 23
    NUMERIC_SCALE: int = 8

    log_settings: LogSettings = LogSettings()
    db_settings: DBSettings = DBSettings()
    auth_settings: AuthSettings = AuthSettings()
    redis_settings: RedisSettings = RedisSettings()

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @property
    def cors_origins(self) -> list[str]:
        if self.DEBUG:
            return ["*"]
        return self.BACKEND_CORS_ORIGINS


settings = Settings()
