"""
Applies optional user-requested event filter to segment list.
e.g. "scrums only" → keep only segments where visual module
detected a scrum with event_confidence >= MIN_EVENT_CONFIDENCE.
"""

import logging

logger = logging.getLogger(__name__)

MIN_EVENT_CONFIDENCE = 0.50  # minimum event_confidence to trust detection

# Map user filter keywords to event_type labels
FILTER_KEYWORD_MAP = {
    "scrum": "scrum",
    "scrums": "scrum",
    "try": "try",
    "tries": "try",
    "lineout": "lineout",
    "lineouts": "lineout",
    "penalty": "penalty",
    "penalties": "penalty",
    "conversion": "conversion",
    "conversions": "conversion",
    "tackle": "tackle",
    "tackles": "tackle",
    "kick": "kick",
    "kicks": "kick",
    "breakdown": "breakdown",
    "ruck": "ruck",
}


def apply_user_filter(segments: list[dict],
                       user_filter: str | None) -> list[dict]:
    """
    Filter segments by user-requested event type.

    Each segment dict must contain:
        "visual_event_type": str | None
        "visual_event_confidence": float | None

    Falls back to all segments if filter produces empty result.
    Returns all segments if user_filter is None.
    """
    if user_filter is None:
        return segments

    # Parse filter string — find first matching keyword
    filter_lower = user_filter.lower()
    target_event = None
    for keyword, event_label in FILTER_KEYWORD_MAP.items():
        if keyword in filter_lower:
            target_event = event_label
            break

    if target_event is None:
        logger.warning(
            "User filter '%s' did not match any known event type. "
            "Known types: %s. Returning all segments.",
            user_filter, list(set(FILTER_KEYWORD_MAP.values()))
        )
        return segments

    filtered = [
        seg for seg in segments
        if seg.get("visual_event_type") == target_event
        and (
            seg.get("visual_event_confidence") is None
            or seg.get("visual_event_confidence") >= MIN_EVENT_CONFIDENCE
        )
    ]

    if not filtered:
        logger.warning(
            "Filter '%s' → '%s' produced 0 results. "
            "Falling back to all %d segments.",
            user_filter, target_event, len(segments)
        )
        return segments

    logger.info(
        "Filter '%s': %d/%d segments kept.",
        target_event, len(filtered), len(segments)
    )
    return filtered
