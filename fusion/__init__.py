"""
Fusion pipeline: aligns module scores, computes fused confidence, filters,
selects top segments, persists FusionResult records, and returns selected Segments.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import FusionResult, ModuleOutput, Segment


_WEIGHTS = {"visual": 0.5, "commentary": 0.3, "audio_energy": 0.2}
_CONFIDENCE_THRESHOLD = 0.4
_MAX_SEGMENTS = 20


def _matches_filter(event_type: str | None, user_filter: str | None) -> bool:
    if not user_filter or not event_type:
        return True
    keyword = user_filter.lower().rstrip("s")  # "scrums" → "scrum"
    return keyword in event_type.lower()


def _fuse_outputs(outputs: list[ModuleOutput], user_filter: str | None) -> float:
    """Weighted mean confidence; returns -1 if the segment fails the user filter."""
    total_weight = 0.0
    fused = 0.0
    for output in outputs:
        if not _matches_filter(output.event_type, user_filter):
            return -1.0
        w = _WEIGHTS.get(output.module_name, 0.0)
        fused += w * output.confidence
        total_weight += w
    return fused / total_weight if total_weight > 0 else -1.0


def _load_outputs(session: Session, segment_id: uuid.UUID) -> list[ModuleOutput]:
    return list(
        session.execute(
            select(ModuleOutput).where(ModuleOutput.segment_id == segment_id)
        ).scalars()
    )


def _persist_results(
    session: Session,
    match_uuid: uuid.UUID,
    top: list[tuple[float, Segment]],
) -> None:
    for rank, (fused_confidence, segment) in enumerate(top):
        session.add(
            FusionResult(
                segment_id=segment.id,
                match_id=match_uuid,
                fused_confidence=fused_confidence,
                selected=True,
                rank=rank,
            )
        )
    session.commit()


def run_fusion_pipeline(
    match_id: str,
    user_filter: str | None,
    session: Session,
) -> list:
    """
    Runs weighted fusion over all module outputs for the match, selects the
    top-scoring segments, persists FusionResult rows, and returns the ordered
    list of selected Segment objects (chronological order).
    """
    match_uuid = uuid.UUID(match_id) if isinstance(match_id, str) else match_id

    segments: list[Segment] = list(
        session.execute(select(Segment).where(Segment.match_id == match_uuid)).scalars()
    )
    if not segments:
        return []

    scored: list[tuple[float, Segment]] = []
    for segment in segments:
        fused = _fuse_outputs(_load_outputs(session, segment.id), user_filter)
        if fused >= _CONFIDENCE_THRESHOLD:
            scored.append((fused, segment))

    top = sorted(scored, key=lambda x: x[0], reverse=True)[:_MAX_SEGMENTS]
    _persist_results(session, match_uuid, top)

    return [seg for _, seg in sorted(top, key=lambda x: x[1].global_start_sec)]
