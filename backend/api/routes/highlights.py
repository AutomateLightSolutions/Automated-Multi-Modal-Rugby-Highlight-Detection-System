"""
Highlights routes: generate highlights, poll status, and download the output video.
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    HighlightJobRequest,
    HighlightJobResponse,
    HighlightJobSummary,
    JobStatusResponse,
    SegmentResult,
)
from db import AsyncSessionLocal
from db.crud import (
    async_create_highlight_job,
    async_delete_highlight_job,
    async_get_highlight_job,
    async_get_highlight_jobs_by_match,
    async_get_match,
    async_get_selected_fusion_results,
)

router = APIRouter()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/highlights/generate", response_model=HighlightJobResponse)
async def generate_highlights(
    body: HighlightJobRequest,
    session: AsyncSession = Depends(get_db),
):
    match = await async_get_match(session, body.match_id)
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {body.match_id} not found.")
    if match.status != "done":
        raise HTTPException(
            status_code=400,
            detail="Match is still processing. Wait for status=done before generating highlights.",
        )

    highlight_type = body.highlight_type.value
    requested_events = [e.value for e in body.requested_events]

    job = await async_create_highlight_job(
        session, body.match_id, highlight_type, requested_events
    )

    from tasks.tasks import generate_highlight
    generate_highlight.delay(str(job.id), str(body.match_id), highlight_type, requested_events)

    return HighlightJobResponse(
        job_id=job.id,
        match_id=body.match_id,
        status=job.status,
    )


@router.get("/highlights/status/{job_id}", response_model=JobStatusResponse)
async def get_highlight_status(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    job = await async_get_highlight_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Highlight job {job_id} not found.")

    segments = None
    if job.status == "done":
        rows = await async_get_selected_fusion_results(session, job.id)
        segments = [
            SegmentResult(
                segment_id=row["fusion"].segment_id,
                global_start_sec=row["segment"].global_start_sec,
                global_end_sec=row["segment"].global_end_sec,
                fused_confidence=row["fusion"].fused_confidence,
                selected=row["fusion"].selected,
                rank=row["fusion"].rank,
                event_type=row["visual"].event_type if row["visual"] else None,
                event_confidence=row["visual"].event_confidence if row["visual"] else None,
            )
            for row in rows
        ]

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        highlight_type=job.highlight_type,
        requested_events=job.requested_events,
        output_path=job.output_path,
        error_message=job.error_message,
        segments=segments,
    )


@router.get("/matches/{match_id}/highlights", response_model=list[HighlightJobSummary])
async def list_match_highlights(
    match_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    jobs = await async_get_highlight_jobs_by_match(session, match_id)
    return [
        HighlightJobSummary(
            job_id=job.id,
            status=job.status,
            highlight_type=job.highlight_type,
            requested_events=job.requested_events,
            output_path=job.output_path,
            error_message=job.error_message,
            created_at=job.created_at,
        )
        for job in jobs
    ]


@router.delete("/highlights/{job_id}", status_code=200)
async def delete_highlight(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    job = await async_get_highlight_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Highlight job {job_id} not found.")

    output_path = await async_delete_highlight_job(session, job_id)
    if output_path:
        try:
            Path(output_path).unlink(missing_ok=True)
        except OSError:
            pass

    return {"deleted": True, "job_id": str(job_id)}


@router.get("/highlights/download/{job_id}")
async def download_highlight(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    job = await async_get_highlight_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Highlight job {job_id} not found.")
    if job.status != "done":
        raise HTTPException(status_code=400, detail="Highlight not ready yet.")
    if not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(status_code=404, detail="Highlight file not found on disk.")
    return FileResponse(
        job.output_path,
        media_type="video/mp4",
        filename=f"highlight_{job_id}.mp4",
    )
