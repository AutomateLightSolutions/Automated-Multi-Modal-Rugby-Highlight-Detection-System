# TryVision 🏉

> **Automatic rugby match highlight generation powered by multimodal AI.**
> Three parallel analysis modules — visual action recognition, commentary transcription, and audio energy detection — feed into a fusion engine that selects and assembles the most exciting moments into a downloadable highlight reel.

---

## Architecture

```
Upload ──► FFmpeg Extraction ──► ┌─ Visual Module   (ResNet/ViT) ─┐
                                 ├─ Commentary Module (Whisper/NLP) ┼──► Fusion ──► NMS ──► Assembly
                                 └─ Audio Module    (librosa RMS)  ┘
                                      3 Celery workers · concurrent
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Framer Motion |
| Backend API | FastAPI, Uvicorn |
| Task Queue | Celery 5, Redis |
| Database | PostgreSQL, SQLAlchemy 2 (async) |
| ML | PyTorch, Whisper, librosa, OpenCV |
| Media | FFmpeg |
| Containerisation | Docker, Docker Compose |

---

## Prerequisites

Before starting, make sure you have these installed:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) *(recommended)*
- **Or** for manual setup: Python 3.11, Node.js 18+, PostgreSQL 15, Redis 7, FFmpeg

---

## Option A — Docker (Recommended)

The easiest way. One command starts everything.

```bash
# 1. Clone the repo
git clone <repo-url>
cd rugby_highlight_system

# 2. Create backend environment file
cp backend/.env.example backend/.env
# Edit backend/.env and set your POSTGRES_PASSWORD

# 3. Build and start all services
docker-compose up --build
```

Services started:

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

To stop:
```bash
docker-compose down
```

---

## Option B — Manual Setup (Windows)

Use this if you want to run services individually for development.

### 1. Clone & configure

```bash
git clone <repo-url>
cd rugby_highlight_system
cp backend/.env.example backend/.env
```

Edit `backend/.env`:
```env
POSTGRES_PASSWORD=your_password
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/rugby_highlights
REDIS_URL=redis://localhost:6379
STORAGE_BASE=./storage
CHUNK_DURATION_SEC=30
MODEL_WEIGHTS_PATH=./weights
LOG_LEVEL=INFO
```

### 2. Start Redis

```powershell
# Option 1 — Docker (easiest)
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Option 2 — WSL
wsl -e redis-server
```

### 3. Start PostgreSQL

```powershell
# Docker
docker run -d -p 5432:5432 --name postgres `
  -e POSTGRES_DB=rugby_highlights `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=your_password `
  postgres:15
```

### 4. Backend setup

Open a terminal in `backend/`:

```powershell
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create database tables
python create_tables.py
```

### 5. Start the API server

In the `backend/` terminal (venv active):

```powershell
$env:PYTHONPATH = "C:\path\to\rugby_highlight_system\backend"
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify: http://localhost:8000/health should return `{"status":"ok"}`

### 6. Start the Celery worker

Open a **new terminal** in `backend/`:

```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Reload PATH to pick up FFmpeg
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
$env:PYTHONPATH = "C:\path\to\rugby_highlight_system\backend"

.\venv\Scripts\python.exe -m celery -A tasks.celery_app:app worker `
  --loglevel=info -P solo -Q ml,fusion,default
```

> **Note — Windows only:** The `-P solo` flag is required on Windows. Linux/Mac/Docker use the default prefork pool.

### 7. Start the frontend

Open a **new terminal** in `frontend/`:

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173

---

## Model Weights

Place trained model weights here before processing:

```
backend/weights/visual/rugby_action_classifier.pth
```

- **Visual module** — requires `.pth` weights file
- **Commentary module** — Whisper downloads weights automatically on first run
- **Audio energy module** — no weights needed (signal processing only)

---

## Project Structure

```
rugby_highlight_system/
├── backend/
│   ├── api/              # FastAPI routes & schemas
│   ├── db/               # SQLAlchemy models & CRUD
│   ├── pipeline/         # FFmpeg extraction, segmenting, assembly
│   ├── modules/
│   │   ├── visual/       # ResNet/ViT action recognition
│   │   ├── commentary/   # Whisper ASR + NLP scoring
│   │   └── audio_energy/ # RMS energy & spectral analysis
│   ├── fusion/           # Score fusion engine
│   ├── tasks/            # Celery task definitions
│   ├── storage/          # Raw video, chunks, outputs
│   └── weights/          # Model weight files
└── frontend/
    └── src/
        ├── components/   # UI components
        ├── pages/        # Route pages
        ├── hooks/        # Polling hooks
        └── lib/          # API client
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | — |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `STORAGE_BASE` | Directory for video files | `./storage` |
| `CHUNK_DURATION_SEC` | Segment length in seconds | `30` |
| `MODEL_WEIGHTS_PATH` | Path to model weights | `./weights` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

---

## Team

| Member | Module |
|---|---|
| Thimira Deshaka | Visual Analysis (ResNet/ViT) |
| Piyushan | Commentary Analysis (Whisper/NLP) |
| Bhashini | Audio Energy (librosa) |

---

## License

Final year research project — University use only.
