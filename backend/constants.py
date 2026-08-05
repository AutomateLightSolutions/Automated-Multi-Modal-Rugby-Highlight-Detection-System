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
# Clip lengths are multiples of FUSION_GRID_SEC (4s) — min_clip_sec is rounded
# to the nearest 4s boundary that stays >= the requested minimum (short
# requested 15s -> 16s; extended 40s -> 40s exact).
#
# max_clip_sec is kept as recorded metadata (surfaced in job params) but is
# NOT the active trim threshold — see CLIP_SAFETY_CEILING_SEC below. Clips
# are no longer force-trimmed to max_clip_sec: cutting a natural run there
# was slicing through ongoing action. Runs now keep their natural length up
# to the safety ceiling; the reel's total duration flexes between
# budget_sec (target) and budget_max_sec (ceiling) to absorb the difference
# instead of arbitrarily cutting or dropping whole clips.
PROFILES: dict[str, dict] = {
    HighlightType.SHORT: {
        "budget_sec": 180.0, "budget_max_sec": 300.0,
        "min_clip_sec": 16.0, "max_clip_sec": 44.0,
    },
    HighlightType.EXTENDED: {
        "budget_sec": 720.0, "budget_max_sec": 900.0,
        "min_clip_sec": 40.0, "max_clip_sec": 88.0,
    },
}

# Absolute per-clip safety valve — a run longer than this (a very long
# unbroken stretch of one identical event label) gets trimmed to its
# best-scoring window of this length. Runs shorter than this pass through
# at their natural length, uncut.
CLIP_SAFETY_CEILING_SEC = 90.0

MIN_GAP_SEC = 4.0        # minimum gap between selected clips
MIN_CELL_SCORE = 0.35    # candidate cell floor
BRIDGE_CELLS = 1         # allowed one-cell gap inside an event run
