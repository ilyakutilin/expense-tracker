from pathlib import Path

from dotenv import find_dotenv
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

    host: str = "localhost"
    port: int = 5432
    name: str = "postgres"
    user: str = "postgres"
    password: str = ""

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.name}"
        )


db_settings = DBSettings()
