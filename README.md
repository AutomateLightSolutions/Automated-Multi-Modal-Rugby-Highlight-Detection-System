# Rugby Highlight Generator

Automatic rugby match highlight generation using multimodal AI.
Three concurrent modules (visual, commentary, audio energy) feed
into a fusion model to select and assemble highlight segments.

## Quick Start (Docker)
docker-compose up --build

## Manual Setup (without Docker)
# 1. Start PostgreSQL and Redis locally
# 2. Activate venv: source venv/bin/activate
# 3. Copy env: cp .env.example .env  (edit values as needed)
# 4. Run API: uvicorn api.main:app --reload
# 5. Run worker: celery -A tasks.celery_app worker --loglevel=info

## CLI Usage
python cli.py health
python cli.py process --video path/to/match.mp4
python cli.py test-modules --chunk-video path/to/chunk.mp4 \
    --chunk-audio path/to/chunk.wav --start 0 --end 30

## Run Tests
python tests/test_pipeline.py

## Model Weights
Place your trained model weights in:
  weights/visual/rugby_action_classifier.pth
Whisper downloads its own weights automatically on first run.
Audio energy module uses signal processing only (no weights needed).

## Environment Variables
See .env.example for all configuration options.
