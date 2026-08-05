"""
Per-tile merge: 3 window-size predictions (8s/16s/32s) -> 1 (event, score).

Score merge is a fixed-weight average favouring the finest window.
Class merge is a class-support-masked weighted vote: each window size only
has real training signal for a subset of event classes (see CLASS_SUPPORT),
so a window is prevented from voting for a class it was never trained to
recognise at that clip length.
"""
import numpy as np

from constants import EVENT_CLASSES

SCORE_WEIGHTS: dict[int, float] = {8: 0.6, 16: 0.3, 32: 0.1}

# Per-window-size event classes with real training support, from this
# project's labeled training data. Hardcoded starting point — recompute if
# the underlying label set changes significantly.
CLASS_SUPPORT: dict[int, set[str]] = {
    8: {"card_event", "goal_kick", "kick_off", "lineout", "maul",
        "normal_play", "penalty", "try", "scrum", "tmo_replay"},
    16: {"goal_kick", "normal_play", "scrum", "tmo_replay", "try"},
    32: {"goal_kick", "normal_play", "tmo_replay", "try"},
}

# Masked probability mass below this is treated as "no signal" -> drop the window.
MASKED_MASS_EPS = 1e-6

_CLASS_INDEX = {name: i for i, name in enumerate(EVENT_CLASSES)}


def merge_tile(window_predictions: dict[int, dict]) -> dict:
    """
    Args:
        window_predictions: {window_sec: {"softmax": Sequence[float] (10,), "score": float}}
            for whichever of SCORE_WEIGHTS' window sizes actually ran.

    Returns:
        {
            "merged_score": float,
            "predicted_event": str,
            "event_confidence": float,
            "event_probs": list[float] (10-dim, the vector argmax was taken over),
            "fallback_used": bool,
            "windows_dropped": list[int],
            "window_audit": {window_sec: {"masked_mass": float, "dropped": bool}},
                # source of truth for the visual_window_prediction audit rows —
                # callers should not recompute masking themselves.
        }
    """
    merged_score = _merge_score(window_predictions)

    surviving: dict[int, np.ndarray] = {}
    windows_dropped: list[int] = []
    window_audit: dict[int, dict] = {}
    for window_sec in SCORE_WEIGHTS:
        pred = window_predictions.get(window_sec)
        if pred is None:
            continue
        masked, mass = _mask_probs(np.asarray(pred["softmax"], dtype=float), window_sec)
        dropped = mass < MASKED_MASS_EPS
        window_audit[window_sec] = {"masked_mass": round(mass, 6), "dropped": dropped}
        if dropped:
            windows_dropped.append(window_sec)
            continue
        surviving[window_sec] = masked / mass

    fallback_used = not surviving
    combined = (
        _weighted_average(surviving)
        if surviving
        else _fallback_raw_average(window_predictions)
    )

    best_idx = int(np.argmax(combined))
    return {
        "merged_score": round(float(merged_score), 4),
        "predicted_event": EVENT_CLASSES[best_idx],
        "event_confidence": round(float(combined[best_idx]), 4),
        "event_probs": [round(float(x), 6) for x in combined],
        "fallback_used": fallback_used,
        "windows_dropped": windows_dropped,
        "window_audit": window_audit,
    }


def _merge_score(window_predictions: dict[int, dict]) -> float:
    num = 0.0
    den = 0.0
    for window_sec, weight in SCORE_WEIGHTS.items():
        pred = window_predictions.get(window_sec)
        if pred is None:
            continue
        num += weight * pred["score"]
        den += weight
    return num / den if den > 0 else 0.0


def _mask_probs(probs: np.ndarray, window_sec: int) -> tuple[np.ndarray, float]:
    support = CLASS_SUPPORT.get(window_sec, set(EVENT_CLASSES))
    mask = np.array([1.0 if cls in support else 0.0 for cls in EVENT_CLASSES])
    masked = probs * mask
    return masked, float(masked.sum())


def _weighted_average(surviving: dict[int, np.ndarray]) -> np.ndarray:
    num = np.zeros(len(EVENT_CLASSES))
    den = 0.0
    for window_sec, renorm_probs in surviving.items():
        weight = SCORE_WEIGHTS[window_sec]
        num += weight * renorm_probs
        den += weight
    return num / den if den > 0 else num


def _fallback_raw_average(window_predictions: dict[int, dict]) -> np.ndarray:
    """All windows got masked to ~0 mass — average the raw unmasked softmaxes
    instead, so the tile still gets a label rather than being dropped."""
    num = np.zeros(len(EVENT_CLASSES))
    den = 0.0
    for window_sec, weight in SCORE_WEIGHTS.items():
        pred = window_predictions.get(window_sec)
        if pred is None:
            continue
        num += weight * np.asarray(pred["softmax"], dtype=float)
        den += weight
    return num / den if den > 0 else num
