"""
Filter 2 (score-based selection within time budget): rank remaining clips
by combined score descending, then greedily fill a duration budget —
skipping (not breaking on) clips that would overflow it, since a later,
shorter clip may still fit. NMS gap-checking avoids near-duplicate picks.
Outputs segments in chronological order for final video assembly.
"""

import logging

logger = logging.getLogger(__name__)


def select_segments(fused_scores: list[dict],
                     duration_budget_sec: float,
                     min_gap_sec: float = 5.0) -> list[dict]:
    """
    Greedily select highlight segments up to a duration budget.

    Args:
        fused_scores: list of dicts, each with:
            segment_id, global_start_sec, global_end_sec,
            fused_confidence, visual_event_type, visual_event_confidence
        duration_budget_sec: cumulative duration ceiling (from highlight_type)
        min_gap_sec: minimum gap between selected segments (NMS-style)

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
    running_duration = 0.0
    for candidate in sorted_segments:
        candidate_start = candidate["global_start_sec"]
        candidate_end = candidate["global_end_sec"]
        candidate_duration = candidate_end - candidate_start

        # Check against all already-selected segments
        too_close = any(
            max(candidate_start - a["global_end_sec"], a["global_start_sec"] - candidate_end) < min_gap_sec
            for a in selected
        )
        if too_close:
            continue

        # Skip (don't stop) clips that would overflow the budget —
        # a later, shorter clip may still fit.
        if running_duration + candidate_duration > duration_budget_sec:
            continue

        selected.append(candidate)
        running_duration += candidate_duration

    # Assign confidence rank before resorting
    for rank, seg in enumerate(selected, start=1):
        seg["rank"] = rank

    # Re-sort chronologically for video assembly
    selected.sort(key=lambda s: s["global_start_sec"])

    logger.info(
        "Budget selection: %d candidates → %d selected (%.1fs / %.1fs budget, min_gap=%.1fs)",
        len(fused_scores), len(selected), running_duration, duration_budget_sec, min_gap_sec
    )
    return selected
