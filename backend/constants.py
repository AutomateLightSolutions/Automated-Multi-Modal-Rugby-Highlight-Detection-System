"""
Canonical taxonomy shared across the API, DB, and analysis modules.
Every module that emits or consumes an event_type must use these values
so the fusion layer's event filter can match user requests exactly.
"""
from enum import Enum


class EventClass(str, Enum):
    """Canonical pipeline-v2 event vocabulary (SlowFast visual classifier).
    Declaration order matters: it must match the checkpoint's class_logits
    index order exactly. Independently confirmed against the training run's
    metrics.json per_class_f1 key order. Used for API request validation;
    EVENT_CLASSES (below) is the same values as an ordered list, used for
    indexing into class_logits/softmax vectors."""
    TRY = "try"
    GOAL_KICK = "goal_kick"
    CARD_EVENT = "card_event"
    PENALTY = "penalty"
    SCRUM = "scrum"
    MAUL = "maul"
    LINEOUT = "lineout"
    KICK_OFF = "kick_off"
    TMO_REPLAY = "tmo_replay"
    NORMAL_PLAY = "normal_play"


EVENT_CLASSES: list[str] = [e.value for e in EventClass]

EVENT_CLASS_LABELS: dict[str, str] = {
    EventClass.TRY: "Try",
    EventClass.GOAL_KICK: "Goal Kick",
    EventClass.CARD_EVENT: "Card Event",
    EventClass.PENALTY: "Penalty",
    EventClass.SCRUM: "Scrum",
    EventClass.MAUL: "Maul",
    EventClass.LINEOUT: "Lineout",
    EventClass.KICK_OFF: "Kick Off",
    EventClass.TMO_REPLAY: "TMO/Replay",
    EventClass.NORMAL_PLAY: "Normal Play",
}

# Visual tiling (pipeline v2): non-overlapping tile size + context window sizes.
TILE_SEC = 8
CONTEXT_WINDOWS_SEC = (8, 16, 32)

# Audio/commentary windowing (pipeline v2): overlapping analysis windows,
# de-overlapped onto the non-overlapping master fusion grid.
AUDIO_WINDOW_SEC = 4
AUDIO_HOP_SEC = 2
FUSION_GRID_SEC = 4


class HighlightType(str, Enum):
    SHORT = "short"
    EXTENDED = "extended"


# Highlight generation rules (pipeline v2), keyed by HighlightType.
# Clip lengths are multiples of FUSION_GRID_SEC (4s) — min/max are rounded to
# the nearest 4s boundary that stays INSIDE the requested [min, max] range
# (min rounds up, max rounds down), so generated clips never fall outside
# the intended bounds: short requested 15-45s -> 16-44s; extended requested
# 40-90s -> 40-88s.
PROFILES: dict[str, dict] = {
    HighlightType.SHORT: {"budget_sec": 180.0, "min_clip_sec": 16.0, "max_clip_sec": 44.0},
    HighlightType.EXTENDED: {"budget_sec": 720.0, "min_clip_sec": 40.0, "max_clip_sec": 88.0},
}

MIN_GAP_SEC = 4.0        # minimum gap between selected clips
MIN_CELL_SCORE = 0.35    # candidate cell floor
BRIDGE_CELLS = 1         # allowed one-cell gap inside an event run
