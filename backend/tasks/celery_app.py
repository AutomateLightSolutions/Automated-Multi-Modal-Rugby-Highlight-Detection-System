"""
Celery application factory and queue configuration.
"""
import sys
from pathlib import Path

# Ensure backend/ is on sys.path so sibling packages (pipeline, modules, etc.)
# are importable however Celery is invoked (script vs python -m).
_backend_dir = Path(__file__).resolve().parent.parent
_backend_str = str(_backend_dir)
_resolved = [str(Path(p).resolve()) for p in sys.path if p]
if _backend_str not in _resolved:
    sys.path.insert(0, _backend_str)

from celery import Celery

from config import settings

app = Celery(
    "rugby_highlights",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.tasks"],
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    task_soft_time_limit=3300,  # raise SoftTimeLimitExceeded at 55 min → task can mark match as failed
    task_time_limit=3600,       # hard kill at 60 min if soft limit was ignored
    task_routes={
        "tasks.tasks.run_visual_module":       {"queue": "ml"},
        "tasks.tasks.run_commentary_module":   {"queue": "ml"},
        "tasks.tasks.run_audio_energy_module": {"queue": "ml"},
        "tasks.tasks.run_fusion":              {"queue": "fusion"},
        "tasks.tasks.generate_highlight":      {"queue": "default"},
        "tasks.tasks.process_match":           {"queue": "default"},
    },
)
