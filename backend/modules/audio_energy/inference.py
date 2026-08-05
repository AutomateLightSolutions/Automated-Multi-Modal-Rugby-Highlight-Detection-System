"""
Audio event classifier + highlight regressor — loaded once per Celery
worker process (module-level singleton), same pattern as
modules/visual/inference.py's get_model().

Two independent branches share one 78-dim feature vector:
    classification: best_event_model.pkl + best_event_scaler.pkl
    regression:      best_highlight_model.pkl + best_highlight_scaler.pkl
Never cross-pair a model with the wrong scaler.
"""
import logging

import joblib
import numpy as np

from config import settings
from constants import EventClass

logger = logging.getLogger(__name__)

WEIGHTS_DIR = settings.MODEL_WEIGHTS_PATH / "audio_energy"
EVENT_MODEL_PATH = WEIGHTS_DIR / "best_event_model.pkl"
EVENT_SCALER_PATH = WEIGHTS_DIR / "best_event_scaler.pkl"
HIGHLIGHT_MODEL_PATH = WEIGHTS_DIR / "best_highlight_model.pkl"
HIGHLIGHT_SCALER_PATH = WEIGHTS_DIR / "best_highlight_scaler.pkl"

# The event model's own fixed training-time label order (index = canonical
# label), mapped straight onto constants.EventClass — the value every other
# module (visual, commentary, fusion) already uses for predicted_event.
EVENTS_LIST: list[EventClass] = [
    EventClass.TRY,          # 0
    EventClass.GOAL_KICK,    # 1
    EventClass.CARD_EVENT,   # 2
    EventClass.SCRUM,        # 3
    EventClass.MAUL,         # 4
    EventClass.LINEOUT,      # 5
    EventClass.KICK_OFF,     # 6
    EventClass.TMO_REPLAY,   # 7
    EventClass.NORMAL_PLAY,  # 8
    EventClass.PENALTY,      # 9
]

_event_model = None
_event_classes: list[int] | None = None
_event_scaler = None
_highlight_model = None
_highlight_scaler = None


def _get_event_artifacts():
    global _event_model, _event_classes, _event_scaler
    if _event_model is None:
        bundle = joblib.load(EVENT_MODEL_PATH)
        _event_model = bundle["model"]
        _event_classes = bundle["classes"]
        _event_scaler = joblib.load(EVENT_SCALER_PATH)
        logger.info(
            "Audio event model loaded from %s (%s)",
            EVENT_MODEL_PATH, type(_event_model).__name__,
        )
    return _event_model, _event_classes, _event_scaler


def _get_highlight_artifacts():
    global _highlight_model, _highlight_scaler
    if _highlight_model is None:
        _highlight_model = joblib.load(HIGHLIGHT_MODEL_PATH)
        _highlight_scaler = joblib.load(HIGHLIGHT_SCALER_PATH)
        logger.info(
            "Audio highlight model loaded from %s (%s)",
            HIGHLIGHT_MODEL_PATH, type(_highlight_model).__name__,
        )
    return _highlight_model, _highlight_scaler


def predict_chunk(features: np.ndarray) -> dict:
    """
    Run both branches over one chunk's 78-dim feature vector.

    Returns: {"predicted_event": EVENT_CLASSES value, "event_confidence",
              "highlight_score"} — event_confidence is the classifier's own
    internal confidence heuristic, not a calibrated probability.
    """
    model, classes, scaler = _get_event_artifacts()
    scaled = scaler.transform(features.reshape(1, -1))
    proba = model.predict_proba(scaled)[0]
    pred_class_encoded = int(np.argmax(proba))
    event_confidence = float(proba[pred_class_encoded])

    original_label = classes[pred_class_encoded]  # decode dense training-time encoding
    predicted_event = EVENTS_LIST[original_label].value

    h_model, h_scaler = _get_highlight_artifacts()
    h_scaled = h_scaler.transform(features.reshape(1, -1))
    raw_score = float(h_model.predict(h_scaled)[0])
    highlight_score = max(0.0, min(1.0, raw_score))  # raw regressor output is unbounded

    return {
        "predicted_event": predicted_event,
        "event_confidence": round(event_confidence, 4),
        "highlight_score": round(highlight_score, 4),
    }
