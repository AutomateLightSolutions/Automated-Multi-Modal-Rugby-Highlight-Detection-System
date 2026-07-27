"""
Filter 1 (event selection by user request): keep only segments whose
detected event class is one of the user's requested_events. No fallback —
a clip that doesn't match a requested type is discarded, per spec.
"""

import logging

logger = logging.getLogger(__name__)

MIN_EVENT_CONFIDENCE = 0.50  # minimum event_confidence to trust detection


def filter_by_requested_events(
    segments: list[dict], requested_events: list[str]
) -> list[dict]:
    """
    Filter segments to only those whose visual_event_type is in requested_events.

    Each segment dict must contain:
        "visual_event_type": str | None
        "visual_event_confidence": float | None
    """
    wanted = set(requested_events)

    filtered = [
        seg for seg in segments
        if seg.get("visual_event_type") in wanted
        and (
            seg.get("visual_event_confidence") is None
            or seg.get("visual_event_confidence") >= MIN_EVENT_CONFIDENCE
        )
    ]

    logger.info(
        "Event filter %s: %d/%d segments kept.",
        sorted(wanted), len(filtered), len(segments)
    )
    return filtered
