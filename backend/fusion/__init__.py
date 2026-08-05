"""
Highlight generation entry point (pipeline v2). Called by the
generate_highlight Celery task.

Fusion itself (module_predictions -> fusion_cells) already ran automatically
when match processing finished (tasks.fuse_match, fusion/grid_fusion.py).
This just reads the match's active fusion_run and turns its cells into a
ranked, budget-filled set of highlight clips.
"""
import logging

from constants import PROFILES, HighlightType
from db.crud import sync_get_active_fusion_run, sync_get_fusion_cells
from fusion.highlight_selector import select_highlight_clips

logger = logging.getLogger(__name__)


def generate_highlight_clips(match_id: str, requested_events: list[str],
                              highlight_type: str, duration_sec: float, session) -> dict:
    """
    Returns:
        {"fusion_run_id": str | None, "clips": list[dict]}
        clips is empty if there's no active fusion_run yet (match still
        processing) or no candidates survived selection.
    """
    fusion_run = sync_get_active_fusion_run(session, match_id)
    if fusion_run is None:
        logger.error("No active fusion_run for match %s — has processing finished?", match_id)
        return {"fusion_run_id": None, "clips": []}

    cell_rows = sync_get_fusion_cells(session, str(fusion_run.id))
    cells = [
        {
            "cell_index": row.cell_index,
            "fused_event": row.fused_event,
            "fused_score": row.fused_score,
            "global_start_sec": row.global_start_sec,
            "global_end_sec": row.global_end_sec,
        }
        for row in cell_rows
    ]

    profile = PROFILES[HighlightType(highlight_type)]
    clips = select_highlight_clips(cells, profile, requested_events, duration_sec)

    return {"fusion_run_id": str(fusion_run.id), "clips": clips}
