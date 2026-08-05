"""
CRUD helpers — sync variants for Celery workers, async variants for FastAPI endpoints.
"""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.models import (
    FusionCell, FusionRun, HighlightClip, HighlightJob, Match,
    ModulePrediction, VisualWindowPrediction,
)


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


def sync_update_match_transcript(session: Session, match_id: str, transcript: list[dict]) -> None:
    match = session.get(Match, uuid.UUID(match_id))
    if match:
        match.transcript = transcript
        session.commit()


def sync_init_match_progress(session: Session, match_id: str) -> None:
    match = session.get(Match, uuid.UUID(match_id))
    if match:
        match.progress = {
            "visual": {"status": "pending"},
            "audio": {"status": "pending"},
            "commentary": {"status": "pending"},
        }
        session.commit()


def sync_update_match_progress(session: Session, match_id: str, module: str, **fields) -> None:
    """Merge fields into one module's progress sub-dict, preserving the
    others. Reassigns the whole dict rather than mutating in place —
    SQLAlchemy only detects JSON-column changes on attribute reassignment."""
    match = session.get(Match, uuid.UUID(match_id))
    if not match:
        return
    progress = dict(match.progress or {})
    progress[module] = {**progress.get(module, {}), **fields}
    match.progress = progress
    session.commit()


def sync_get_highlight_job(session: Session, job_id: str) -> HighlightJob | None:
    return session.get(HighlightJob, uuid.UUID(job_id))


def sync_update_highlight_job(session: Session, job_id: str, **kwargs) -> None:
    job = session.get(HighlightJob, uuid.UUID(job_id))
    if job:
        for key, value in kwargs.items():
            setattr(job, key, value)
        session.commit()


def sync_bulk_create_module_predictions(
    session: Session, match_id: str, module: str, rows: list[dict]
) -> None:
    """Bulk-insert one module's rows for a match (~hundreds per match) — a
    per-row commit here would be needlessly slow at that volume."""
    objs = [
        ModulePrediction(
            match_id=uuid.UUID(match_id),
            module=module,
            window_sec=row["window_sec"],
            index_in_module=row["index_in_module"],
            global_start_sec=row["global_start_sec"],
            global_end_sec=row["global_end_sec"],
            predicted_event=row.get("predicted_event"),
            event_confidence=row.get("event_confidence"),
            highlight_score=row["highlight_score"],
            event_probs=row.get("event_probs"),
            extra=row.get("extra"),
        )
        for row in rows
    ]
    session.bulk_save_objects(objs)
    session.commit()


def sync_bulk_create_visual_window_predictions(
    session: Session, match_id: str, rows: list[dict]
) -> None:
    """Bulk-insert the raw per-window audit rows (3x the tile count per match)."""
    objs = [
        VisualWindowPrediction(
            match_id=uuid.UUID(match_id),
            tile_index=row["tile_index"],
            window_sec=row["window_sec"],
            clip_start_sec=row["clip_start_sec"],
            clip_end_sec=row["clip_end_sec"],
            raw_event=row.get("raw_event"),
            raw_confidence=row.get("raw_confidence"),
            raw_score=row["raw_score"],
            softmax=row["softmax"],
            masked_mass=row["masked_mass"],
            dropped=row["dropped"],
            drop_reason=row.get("drop_reason"),
        )
        for row in rows
    ]
    session.bulk_save_objects(objs)
    session.commit()


def sync_get_module_predictions_by_match(
    session: Session, match_id: str, module: str | None = None
) -> list[ModulePrediction]:
    stmt = select(ModulePrediction).where(ModulePrediction.match_id == uuid.UUID(match_id))
    if module:
        stmt = stmt.where(ModulePrediction.module == module)
    stmt = stmt.order_by(ModulePrediction.global_start_sec)
    return list(session.execute(stmt).scalars())


def sync_create_fusion_run(
    session: Session,
    match_id: str,
    weights: dict,
    grid_sec: float,
    sigmoid_k: float,
    commentary_lag_sec: float,
    notes: str | None = None,
) -> FusionRun:
    """Deactivates any previously-active run for this match, then creates a
    new active one. Old runs and their cells are kept, never overwritten —
    that's what lets fusion weights be tuned without reprocessing any ML."""
    for prior in session.execute(
        select(FusionRun).where(FusionRun.match_id == uuid.UUID(match_id), FusionRun.is_active.is_(True))
    ).scalars():
        prior.is_active = False

    run = FusionRun(
        match_id=uuid.UUID(match_id),
        weights=weights,
        grid_sec=grid_sec,
        sigmoid_k=sigmoid_k,
        commentary_lag_sec=commentary_lag_sec,
        is_active=True,
        notes=notes,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def sync_bulk_create_fusion_cells(session: Session, fusion_run_id: str, match_id: str, rows: list[dict]) -> None:
    objs = [
        FusionCell(
            fusion_run_id=uuid.UUID(fusion_run_id),
            match_id=uuid.UUID(match_id),
            cell_index=row["cell_index"],
            global_start_sec=row["global_start_sec"],
            global_end_sec=row["global_end_sec"],
            fused_event=row["fused_event"],
            fused_event_confidence=row["fused_event_confidence"],
            fused_score=row["fused_score"],
            visual_tile_index=row["visual_tile_index"],
            contributions=row["contributions"],
            modules_present=row["modules_present"],
            disagreement=row["disagreement"],
            is_partial=row["is_partial"],
        )
        for row in rows
    ]
    session.bulk_save_objects(objs)
    session.commit()


def sync_get_active_fusion_run(session: Session, match_id: str) -> FusionRun | None:
    return session.execute(
        select(FusionRun).where(FusionRun.match_id == uuid.UUID(match_id), FusionRun.is_active.is_(True))
    ).scalar_one_or_none()


def sync_get_fusion_cells(session: Session, fusion_run_id: str) -> list[FusionCell]:
    stmt = (
        select(FusionCell)
        .where(FusionCell.fusion_run_id == uuid.UUID(fusion_run_id))
        .order_by(FusionCell.cell_index)
    )
    return list(session.execute(stmt).scalars())


def sync_bulk_create_highlight_clips(session: Session, job_id: str, rows: list[dict]) -> None:
    objs = [
        HighlightClip(
            job_id=uuid.UUID(job_id),
            rank=row["rank"],
            global_start_sec=row["global_start_sec"],
            global_end_sec=row["global_end_sec"],
            duration_sec=row["duration_sec"],
            event=row["event"],
            peak_score=row["peak_score"],
            mean_score=row["mean_score"],
            source_cell_start=row["source_cell_start"],
            source_cell_end=row["source_cell_end"],
            cells=row["cells"],
            was_expanded=row["was_expanded"],
            was_trimmed=row["was_trimmed"],
        )
        for row in rows
    ]
    session.bulk_save_objects(objs)
    session.commit()


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


async def async_list_matches(session: AsyncSession) -> list[Match]:
    stmt = select(Match).order_by(Match.created_at.desc())
    return list((await session.execute(stmt)).scalars())


async def async_create_highlight_job(
    session: AsyncSession,
    match_id: uuid.UUID,
    highlight_type: str,
    requested_events: list[str],
) -> HighlightJob:
    job = HighlightJob(
        match_id=match_id,
        status="pending",
        highlight_type=highlight_type,
        requested_events=requested_events,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def async_get_highlight_job(
    session: AsyncSession, job_id: uuid.UUID
) -> HighlightJob | None:
    return await session.get(HighlightJob, job_id)


async def async_delete_match(session: AsyncSession, match_id: uuid.UUID) -> list[str]:
    """Delete match and all cascaded records. Returns file paths to clean up from disk."""
    from sqlalchemy.orm import selectinload

    result = await session.execute(
        select(Match)
        .options(
            selectinload(Match.highlight_jobs).selectinload(HighlightJob.highlight_clips),
            selectinload(Match.module_predictions),
            selectinload(Match.visual_window_predictions),
            selectinload(Match.fusion_runs).selectinload(FusionRun.cells),
        )
        .where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        return []

    file_paths: list[str] = []
    for job in match.highlight_jobs:
        if job.output_path:
            file_paths.append(job.output_path)

    await session.delete(match)
    await session.commit()
    return file_paths


async def async_get_highlight_clips(session: AsyncSession, job_id: uuid.UUID) -> list[HighlightClip]:
    stmt = select(HighlightClip).where(HighlightClip.job_id == job_id).order_by(HighlightClip.rank)
    return list((await session.execute(stmt)).scalars())


async def async_get_highlight_jobs_by_match(
    session: AsyncSession, match_id: uuid.UUID
) -> list[HighlightJob]:
    stmt = (
        select(HighlightJob)
        .where(HighlightJob.match_id == match_id)
        .order_by(HighlightJob.created_at.desc())
    )
    return list((await session.execute(stmt)).scalars())


# ---------------------------------------------------------------------------
# Async CRUD — admin/inspection routes
# ---------------------------------------------------------------------------

async def async_admin_list_matches(session: AsyncSession) -> list[dict]:
    """Match list with per-module row counts and active fusion run id, for
    the admin matches table."""
    matches = list((await session.execute(
        select(Match).order_by(Match.created_at.desc())
    )).scalars())

    rows = []
    for match in matches:
        counts = {}
        for module in ("visual", "commentary", "audio"):
            counts[module] = (await session.execute(
                select(func.count()).select_from(ModulePrediction)
                .where(ModulePrediction.match_id == match.id, ModulePrediction.module == module)
            )).scalar_one()
        active_run = (await session.execute(
            select(FusionRun.id).where(FusionRun.match_id == match.id, FusionRun.is_active.is_(True))
        )).scalar_one_or_none()
        rows.append({"match": match, "module_counts": counts, "active_fusion_run_id": active_run})
    return rows


async def async_get_active_fusion_run(session: AsyncSession, match_id: uuid.UUID) -> FusionRun | None:
    return (await session.execute(
        select(FusionRun).where(FusionRun.match_id == match_id, FusionRun.is_active.is_(True))
    )).scalar_one_or_none()


async def async_get_fusion_runs_by_match(session: AsyncSession, match_id: uuid.UUID) -> list[FusionRun]:
    stmt = select(FusionRun).where(FusionRun.match_id == match_id).order_by(FusionRun.created_at.desc())
    return list((await session.execute(stmt)).scalars())


async def async_get_fusion_cells(session: AsyncSession, fusion_run_id: uuid.UUID) -> list[FusionCell]:
    stmt = (
        select(FusionCell)
        .where(FusionCell.fusion_run_id == fusion_run_id)
        .order_by(FusionCell.cell_index)
    )
    return list((await session.execute(stmt)).scalars())


async def async_delete_highlight_job(
    session: AsyncSession, job_id: uuid.UUID
) -> str | None:
    """Delete a highlight job (cascades its fusion results). Returns its output_path, if any."""
    job = await session.get(HighlightJob, job_id)
    if not job:
        return None
    output_path = job.output_path
    await session.delete(job)
    await session.commit()
    return output_path
