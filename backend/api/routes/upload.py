"""
Upload route: accepts a video file and enqueues a processing task.
"""
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import MatchStatusResponse, MatchUploadResponse
from config import settings
from db import AsyncSessionLocal
from db.crud import async_create_match, async_delete_match, async_get_match

router = APIRouter()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/upload", response_model=MatchUploadResponse)
async def upload_match(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):
    if not file.filename or Path(file.filename).suffix.lower() not in {".mp4", ".mov"}:
        raise HTTPException(status_code=400, detail="Only .mp4 and .mov files are supported.")

    match_id = uuid.uuid4()

    raw_dir = settings.STORAGE_BASE / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    saved_path = raw_dir / f"{match_id}_{file.filename}"

    total_bytes = 0
    async with aiofiles.open(saved_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):  # stream in 1 MB chunks
            total_bytes += len(chunk)
            await out.write(chunk)

    if total_bytes == 0:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    await async_create_match(session, match_id, file.filename)

    # Import here to avoid a circular import at module load time
    from tasks.tasks import process_match
    process_match.delay(str(match_id), str(saved_path))

    return MatchUploadResponse(
        match_id=match_id,
        filename=file.filename,
        status="uploaded",
        message=(
            f"Match accepted and queued for processing. "
            f"Poll /api/v1/matches/{match_id}/status to track progress."
        ),
    )


@router.delete("/matches/{match_id}", status_code=200)
async def delete_match(
    match_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    match = await async_get_match(session, match_id)
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found.")

    if match.status in ("extracting", "processing"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete a match that is currently {match.status}. "
                   "Wait for it to complete or fail first.",
        )

    filename = match.filename

    file_paths = await async_delete_match(session, match_id)

    # Raw video and full audio are not stored in segment records — reconstruct paths
    file_paths += [
        str(settings.STORAGE_BASE / "raw" / f"{match_id}_{filename}"),
        str(settings.STORAGE_BASE / "audio" / f"{match_id}_full.wav"),
    ]

    for path_str in file_paths:
        try:
            Path(path_str).unlink(missing_ok=True)
        except OSError:
            pass  # best-effort; don't fail the request over a missing file

    return {"deleted": True, "match_id": str(match_id)}


@router.get("/matches/{match_id}/status", response_model=MatchStatusResponse)
async def get_match_status(
    match_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    match = await async_get_match(session, match_id)
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found.")
    return MatchStatusResponse(
        match_id=match.id,
        filename=match.filename,
        status=match.status,
        duration_sec=match.duration_sec,
        fps=match.fps,
        created_at=match.created_at,
    )
