"""
CRUD helpers — sync variants for Celery workers, async variants for FastAPI endpoints.
"""
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.models import FusionResult, HighlightJob, Match, ModuleOutput, Segment


# ---------------------------------------------------------------------------
# Sync CRUD (Celery workers)
# ---------------------------------------------------------------------------

def sync_get_match(session: Session, match_id: str) -> Match | None:
    return session.get(Match, uuid.UUID(match_id))


def sync_update_match_status(session: Session, match_id: str, status: str, **kwargs) -> None:
    match = session.get(Match, uuid.UUID(match_id))
    if match:
        match.status = status
        for key, value in kwargs.items():
            setattr(match, key, value)
        session.commit()


def sync_create_segment(
    session: Session,
    match_id: str,
    global_start_sec: float,
    global_end_sec: float,
    video_chunk_path: str,
    audio_chunk_path: str,
) -> Segment:
    segment = Segment(
        match_id=uuid.UUID(match_id),
        global_start_sec=global_start_sec,
        global_end_sec=global_end_sec,
        video_chunk_path=video_chunk_path,
        audio_chunk_path=audio_chunk_path,
    )
    session.add(segment)
    session.commit()
    session.refresh(segment)
    return segment


def sync_create_module_output(
    session: Session,
    segment_id: str,
    module_name: str,
    confidence: float,
    event_type: str | None,
    event_confidence: float | None,
    extra_data: dict | None,
) -> ModuleOutput:
    output = ModuleOutput(
        segment_id=uuid.UUID(segment_id),
        module_name=module_name,
        confidence=confidence,
        event_type=event_type,
        event_confidence=event_confidence,
        extra_data=extra_data,
    )
    session.add(output)
    session.commit()
    session.refresh(output)
    return output


def sync_get_highlight_job(session: Session, job_id: str) -> HighlightJob | None:
    return session.get(HighlightJob, uuid.UUID(job_id))


def sync_update_highlight_job(session: Session, job_id: str, **kwargs) -> None:
    job = session.get(HighlightJob, uuid.UUID(job_id))
    if job:
        for key, value in kwargs.items():
            setattr(job, key, value)
        session.commit()


def sync_create_fusion_result(
    session: Session,
    segment_id: str,
    match_id: str,
    fused_confidence: float,
    selected: bool,
    rank: int | None,
) -> FusionResult:
    result = FusionResult(
        segment_id=uuid.UUID(segment_id),
        match_id=uuid.UUID(match_id),
        fused_confidence=fused_confidence,
        selected=selected,
        rank=rank,
    )
    session.add(result)
    session.commit()
    session.refresh(result)
    return result


# ---------------------------------------------------------------------------
# Async CRUD (FastAPI endpoints)
# ---------------------------------------------------------------------------

async def async_create_match(
    session: AsyncSession, match_id: uuid.UUID, filename: str
) -> Match:
    match = Match(id=match_id, filename=filename, status="uploaded")
    session.add(match)
    await session.commit()
    await session.refresh(match)
    return match


async def async_get_match(session: AsyncSession, match_id: uuid.UUID) -> Match | None:
    return await session.get(Match, match_id)


async def async_create_highlight_job(
    session: AsyncSession, match_id: uuid.UUID, user_filter: str | None
) -> HighlightJob:
    job = HighlightJob(match_id=match_id, status="pending", user_filter=user_filter)
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def async_get_highlight_job(
    session: AsyncSession, job_id: uuid.UUID
) -> HighlightJob | None:
    return await session.get(HighlightJob, job_id)


async def async_get_selected_fusion_results(
    session: AsyncSession, match_id: uuid.UUID
) -> list[dict]:
    """Return selected FusionResults joined with Segment and visual ModuleOutput, ordered by rank."""
    stmt = (
        select(FusionResult, Segment, ModuleOutput)
        .join(Segment, FusionResult.segment_id == Segment.id)
        .outerjoin(
            ModuleOutput,
            and_(
                ModuleOutput.segment_id == Segment.id,
                ModuleOutput.module_name == "visual",
            ),
        )
        .where(FusionResult.match_id == match_id, FusionResult.selected.is_(True))
        .order_by(FusionResult.rank)
    )
    rows = (await session.execute(stmt)).all()
    return [{"fusion": fusion, "segment": segment, "visual": visual} for fusion, segment, visual in rows]
