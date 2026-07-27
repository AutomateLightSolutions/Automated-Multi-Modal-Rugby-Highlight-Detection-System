"""
Commentary excitement scorer.
Scores a segment based on rugby keywords detected in transcription.
confidence = overall excitement level of the commentary (0.0 to 1.0)
event_type = canonical event class (constants.EventType) of the
             highest-weight keyword found (or None)
event_confidence = None (commentary does not classify events with certainty)
"""

import math
import logging
from modules.commentary.asr import transcribe_audio

logger = logging.getLogger(__name__)

# Keywords, their excitement weights, and the canonical EventType they map to.
# word -> (weight, event_type)
RUGBY_KEYWORDS = {
    "try": (1.0, "try"),
    "scrum": (0.85, "scrum"),
    "penalty": (0.80, "kick"),
    "lineout": (0.75, "lineout"),
    "conversion": (0.70, "kick"),
    "kick": (0.65, "kick"),
    "yellow": (0.85, "card"),
    "red": (0.90, "card"),
    "card": (0.80, "card"),
    "sinbin": (0.80, "card"),
    "tmo": (0.55, "tmo_replay"),
    "replay": (0.50, "tmo_replay"),
    "review": (0.50, "tmo_replay"),
    "offload": (0.65, None),
    "tackle": (0.60, None),
    "breakdown": (0.55, None),
    "ruck": (0.55, None),
    "maul": (0.50, None),
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


def run_inference(audio_path: str, global_start_sec: float,
                  global_end_sec: float) -> dict:
    """
    Score commentary excitement for a single audio chunk.
    """
    words = transcribe_audio(audio_path, global_start_sec)

    raw_score = 0.0
    best_event = None
    best_event_weight = 0.0

    for word_data in words:
        word = word_data["word"].lower().strip(".,!?")
        if word in RUGBY_KEYWORDS:
            weight, event_type = RUGBY_KEYWORDS[word]
            raw_score += weight
            # Only words that map to a canonical event class can win the
            # segment's event_type — others (e.g. "tackle") only add excitement.
            if event_type is not None and weight > best_event_weight:
                best_event_weight = weight
                best_event = event_type

    # Clip raw score (can exceed 1.0 with many keywords)
    raw_score = min(raw_score, 2.0) / 2.0  # normalise to [0,1]
    confidence = _sigmoid_normalize(raw_score)

    return {
        "segment_id": None,
        "module": "commentary",
        "global_start_sec": global_start_sec,
        "global_end_sec": global_end_sec,
        "confidence": round(confidence, 4),
        "event_type": best_event,
        "event_confidence": None,   # commentary never sets this
        "extra_data": {
            "num_words_transcribed": len(words),
            "keywords_found": [
                w["word"] for w in words
                if w["word"] in RUGBY_KEYWORDS
            ],
            "raw_score": round(raw_score, 4)
        }
    }
