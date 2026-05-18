"""
FastAPI application entry point.
Registers all routers and configures middleware.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import highlights, upload

app = FastAPI(
    title="Rugby Highlight Generator",
    description="Automatic rugby match highlight generation using multimodal AI.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(highlights.router, prefix="/api/v1", tags=["highlights"])


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "service": "rugby-highlight-generator"}


@app.on_event("startup")
async def startup():
    from db import async_engine
    from db.models import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
