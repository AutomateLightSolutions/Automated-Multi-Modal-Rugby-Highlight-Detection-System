"""
Admin/inspection routes: browse per-module and fused predictions for a
match, and stream its original video (Range-aware, for the timeline's
click-to-seek player). Local dev tool — no auth.
"""
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db import AsyncSessionLocal
from db.crud import (
    async_admin_list_matches,
    async_get_active_fusion_run,
    async_get_fusion_cells,
    async_get_fusion_runs_by_match,
    async_get_match,
)

router = APIRouter()

CHUNK_SIZE = 1024 * 1024  # 1MB read chunks for range streaming


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/admin/matches")
async def admin_list_matches(session: AsyncSession = Depends(get_db)):
    rows = await async_admin_list_matches(session)
    return [
        {
            "match_id": str(row["match"].id),
            "filename": row["match"].filename,
            "status": row["match"].status,
            "pipeline_version": row["match"].pipeline_version,
            "duration_sec": row["match"].duration_sec,
            "created_at": row["match"].created_at.isoformat(),
            "module_counts": row["module_counts"],
            "active_fusion_run_id": str(row["active_fusion_run_id"]) if row["active_fusion_run_id"] else None,
        }
        for row in rows
    ]


@router.get("/admin/matches/{match_id}")
async def admin_get_match(match_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    match = await async_get_match(session, match_id)
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found.")

    runs = await async_get_fusion_runs_by_match(session, match_id)
    return {
        "match_id": str(match.id),
        "filename": match.filename,
        "status": match.status,
        "pipeline_version": match.pipeline_version,
        "duration_sec": match.duration_sec,
        "fps": match.fps,
        "audio_offset_sec": match.audio_offset_sec,
        "created_at": match.created_at.isoformat(),
        "has_transcript": match.transcript is not None,
        "fusion_runs": [
            {
                "fusion_run_id": str(run.id),
                "weights": run.weights,
                "grid_sec": run.grid_sec,
                "sigmoid_k": run.sigmoid_k,
                "commentary_lag_sec": run.commentary_lag_sec,
                "is_active": run.is_active,
                "notes": run.notes,
                "created_at": run.created_at.isoformat(),
            }
            for run in runs
        ],
    }


@router.get("/admin/matches/{match_id}/timeline")
async def admin_get_timeline(
    match_id: uuid.UUID,
    fusion_run_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_db),
):
    match = await async_get_match(session, match_id)
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found.")

    if fusion_run_id:
        from db.models import FusionRun
        run = await session.get(FusionRun, fusion_run_id)
        if not run or run.match_id != match_id:
            raise HTTPException(status_code=404, detail="Fusion run not found for this match.")
    else:
        run = await async_get_active_fusion_run(session, match_id)

    if not run:
        return {"fusion_run_id": None, "cells": []}

    cells = await async_get_fusion_cells(session, run.id)
    return {
        "fusion_run_id": str(run.id),
        "cells": [
            {
                "cell_index": c.cell_index,
                "global_start_sec": c.global_start_sec,
                "global_end_sec": c.global_end_sec,
                "fused_event": c.fused_event,
                "fused_event_confidence": c.fused_event_confidence,
                "fused_score": c.fused_score,
                "visual_tile_index": c.visual_tile_index,
                "contributions": c.contributions,
                "modules_present": c.modules_present,
                "disagreement": c.disagreement,
                "is_partial": c.is_partial,
            }
            for c in cells
        ],
    }


_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


@router.get("/admin/matches/{match_id}/video")
async def admin_stream_video(match_id: uuid.UUID, request: Request, session: AsyncSession = Depends(get_db)):
    """Range-aware video streaming so the admin timeline's <video> element can seek."""
    match = await async_get_match(session, match_id)
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found.")

    video_path = Path(settings.STORAGE_BASE) / "raw" / f"{match_id}_{match.filename}"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk.")

    file_size = video_path.stat().st_size
    range_header = request.headers.get("range")

    if not range_header:
        def _full_iter():
            with open(video_path, "rb") as f:
                while chunk := f.read(CHUNK_SIZE):
                    yield chunk
        return StreamingResponse(
            _full_iter(), media_type="video/mp4",
            headers={"Content-Length": str(file_size), "Accept-Ranges": "bytes"},
        )

    match_range = _RANGE_RE.match(range_header)
    if not match_range:
        raise HTTPException(status_code=416, detail="Invalid Range header.")

    start_str, end_str = match_range.groups()
    start = int(start_str) if start_str else 0
    end = int(end_str) if end_str else file_size - 1
    end = min(end, file_size - 1)
    if start > end or start >= file_size:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})

    length = end - start + 1

    def _range_iter():
        with open(video_path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(CHUNK_SIZE, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    return StreamingResponse(
        _range_iter(),
        status_code=206,
        media_type="video/mp4",
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
        },
    )
