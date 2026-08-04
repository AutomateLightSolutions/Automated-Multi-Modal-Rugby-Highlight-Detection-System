"""
Automatic Speech Recognition using OpenAI Whisper.

Transcribes the whole match's audio track in a single pass with word-level
timestamps — not per 4s/2s window, which would destroy ASR context and mean
thousands of Whisper invocations per match. The 4s/2s analysis windows are
built afterwards (modules/commentary/scorer.py) by assigning each word to
the windows its timestamp falls inside.
"""
import logging

import torch
import whisper

from config import settings

logger = logging.getLogger(__name__)

_whisper_model = None


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _whisper_model = whisper.load_model(settings.WHISPER_MODEL_SIZE, device=device)
        logger.info("Whisper model '%s' loaded on %s", settings.WHISPER_MODEL_SIZE, device)
    return _whisper_model


def transcribe_match(audio_path: str) -> list[dict]:
    """
    Transcribe one match's full audio track.

    Returns a list of word dicts, in absolute match time (the audio track
    already starts at t=0 of the match, so no offset is needed):
        {"word": str, "start": float, "end": float, "confidence": float}
    """
    model = _get_whisper_model()
    result = model.transcribe(audio_path, word_timestamps=True)

    words = []
    for segment in result.get("segments", []):
        for word_data in segment.get("words", []):
            words.append({
                "word": word_data["word"].strip().lower(),
                "start": float(word_data["start"]),
                "end": float(word_data["end"]),
                "confidence": float(word_data.get("probability", 1.0)),
            })
    return words
