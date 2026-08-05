"""
Commentary excitement scorer (pipeline v2).

Scores the 4s/2s-hop analysis windows from the match's word-timestamped
transcript, then de-overlaps them onto the 4s master fusion grid — same
window/grid scheme as the audio energy module (modules/grid.py).

Per cell:
    highlight_score  = overlap-weighted mean of window excitement scores
    predicted_event  = argmax of the overlap-weighted, confidence-scaled
                        vote over EVENT_CLASSES
    event_confidence = that argmax's weighted vote value

A window with no event-mapped keyword votes for "normal_play" — the
catch-all class — rather than contributing nothing, so cells near a real
event only compete against their immediate 2 overlapping neighbours, not
the whole match.
"""
import math
import logging

import numpy as np

from constants import EVENT_CLASSES
from modules.commentary.asr import transcribe_match
from modules.grid import compute_analysis_windows, compute_grid_cells, deoverlap_weighted_average

logger = logging.getLogger(__name__)

_CLASS_INDEX = {name: i for i, name in enumerate(EVENT_CLASSES)}

# word -> (excitement weight, canonical EVENT_CLASSES member | None).
# Remapped from the legacy 6-class lexicon onto the SlowFast 10-class
# taxonomy (constants.EVENT_CLASSES). Words with event_type=None still
# contribute to highlight_score but never decide predicted_event — same
# distinction the legacy scorer made.
RUGBY_KEYWORDS: dict[str, tuple[float, str | None]] = {
    "try": (1.0, "try"),
    "conversion": (0.70, "goal_kick"),
    "penalty": (0.80, "penalty"),
    "offside": (0.60, "penalty"),
    "scrum": (0.85, "scrum"),
    "maul": (0.70, "maul"),
    "lineout": (0.75, "lineout"),
    "restart": (0.55, "kick_off"),
    "kickoff": (0.60, "kick_off"),
    "yellow": (0.85, "card_event"),
    "red": (0.90, "card_event"),
    "card": (0.80, "card_event"),
    "sinbin": (0.80, "card_event"),
    "tmo": (0.55, "tmo_replay"),
    "replay": (0.50, "tmo_replay"),
    "review": (0.50, "tmo_replay"),
    "referral": (0.50, "tmo_replay"),
    # Excitement-only — no canonical event class.
    "kick": (0.65, None),
    "offload": (0.65, None),
    "tackle": (0.60, None),
    "breakdown": (0.55, None),
    "ruck": (0.55, None),
    "grubber": (0.50, None),
    "incredible": (0.50, None),
    "brilliant": (0.45, None),
    "danger": (0.40, None),
    "whistle": (0.35, None),
    "referee": (0.30, None),
}


def _sigmoid_normalize(raw_score: float) -> float:
    """Map raw keyword score to [0, 1] via sigmoid."""
    return 1.0 / (1.0 + math.exp(-3.0 * (raw_score - 0.5)))


def _score_window(words_in_window: list[dict]) -> dict:
    """
    Args:
        words_in_window: words (from transcribe_match) whose timestamp falls
            inside this analysis window.

    Returns:
        {"highlight_score": float, "predicted_event": str, "event_weight": float}
        predicted_event always has a value — defaults to "normal_play" when
        no event-mapped keyword is present.
    """
    raw_score = 0.0
    best_event = None
    best_event_weight = 0.0

    for word_data in words_in_window:
        word = word_data["word"].strip(".,!?")
        if word in RUGBY_KEYWORDS:
            weight, event_type = RUGBY_KEYWORDS[word]
            raw_score += weight
            if event_type is not None and weight > best_event_weight:
                best_event_weight = weight
                best_event = event_type

    raw_score_norm = min(raw_score, 2.0) / 2.0
    highlight_score = _sigmoid_normalize(raw_score_norm)

    if best_event is None:
        return {"highlight_score": highlight_score, "predicted_event": "normal_play", "event_weight": 1.0}
    return {"highlight_score": highlight_score, "predicted_event": best_event, "event_weight": best_event_weight}


def analyze_match(audio_path: str, duration_sec: float, lag_sec: float = 0.0) -> dict:
    """
    Run the full windowed commentary analysis over one match's audio track.

    Args:
        lag_sec: shift word timestamps earlier by this much before gridding
            (commentators react after the play). Default 0.0 — see
            config.settings.COMMENTARY_LAG_SEC.

    Returns:
        {"cells": [{cell_index, global_start_sec, global_end_sec,
                    predicted_event, event_confidence, highlight_score,
                    extra}, ...],
         "transcript": [word dicts, absolute match time]}
    """
    words = transcribe_match(audio_path)
    if lag_sec:
        words = [
            {**w, "start": max(0.0, w["start"] - lag_sec), "end": max(0.0, w["end"] - lag_sec)}
            for w in words
        ]

    windows = compute_analysis_windows(duration_sec)
    grid_cells = compute_grid_cells(duration_sec)

    window_scores: dict[int, float] = {}
    window_votes: dict[int, np.ndarray] = {}
    for idx, (w_start, w_end) in enumerate(windows):
        words_in_window = [w for w in words if w_start <= w["start"] < w_end]
        scored = _score_window(words_in_window)

        window_scores[idx] = scored["highlight_score"]
        vote = np.zeros(len(EVENT_CLASSES))
        vote[_CLASS_INDEX[scored["predicted_event"]]] = scored["event_weight"]
        window_votes[idx] = vote

    n_cells = len(grid_cells)
    cell_scores = deoverlap_weighted_average(window_scores, n_cells)
    cell_votes = deoverlap_weighted_average(window_votes, n_cells)

    cells = []
    for j, grid_cell in enumerate(grid_cells):
        vote = cell_votes[j] if cell_votes[j] is not None else np.zeros(len(EVENT_CLASSES))
        best_idx = int(np.argmax(vote))
        score = cell_scores[j] if cell_scores[j] is not None else 0.0

        cells.append({
            "cell_index": j,
            "global_start_sec": grid_cell["start_sec"],
            "global_end_sec": grid_cell["end_sec"],
            "predicted_event": EVENT_CLASSES[best_idx],
            "event_confidence": round(float(vote[best_idx]), 4),
            "highlight_score": round(float(score), 4),
            "extra": {"is_partial": grid_cell["is_partial"]},
        })

    logger.info("Commentary analysis: %d words, %d windows, %d cells", len(words), len(windows), n_cells)
    return {"cells": cells, "transcript": words}
