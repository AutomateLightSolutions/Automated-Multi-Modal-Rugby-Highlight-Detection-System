"""
Audio event/highlight scorer (pipeline v2).

Loads the match's full audio track once, selects the non-overlapping subset
of 4.0s/2.0s-hop analysis chunks (modules/audio_energy/chunking.py — halves
feature-extraction work versus scoring every overlapping chunk), then runs
the trained event classifier + highlight regressor on each chunk. Selected
chunks land 1:1 on the 4s master fusion grid (same count and boundaries as
modules.grid.compute_grid_cells), so no de-overlap averaging step is needed
here, unlike the commentary module.

Unlike this module's previous RMS-only implementation, this one does set
predicted_event / event_confidence — fusion (fusion/grid_fusion.py) folds
audio in as a third weighted vote alongside visual and commentary when
deciding fused_event, in addition to using its highlight_score for the
fused score and disagreement check.
"""
import logging

import librosa
import numpy as np

from modules.audio_energy.chunking import build_raw_chunks, select_non_overlapping_chunks
from modules.audio_energy.features import SAMPLE_RATE, extract_features
from modules.audio_energy.inference import predict_chunk
from modules.grid import compute_grid_cells

logger = logging.getLogger(__name__)


def analyze_match(audio_path: str, duration_sec: float) -> dict:
    """
    Run the full audio event/highlight analysis over one match's audio track.

    Returns:
        {"cells": [{cell_index, global_start_sec, global_end_sec,
                    predicted_event, event_confidence, highlight_score,
                    extra}, ...]}
    """
    try:
        y, _ = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
    except Exception:
        logger.exception("Failed to load audio %s", audio_path)
        y = np.zeros(0, dtype=np.float32)

    raw_chunks = build_raw_chunks(duration_sec)
    selected_chunks = select_non_overlapping_chunks(raw_chunks)
    grid_cells = compute_grid_cells(duration_sec)

    if len(selected_chunks) != len(grid_cells):
        logger.warning(
            "Audio chunk/grid mismatch for a %.2fs match: %d selected chunks vs %d grid cells",
            duration_sec, len(selected_chunks), len(grid_cells),
        )

    cells = []
    skipped = 0
    for grid_cell, chunk in zip(grid_cells, selected_chunks):
        start_sample = int(chunk["start_time"] * SAMPLE_RATE)
        end_sample = int(chunk["end_time"] * SAMPLE_RATE)
        segment = y[start_sample:end_sample]

        features = extract_features(segment, sr=SAMPLE_RATE)
        if features is None:
            skipped += 1
            cells.append({
                "cell_index": grid_cell["cell_index"],
                "global_start_sec": grid_cell["start_sec"],
                "global_end_sec": grid_cell["end_sec"],
                "predicted_event": None,
                "event_confidence": None,
                "highlight_score": 0.0,
                "extra": {"is_partial": grid_cell["is_partial"], "skipped": True},
            })
            continue

        prediction = predict_chunk(features)
        cells.append({
            "cell_index": grid_cell["cell_index"],
            "global_start_sec": grid_cell["start_sec"],
            "global_end_sec": grid_cell["end_sec"],
            "predicted_event": prediction["predicted_event"],
            "event_confidence": prediction["event_confidence"],
            "highlight_score": prediction["highlight_score"],
            "extra": {"is_partial": grid_cell["is_partial"]},
        })

    logger.info(
        "Audio energy analysis: %d raw chunks, %d selected, %d cells (%d skipped)",
        len(raw_chunks), len(selected_chunks), len(grid_cells), skipped,
    )
    return {"cells": cells}
