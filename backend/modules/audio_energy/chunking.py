"""
Chunk generation and prediction-time non-overlapping selection for the
audio_energy event/highlight models.

The models were trained on overlapping 4.0s-window/2.0s-hop chunks (the same
scheme modules/grid.py already uses for audio/commentary analysis windows).
Inference only needs a non-overlapping subset of those — extracting features
for the discarded overlap wastes roughly half the compute, so the filter is
applied once per match, before any feature extraction.
"""
from modules.grid import compute_analysis_windows


def build_raw_chunks(duration_sec: float) -> list[dict]:
    """The full overlapping 4.0s/2.0s-hop chunk set. Training used every one
    of these; only prediction discards the overlap (see
    select_non_overlapping_chunks)."""
    windows = compute_analysis_windows(duration_sec)
    return [
        {"chunk_id": i, "start_time": start, "end_time": end}
        for i, (start, end) in enumerate(windows)
    ]


def select_non_overlapping_chunks(chunks: list[dict]) -> list[dict]:
    """Greedy, sorted by start_time: keep a chunk only if its start is at or
    after the previously-kept chunk's end. Prediction-time-only — training
    still uses every overlapping chunk."""
    selected = []
    last_end = None
    for chunk in sorted(chunks, key=lambda c: c["start_time"]):
        if last_end is None or chunk["start_time"] >= last_end - 1e-6:
            selected.append(chunk)
            last_end = chunk["end_time"]
    return selected
