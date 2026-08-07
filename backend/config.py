"""
Central configuration using pydantic-settings.
All values are loaded from the .env file.
Import the `settings` singleton everywhere in the project.
Never read os.environ directly anywhere else.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    REDIS_URL: str
    STORAGE_BASE: Path = Path("./storage")
    CHUNK_DURATION_SEC: int = 30  # legacy v1 pipeline only; v2 uses constants.TILE_SEC/AUDIO_WINDOW_SEC
    MODEL_WEIGHTS_PATH: Path = Path("./weights")
    LOG_LEVEL: str = "INFO"

    # Commentators react *after* the play — shifting word timestamps earlier by
    # this amount before gridding may improve alignment with visual/audio.
    # Default 0 keeps behaviour deterministic until this is measured; 2.0s is
    # a reasonable starting point to experiment with.
    COMMENTARY_LAG_SEC: float = 0.0
    WHISPER_MODEL_SIZE: str = "base"

    # How often the commentary task writes a "still alive" heartbeat to
    # match.progress while inside its single long Whisper/inference calls
    # (which have no internal progress callback of their own). Lets the
    # frontend tell "legitimately slow" apart from "worker died silently".
    COMMENTARY_HEARTBEAT_SEC: float = 20.0

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Synchronous driver URL for Celery workers."""
        url = self.DATABASE_URL
        if "asyncpg" in url:
            url = url.replace("postgresql+asyncpg", "postgresql+psycopg2")
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://")
        return url

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Async driver URL for FastAPI endpoints."""
        url = self.DATABASE_URL
        if "asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        return url


settings = Settings()
