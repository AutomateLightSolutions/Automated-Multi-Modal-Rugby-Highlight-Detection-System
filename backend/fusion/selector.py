"""
Selects the best highlight segments using Non-Maximum Suppression.
Outputs segments in chronological order for final video assembly.
"""

import logging

logger = logging.getLogger(__name__)


def select_segments(fused_scores: list[dict],
                     top_n: int = 10,
                     min_gap_sec: float = 5.0) -> list[dict]:
    """
    Select top highlight segments with NMS to avoid redundancy.

    Args:
        fused_scores: list of dicts, each with:
            segment_id, global_start_sec, global_end_sec,
            fused_confidence, visual_event_type, visual_event_confidence
        top_n: maximum number of segments to select
        min_gap_sec: minimum gap between selected segments

    Returns:
        Selected segments sorted chronologically (by global_start_sec),
        with "rank" field added (1 = highest confidence).
    """
    if not fused_scores:
        return []

    # Sort by confidence descending
    sorted_segments = sorted(
        fused_scores,
        key=lambda s: s["fused_confidence"],
        reverse=True
    )

    selected = []
    for candidate in sorted_segments:
        if len(selected) >= top_n:
            break

        candidate_start = candidate["global_start_sec"]
        candidate_end = candidate["global_end_sec"]

        # Check against all already-selected segments
        too_close = False
        for accepted in selected:
            accepted_start = accepted["global_start_sec"]
            accepted_end = accepted["global_end_sec"]

            # Overlap check with gap tolerance
            gap = max(
                candidate_start - accepted_end,
                accepted_start - candidate_end
            )
            if gap < min_gap_sec:
                too_close = True
                break

        if not too_close:
            selected.append(candidate)

    # Assign confidence rank before resorting
    for rank, seg in enumerate(selected, start=1):
        seg["rank"] = rank

    # Re-sort chronologically for video assembly
    selected.sort(key=lambda s: s["global_start_sec"])

    logger.info(
        "NMS selection: %d candidates → %d selected (top_n=%d, min_gap=%.1fs)",
        len(fused_scores), len(selected), top_n, min_gap_sec
    )
    return selected
