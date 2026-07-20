"""
Canonical taxonomy shared across the API, DB, and analysis modules.
Every module that emits or consumes an event_type must use these values
so the fusion layer's event filter can match user requests exactly.
"""
from enum import Enum


class EventType(str, Enum):
    TRY = "try"
    KICK = "kick"
    CARD = "card"
    SCRUM = "scrum"
    LINEOUT = "lineout"
    TMO_REPLAY = "tmo_replay"


EVENT_TYPE_LABELS: dict[str, str] = {
    EventType.TRY: "Try",
    EventType.KICK: "Kicks",
    EventType.CARD: "Card Event",
    EventType.SCRUM: "Scrum",
    EventType.LINEOUT: "Lineout",
    EventType.TMO_REPLAY: "TMO/Replay",
}


class HighlightType(str, Enum):
    SHORT = "short"
    EXTENDED = "extended"


# Duration budget ceilings the greedy fusion selector fills up to.
HIGHLIGHT_DURATION_BUDGET_SEC: dict[str, float] = {
    HighlightType.SHORT: 180.0,     # ~3 minutes
    HighlightType.EXTENDED: 900.0,  # 10-15 minute target range, 15 min ceiling
}
