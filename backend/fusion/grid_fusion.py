"""
Grid-based fusion engine (pipeline v2).

Combines per-module predictions — visual's 8s tiles, commentary/audio's 4s
grid cells — onto the master 4s fusion grid. Visual's 8s tile covers exactly
2 grid cells (cell j's covering tile is j // 2); commentary and audio
already share the grid, so their rows map onto cells 1:1 by index.

Runs once automatically when match processing completes (all 3 module
tasks finish); results are stored per fusion_run so re-fusing with
different weights never overwrites a prior run.
"""
import math
import logging

import numpy as np

from constants import EVENT_CLASSES

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS: dict[str, float] = {"visual": 0.45, "commentary": 0.30, "audio": 0.25}
SIGMOID_K = 5.0
# |sig(visual_score) - sig(audio_score)| beyond this also counts as disagreement,
# independent of whether the two modules' event calls differ.
DISAGREEMENT_SCORE_GAP = 0.4

_CLASS_INDEX = {name: i for i, name in enumerate(EVENT_CLASSES)}
_NORMAL_PLAY_IDX = _CLASS_INDEX["normal_play"]


def _sigmoid(x: float, k: float = SIGMOID_K, x0: float = 0.5) -> float:
    return 1.0 / (1.0 + math.exp(-k * (x - x0)))


def _event_probs_from_prediction(row: dict) -> np.ndarray:
    """One-hot on predicted_event scaled by event_confidence, with the
    residual mass placed on normal_play. Used for commentary and audio —
    unlike visual's softmax, neither gives a full probability vector, just
    one best guess plus a confidence heuristic."""
    vec = np.zeros(len(EVENT_CLASSES))
    idx = _CLASS_INDEX.get(row.get("predicted_event"), _NORMAL_PLAY_IDX)
    confidence = row.get("event_confidence") or 0.0
    vec[idx] = confidence
    vec[_NORMAL_PLAY_IDX] += (1.0 - confidence)
    return vec


_MODULE_ROWS = ("visual", "commentary", "audio")


def _score_contributions(rows_by_module: dict[str, dict | None], weights: dict) -> tuple[float, dict, list[str]]:
    """Weighted-average sigmoid(highlight_score) across present modules, plus
    the per-module contributions dict the fusion_cells row stores verbatim."""
    modules_present = []
    score_num = 0.0
    score_den = 0.0
    contributions = {}

    for module_name in _MODULE_ROWS:
        row = rows_by_module[module_name]
        weight = weights[module_name]
        if row is not None:
            modules_present.append(module_name)
            raw_score = row["highlight_score"]
            sig_score = _sigmoid(raw_score)
            score_num += weight * sig_score
            score_den += weight
            contributions[module_name] = {
                "event": row.get("predicted_event"),
                "event_confidence": row.get("event_confidence"),
                "highlight_score": raw_score,
                "sigmoid_score": round(sig_score, 4),
                "weight": weight,
                "present": True,
            }
        else:
            contributions[module_name] = {
                "event": None, "event_confidence": None, "highlight_score": None,
                "sigmoid_score": None, "weight": weight, "present": False,
            }

    fused_score = score_num / score_den if score_den > 0 else 0.0
    return fused_score, contributions, modules_present


def _fused_event(rows_by_module: dict[str, dict | None], weights: dict) -> tuple[str, float]:
    """Weighted vote over visual's softmax + commentary/audio's one-hot
    guesses, renormalized over whichever modules are present. Visual gives a
    full probability vector; commentary and audio each give one best guess
    plus a confidence heuristic (_event_probs_from_prediction)."""
    active_weights = {
        module: weights[module] for module in _MODULE_ROWS if rows_by_module[module] is not None
    }
    event_weight_total = sum(active_weights.values())

    if event_weight_total == 0:
        event_vec = np.zeros(len(EVENT_CLASSES))
        event_vec[_NORMAL_PLAY_IDX] = 1.0
    else:
        visual_row = rows_by_module["visual"]
        visual_probs = np.array(visual_row["event_probs"]) if visual_row is not None else np.zeros(len(EVENT_CLASSES))
        commentary_probs = (
            _event_probs_from_prediction(rows_by_module["commentary"])
            if rows_by_module["commentary"] is not None else np.zeros(len(EVENT_CLASSES))
        )
        audio_probs = (
            _event_probs_from_prediction(rows_by_module["audio"])
            if rows_by_module["audio"] is not None else np.zeros(len(EVENT_CLASSES))
        )
        event_vec = (
            active_weights.get("visual", 0.0) * visual_probs
            + active_weights.get("commentary", 0.0) * commentary_probs
            + active_weights.get("audio", 0.0) * audio_probs
        ) / event_weight_total

    best_idx = int(np.argmax(event_vec))
    return EVENT_CLASSES[best_idx], float(event_vec[best_idx])


def _check_disagreement(rows_by_module: dict[str, dict | None]) -> bool:
    """True if visual and commentary call different (non-normal_play)
    events, or if visual and audio's excitement scores diverge sharply."""
    visual_row = rows_by_module["visual"]
    commentary_row = rows_by_module["commentary"]
    audio_row = rows_by_module["audio"]

    if visual_row is not None and commentary_row is not None:
        v_event = visual_row.get("predicted_event")
        c_event = commentary_row.get("predicted_event")
        if v_event != "normal_play" and c_event != "normal_play" and v_event != c_event:
            return True

    if visual_row is not None and audio_row is not None:
        v_sig = _sigmoid(visual_row["highlight_score"])
        a_sig = _sigmoid(audio_row["highlight_score"])
        if abs(v_sig - a_sig) > DISAGREEMENT_SCORE_GAP:
            return True

    return False


def fuse_cell(cell_index: int, visual_row: dict | None, commentary_row: dict | None,
              audio_row: dict | None, weights: dict = DEFAULT_WEIGHTS) -> dict:
    """
    Fuse one grid cell's per-module rows into a fused score/event.

    Each *_row (if present) is a plain dict with at least "highlight_score";
    visual_row additionally needs "event_probs" (10-dim), commentary_row and
    audio_row need "predicted_event"/"event_confidence".

    Returns: {cell_index, fused_event, fused_event_confidence, fused_score,
              contributions, modules_present, disagreement}
    """
    rows_by_module = {"visual": visual_row, "commentary": commentary_row, "audio": audio_row}

    fused_score, contributions, modules_present = _score_contributions(rows_by_module, weights)
    fused_event, fused_event_confidence = _fused_event(rows_by_module, weights)
    disagreement = _check_disagreement(rows_by_module)

    return {
        "cell_index": cell_index,
        "fused_event": fused_event,
        "fused_event_confidence": round(fused_event_confidence, 4),
        "fused_score": round(fused_score, 4),
        "contributions": contributions,
        "modules_present": modules_present,
        "disagreement": disagreement,
    }


def run_fusion(duration_sec: float, visual_rows: list[dict], commentary_rows: list[dict],
               audio_rows: list[dict], weights: dict = DEFAULT_WEIGHTS) -> list[dict]:
    """
    Fuse a whole match's module_predictions onto the 4s grid.

    Each *_rows arg is the list of that module's rows (plain dicts, each
    with "index_in_module" — tile index for visual, cell index for
    commentary/audio — plus the fields fuse_cell needs).

    Returns one dict per grid cell (fuse_cell's output, plus
    global_start_sec/global_end_sec/visual_tile_index/is_partial).
    """
    from modules.grid import compute_grid_cells

    visual_by_tile = {row["index_in_module"]: row for row in visual_rows}
    commentary_by_cell = {row["index_in_module"]: row for row in commentary_rows}
    audio_by_cell = {row["index_in_module"]: row for row in audio_rows}

    grid_cells = compute_grid_cells(duration_sec)
    fused = []
    for grid_cell in grid_cells:
        j = grid_cell["cell_index"]
        tile_index = j // 2
        result = fuse_cell(
            j,
            visual_by_tile.get(tile_index),
            commentary_by_cell.get(j),
            audio_by_cell.get(j),
            weights=weights,
        )
        result["global_start_sec"] = grid_cell["start_sec"]
        result["global_end_sec"] = grid_cell["end_sec"]
        result["visual_tile_index"] = tile_index
        result["is_partial"] = grid_cell["is_partial"]
        fused.append(result)

    logger.info("Fusion: %d cells fused (weights=%s)", len(fused), weights)
    return fused
