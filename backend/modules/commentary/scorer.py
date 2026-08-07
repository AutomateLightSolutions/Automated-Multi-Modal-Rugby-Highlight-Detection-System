"""
Commentary hybrid (ML transformer + lexicon) excitement/event scorer.

Runs the uploaded DualHeadRoBERTa checkpoint and lexicon.json (via
modules.commentary.weights_io) over the match's Whisper transcript, chunked
onto the shared 4s master fusion grid (modules.commentary.chunking). One
batched forward pass scores every non-silent cell; results are combined via
modules.commentary.hybrid.predict_chunks.

Requires a model + lexicon to have been uploaded via the Models admin page
(POST /api/v1/admin/models/upload) — there is no keyword-lexicon fallback,
matching the visual module's hard dependency on
backend/weights/visual/best_model.pt existing on disk.
"""
import logging

from modules.commentary import weights_io
from modules.commentary.asr import transcribe_match
from modules.commentary.chunking import build_grid_chunks
from modules.commentary.hybrid import predict_chunks

logger = logging.getLogger(__name__)


def analyze_match(
    audio_path: str, duration_sec: float, lag_sec: float = 0.0, on_stage=None,
) -> dict:
    """
    Run the full commentary hybrid analysis over one match's audio track.

    Args:
        lag_sec: shift word timestamps earlier by this much before gridding
            (commentators react after the play). Default 0.0 — see
            config.settings.COMMENTARY_LAG_SEC.
        on_stage: optional callback(stage_name: str), invoked before each
            major phase ("transcribing" | "loading_model" | "scoring").
            Whisper/inference are single blocking calls with no fine-grained
            progress of their own, so this is coarse — enough for the caller
            to show *something* moved instead of a bare "Running…" for the
            whole task duration.

    Returns:
        {"cells": [{cell_index, global_start_sec, global_end_sec,
                    predicted_event, event_confidence, highlight_score,
                    extra}, ...],
         "transcript": [word dicts, absolute match time]}
    """
    if not (weights_io.is_model_available() and weights_io.is_lexicon_available()):
        raise RuntimeError(
            "No commentary model/lexicon installed. Upload a model checkpoint and "
            "lexicon.json via the Models admin page (/admin/models) before processing a match."
        )

    if on_stage:
        on_stage("transcribing")
    words = transcribe_match(audio_path)
    if lag_sec:
        words = [
            {**w, "start": max(0.0, w["start"] - lag_sec), "end": max(0.0, w["end"] - lag_sec)}
            for w in words
        ]

    chunks = build_grid_chunks(words, duration_sec)

    if on_stage:
        on_stage("loading_model")
    model, tokenizer, id2label, device = weights_io.get_checkpoint()
    lexicon = weights_io.get_lexicon()

    if on_stage:
        on_stage("scoring")
    predictions = predict_chunks(chunks, model, tokenizer, id2label, lexicon, device)

    cells = [
        {
            "cell_index": chunk["cell_index"],
            "global_start_sec": chunk["start_sec"],
            "global_end_sec": chunk["end_sec"],
            "predicted_event": pred["predicted_event"],
            "event_confidence": pred["event_confidence"],
            "highlight_score": pred["highlight_score"],
            "extra": {**pred["extra"], "is_partial": chunk["is_partial"]},
        }
        for chunk, pred in zip(chunks, predictions)
    ]

    logger.info("Commentary analysis: %d words, %d cells", len(words), len(cells))
    return {"cells": cells, "transcript": words}
