"""
Audio energy excitement scorer (pipeline v2).

Loads the audio track once, computes RMS over 4s/2s-hop analysis windows,
normalizes each window's 90th-percentile RMS to its percentile rank across
the whole match (so broadcast-level differences don't skew scores), then
de-overlaps onto the 4s master fusion grid — same scheme as the commentary
module (modules/grid.py).

Audio energy never sets an event: predicted_event / event_confidence are
always None. It's a pure excitement signal, not a classifier.
"""
import logging

import numpy as np

from modules.audio_energy.extractor import extract_rms_energy_with_times
from modules.grid import compute_analysis_windows, compute_grid_cells, deoverlap_weighted_average

logger = logging.getLogger(__name__)


def _percentile_rank(values: np.ndarray) -> np.ndarray:
    """Rank each value's position among all values, scaled to [0, 1]."""
    if len(values) <= 1:
        return np.zeros_like(values, dtype=float)
    order = np.argsort(values)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(len(values))
    return ranks / (len(values) - 1)


def analyze_match(audio_path: str, duration_sec: float) -> dict:
    """
    Run the full windowed audio-energy analysis over one match's audio track.

    Returns:
        {"cells": [{cell_index, global_start_sec, global_end_sec,
                    predicted_event: None, event_confidence: None,
                    highlight_score, extra}, ...]}
    """
    rms, times = extract_rms_energy_with_times(audio_path)

    windows = compute_analysis_windows(duration_sec)
    grid_cells = compute_grid_cells(duration_sec)

    raw_p90 = np.zeros(len(windows))
    for idx, (w_start, w_end) in enumerate(windows):
        mask = (times >= w_start) & (times < w_end)
        window_rms = rms[mask]
        raw_p90[idx] = float(np.percentile(window_rms, 90)) if len(window_rms) else 0.0

    normalized = _percentile_rank(raw_p90)
    window_scores = {idx: float(normalized[idx]) for idx in range(len(windows))}

    n_cells = len(grid_cells)
    cell_scores = deoverlap_weighted_average(window_scores, n_cells)

    cells = []
    for j, grid_cell in enumerate(grid_cells):
        score = cell_scores[j] if cell_scores[j] is not None else 0.0
        cells.append({
            "cell_index": j,
            "global_start_sec": grid_cell["start_sec"],
            "global_end_sec": grid_cell["end_sec"],
            "predicted_event": None,
            "event_confidence": None,
            "highlight_score": round(float(score), 4),
            "extra": {"is_partial": grid_cell["is_partial"]},
        })

    logger.info("Audio energy analysis: %d windows, %d cells", len(windows), n_cells)
    return {"cells": cells}
