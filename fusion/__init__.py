"""
Master fusion pipeline. Called by the generate_highlight Celery task.
Loads all module outputs from DB, aligns, scores, filters, selects.
"""

import logging
from fusion.aligner import align_module_outputs
from fusion.scorer import compute_fused_score
from fusion.filter import apply_user_filter
from fusion.selector import select_segments
from db.crud import (
    sync_get_segments_by_match,
    sync_get_module_outputs_by_segment,
    sync_create_fusion_result,
    sync_update_fusion_result,
)

logger = logging.getLogger(__name__)


def run_fusion_pipeline(match_id: str, user_filter: str | None,
                         session) -> list[dict]:
    """
    Full fusion pipeline for one match.

    Returns:
        List of selected segment dicts sorted chronologically.
        Each dict contains all fields needed by assembler.py.
    """
    segments = sync_get_segments_by_match(session, match_id)
    if not segments:
        logger.error("No segments found for match %s", match_id)
        return []

    all_fused = []

    for segment in segments:
        module_outputs_db = sync_get_module_outputs_by_segment(
            session, str(segment.id)
        )

        if not module_outputs_db:
            logger.warning("Segment %s has no module outputs. Skipping.", segment.id)
            continue

        # Convert DB objects to dicts matching module contract
        output_dicts = [
            {
                "module": mo.module_name,
                "global_start_sec": segment.global_start_sec,
                "global_end_sec": segment.global_end_sec,
                "confidence": mo.confidence,
                "event_type": mo.event_type,
                "event_confidence": mo.event_confidence,
            }
            for mo in module_outputs_db
        ]

        # Align and validate timestamps
        try:
            aligned = align_module_outputs(str(segment.id), output_dicts)
        except ValueError:
            logger.exception("Alignment failed for segment %s", segment.id)
            continue

        # Compute fused score
        fused_score = compute_fused_score(aligned)

        # Persist fusion result (not yet selected; rank assigned after NMS)
        sync_create_fusion_result(
            session,
            segment_id=str(segment.id),
            match_id=match_id,
            fused_confidence=fused_score,
            selected=False,
            rank=None,
        )

        # Get visual event data for filtering and downstream use
        visual_out = aligned.get("visual", {})

        all_fused.append({
            "segment_id": str(segment.id),
            "global_start_sec": segment.global_start_sec,
            "global_end_sec": segment.global_end_sec,
            "video_chunk_path": segment.video_chunk_path,
            "fused_confidence": fused_score,
            "visual_event_type": visual_out.get("event_type"),
            "visual_event_confidence": visual_out.get("event_confidence"),
        })

    # Apply user filter
    filtered = apply_user_filter(all_fused, user_filter)

    # NMS selection
    selected = select_segments(filtered, top_n=10, min_gap_sec=5.0)

    # Mark selected segments in DB with their rank
    for seg in selected:
        sync_update_fusion_result(
            session,
            seg["segment_id"],
            selected=True,
            rank=seg["rank"],
        )

    return selected
