"""
Shared 4s-grid / 2s-hop windowing utilities for the audio and commentary
modules. Both compute overlapping analysis windows (W_i = [2i, 2i+4)) and
de-overlap them onto the same non-overlapping master fusion grid
(C_j = [4j, 4j+4)) that fusion reads.

Cell j is exactly covered by window 2j (its overlap weight is 1.0 at the
centre); windows 2j-1 and 2j+1 each cover half of it. Weights 0.25/0.50/0.25
reflect that.
"""
import math

from constants import AUDIO_HOP_SEC, AUDIO_WINDOW_SEC, FUSION_GRID_SEC

# Offsets relative to window index 2j, and their overlap weight.
_DEOVERLAP_OFFSETS: dict[int, float] = {-1: 0.25, 0: 0.50, 1: 0.25}


def compute_analysis_windows(duration_sec: float, window_sec: float = AUDIO_WINDOW_SEC,
                              hop_sec: float = AUDIO_HOP_SEC) -> list[tuple[float, float]]:
    """W_i = [i*hop_sec, i*hop_sec+window_sec), clamped to duration_sec at the tail."""
    windows = []
    i = 0
    while True:
        start = i * hop_sec
        if start >= duration_sec:
            break
        end = min(start + window_sec, duration_sec)
        windows.append((start, end))
        i += 1
    return windows


def compute_grid_cells(duration_sec: float, grid_sec: float = FUSION_GRID_SEC) -> list[dict]:
    """C_j = [j*grid_sec, j*grid_sec+grid_sec). The final cell may be shorter
    than grid_sec if duration isn't a multiple of it — kept, flagged is_partial."""
    if duration_sec <= 0:
        return []
    n_cells = math.ceil(duration_sec / grid_sec)
    cells = []
    for j in range(n_cells):
        start = j * grid_sec
        end = min(start + grid_sec, duration_sec)
        cells.append({
            "cell_index": j,
            "start_sec": float(start),
            "end_sec": float(end),
            "is_partial": (end - start) < grid_sec,
        })
    return cells


def deoverlap_weighted_average(values_by_window_index: dict, n_cells: int):
    """
    Combine analysis-window values onto grid cells via the 0.25/0.50/0.25
    overlap weights, renormalized over whichever of the 3 windows exist
    (edges of the match are missing one side).

    Works for scalar floats and numpy arrays interchangeably (both support
    `weight * value` and `+`), so the same function serves audio's per-window
    scores and commentary's per-window event-vote vectors.

    Returns a list of length n_cells; a cell with no contributing windows at
    all gets None.
    """
    results = []
    for j in range(n_cells):
        weighted_sum = None
        weight_total = 0.0
        for offset, weight in _DEOVERLAP_OFFSETS.items():
            idx = 2 * j + offset
            value = values_by_window_index.get(idx)
            if value is None:
                continue
            contribution = weight * value
            weighted_sum = contribution if weighted_sum is None else weighted_sum + contribution
            weight_total += weight
        results.append(weighted_sum / weight_total if weight_total > 0 else None)
    return results
