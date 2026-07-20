"""
Automatic Speech Recognition using OpenAI Whisper.

STUB BEHAVIOUR (current):
- Returns fake word-level transcription with rugby keywords

HOW TO REPLACE WITH REAL WHISPER:
1. _get_whisper_model() loads model once (singleton)
2. whisper.transcribe() with word_timestamps=True returns word-level data
3. Add global_start_sec to each word timestamp to convert from
   chunk-local time to match-global time.
   CRITICAL: chunk audio file always starts at t=0 internally,
   but it represents global_start_sec in the match.
   So: word_global_start = word_local_start + global_start_sec
"""

import random
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Whisper model singleton — loads once on worker startup
# Uncomment to use real Whisper:
#
# import whisper
# _whisper_model = None
#
# def _get_whisper_model():
#     global _whisper_model
#     if _whisper_model is None:
#         _whisper_model = whisper.load_model("base")
#         logger.info("Whisper model loaded")
#     return _whisper_model
# ---------------------------------------------------------------------------

RUGBY_VOCABULARY = [
    "scrum", "try", "lineout", "penalty", "conversion", "kick",
    "yellow", "red", "card", "sinbin", "tmo", "replay", "review",
    "tackle", "breakdown", "ruck", "maul", "offload",
    "grubber", "incredible", "brilliant", "danger",
    "forward", "referee", "whistle", "ball", "player",
    "and", "the", "it", "is", "a", "to", "in"
]


def transcribe_audio(audio_path: str,
                     global_start_sec: float) -> list[dict]:
    """
    Transcribe audio chunk and return word-level timestamps
    mapped to global match time.

    Returns list of dicts:
    {
        "word": str,
        "global_start": float,  # seconds from match start
        "global_end": float,
        "confidence": float
    }
    """
    logger.debug("transcribe_audio called on %s (stub)", audio_path)
    # --- STUB IMPLEMENTATION ---
    # Replace with:
    # model = _get_whisper_model()
    # result = model.transcribe(audio_path, word_timestamps=True)
    # words = []
    # for segment in result["segments"]:
    #     for word_data in segment.get("words", []):
    #         words.append({
    #             "word": word_data["word"].strip().lower(),
    #             "global_start": word_data["start"] + global_start_sec,
    #             "global_end": word_data["end"] + global_start_sec,
    #             "confidence": word_data.get("probability", 1.0)
    #         })
    # return words

    num_words = random.randint(8, 20)
    words = []
    current_time = global_start_sec

    for _ in range(num_words):
        word = random.choice(RUGBY_VOCABULARY)
        duration = random.uniform(0.1, 0.6)
        words.append({
            "word": word,
            "global_start": round(current_time, 3),
            "global_end": round(current_time + duration, 3),
            "confidence": round(random.uniform(0.7, 0.99), 3)
        })
        current_time += duration + random.uniform(0.05, 0.3)

    return words
