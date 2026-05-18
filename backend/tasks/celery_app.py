"""
Celery application factory and queue configuration.
"""
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
    task_routes={
        "tasks.tasks.run_visual_module":       {"queue": "ml"},
        "tasks.tasks.run_commentary_module":   {"queue": "ml"},
        "tasks.tasks.run_audio_energy_module": {"queue": "ml"},
        "tasks.tasks.run_fusion":              {"queue": "fusion"},
        "tasks.tasks.generate_highlight":      {"queue": "default"},
        "tasks.tasks.process_match":           {"queue": "default"},
    },
)
