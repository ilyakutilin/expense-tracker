from pathlib import Path

from dotenv import find_dotenv
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

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


class Settings(BaseSettings):
    model_config = SETTINGS_MODEL_CONFIG.copy()

    PROJECT_NAME: str = "Expense Tracker"
    APP_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    BACKEND_CORS_ORIGINS: list[str | AnyHttpUrl] = []

    db_settings: DBSettings = DBSettings()

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
