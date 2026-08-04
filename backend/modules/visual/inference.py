"""
Visual module inference — orchestrates tiling, SlowFast forward passes, and
per-tile merge for one match's full visual-only track.

The model is loaded once per Celery worker process (module-level singleton),
never per clip or per tile — SlowFast is expensive enough that reloading it
per clip would be the dominant cost.
"""
import logging

import torch
import torch.nn.functional as F

from config import settings
from constants import EVENT_CLASSES
from modules.visual.merge import merge_tile
from modules.visual.model import RugbyVisualClassifier
from modules.visual.preprocessing import build_pathway_tensors
from modules.visual.tiling import tile_match

logger = logging.getLogger(__name__)

CHECKPOINT_PATH = settings.MODEL_WEIGHTS_PATH / "visual" / "best_model.pt"

_model: RugbyVisualClassifier | None = None
_device: torch.device | None = None


def get_device() -> torch.device:
    global _device
    if _device is None:
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Visual module device: %s", _device)
    return _device


def get_model() -> RugbyVisualClassifier:
    global _model
    if _model is None:
        device = get_device()
        model = RugbyVisualClassifier()
        # weights_only=True restricts unpickling to tensors/plain types — this
        # checkpoint is only {epoch, model_state_dict, val_loss}, so it's safe
        # and avoids torch.load's arbitrary-code-execution surface.
        checkpoint = torch.load(CHECKPOINT_PATH, map_location=device, weights_only=True)
        model.load_state_dict(checkpoint["model_state_dict"], strict=True)
        model.to(device)
        model.eval()
        _model = model
        logger.info(
            "Visual model loaded from %s (epoch=%s, val_loss=%s)",
            CHECKPOINT_PATH, checkpoint.get("epoch"), checkpoint.get("val_loss"),
        )
    return _model


def _run_window(model: RugbyVisualClassifier, device: torch.device,
                 video_path: str, clip_start: float, clip_end: float) -> dict:
    slow, fast = build_pathway_tensors(video_path, clip_start, clip_end)
    slow = slow.to(device)
    fast = fast.to(device)
    with torch.no_grad():
        class_logits, score = model(slow, fast)
        probs = F.softmax(class_logits, dim=1)
    return {
        "softmax": probs[0].detach().cpu().tolist(),
        "score": float(score[0].detach().cpu()),
    }


def analyze_match(video_path: str, duration_sec: float) -> dict:
    """
    Run the full tiled SlowFast analysis over one match's visual-only track.

    Returns:
        {
            "tiles": [ {tile_index, global_start_sec, global_end_sec, module,
                        window_sec, predicted_event, event_confidence,
                        highlight_score, event_probs, extra}, ... ],
            "raw_windows": [ {tile_index, window_sec, clip_start_sec, clip_end_sec,
                               raw_event, raw_confidence, raw_score, softmax,
                               masked_mass, dropped, drop_reason}, ... ],
        }
    """
    model = get_model()
    device = get_device()

    tiles = tile_match(duration_sec)
    tile_records = []
    raw_window_records = []

    for tile in tiles:
        window_predictions = {}
        for window_sec, (clip_start, clip_end) in tile["windows"].items():
            window_predictions[window_sec] = _run_window(model, device, video_path, clip_start, clip_end)

        merged = merge_tile(window_predictions)

        for window_sec, (clip_start, clip_end) in tile["windows"].items():
            pred = window_predictions[window_sec]
            audit = merged["window_audit"].get(window_sec, {"masked_mass": 0.0, "dropped": True})
            raw_best_idx = pred["softmax"].index(max(pred["softmax"]))
            raw_window_records.append({
                "tile_index": tile["tile_index"],
                "window_sec": window_sec,
                "clip_start_sec": clip_start,
                "clip_end_sec": clip_end,
                "raw_event": EVENT_CLASSES[raw_best_idx],
                "raw_confidence": round(pred["softmax"][raw_best_idx], 6),
                "raw_score": round(pred["score"], 4),
                "softmax": pred["softmax"],
                "masked_mass": audit["masked_mass"],
                "dropped": audit["dropped"],
                "drop_reason": (
                    "masked probability mass below threshold" if audit["dropped"] else None
                ),
            })

        tile_records.append({
            "tile_index": tile["tile_index"],
            "global_start_sec": tile["tile_start_sec"],
            "global_end_sec": tile["tile_end_sec"],
            "predicted_event": merged["predicted_event"],
            "event_confidence": merged["event_confidence"],
            "highlight_score": merged["merged_score"],
            "event_probs": merged["event_probs"],
            "extra": {
                "fallback_used": merged["fallback_used"],
                "windows_dropped": merged["windows_dropped"],
            },
        })

        logger.debug(
            "tile %d [%.1fs-%.1fs]: event=%s conf=%.3f score=%.3f dropped=%s fallback=%s",
            tile["tile_index"], tile["tile_start_sec"], tile["tile_end_sec"],
            merged["predicted_event"], merged["event_confidence"], merged["merged_score"],
            merged["windows_dropped"], merged["fallback_used"],
        )

    return {"tiles": tile_records, "raw_windows": raw_window_records}
