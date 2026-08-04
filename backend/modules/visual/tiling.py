"""
Aligned multi-window tiling for the visual module.

The match is tiled into non-overlapping 8s tiles from t=0. Each tile also
gets 16s and 32s "context" clips centred on the same tile's midpoint, clamped
(not shifted) at the match boundaries. Every tile therefore maps to exactly
3 clips in and exactly 1 merged prediction out.
"""

from constants import CONTEXT_WINDOWS_SEC, TILE_SEC


def tile_match(duration_sec: float, tile_sec: int = TILE_SEC,
                context_windows_sec: tuple[int, ...] = CONTEXT_WINDOWS_SEC) -> list[dict]:
    """
    Args:
        duration_sec: total match duration.
        tile_sec: non-overlapping tile size (the finest window).
        context_windows_sec: window sizes to cut per tile, each centred on
            the tile's midpoint. Must include tile_sec itself.

    Returns:
        List of dicts, one per tile:
            {
                "tile_index": int,
                "tile_start_sec": float, "tile_end_sec": float,
                "windows": {window_sec: (clip_start_sec, clip_end_sec), ...},
            }
        The last tile may be shorter than tile_sec if duration isn't a
        multiple of it. Context clips are clamped to [0, duration_sec] at
        the boundaries rather than shifted to keep their nominal length.
    """
    if duration_sec <= 0:
        return []

    import math
    n_tiles = math.ceil(duration_sec / tile_sec)

    tiles = []
    for i in range(n_tiles):
        tile_start = i * tile_sec
        tile_end = min(tile_start + tile_sec, duration_sec)
        center = (tile_start + tile_end) / 2

        windows = {}
        for window_sec in context_windows_sec:
            half = window_sec / 2
            clip_start = max(0.0, center - half)
            clip_end = min(duration_sec, center + half)
            windows[window_sec] = (clip_start, clip_end)

        tiles.append({
            "tile_index": i,
            "tile_start_sec": float(tile_start),
            "tile_end_sec": float(tile_end),
            "windows": windows,
        })

    return tiles
