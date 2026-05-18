"""
Weighted fusion of module confidence scores.
F = w_visual * sigmoid(C_visual) + w_commentary * sigmoid(C_commentary)
                                 + w_audio * sigmoid(C_audio)
"""

import math
import logging

logger = logging.getLogger(__name__)

# Module weights — must sum to 1.0
# Visual is highest because it directly observes game events.
# Tune these weights using cross-validation on your dataset.
WEIGHTS = {
    "visual": 0.45,
    "commentary": 0.30,
    "audio_energy": 0.25
}


def _sigmoid(x: float, k: float = 5.0, x0: float = 0.5) -> float:
    """Sigmoid normalization centred at x0 with steepness k."""
    return 1.0 / (1.0 + math.exp(-k * (x - x0)))


def compute_fused_score(aligned_outputs: dict) -> float:
    """
    Compute the weighted fused confidence score for one segment.

    Args:
        aligned_outputs: dict keyed by module name from aligner.py

    Returns:
        Fused score in [0.0, 1.0]
    """
    fused = 0.0
    for module_name, weight in WEIGHTS.items():
        output = aligned_outputs.get(module_name)
        raw_confidence = output["confidence"] if output else 0.0
        normalized = _sigmoid(raw_confidence)
        fused += weight * normalized
        logger.debug(
            "  %s: raw=%.4f norm=%.4f weighted=%.4f",
            module_name, raw_confidence, normalized, weight * normalized
        )

    return round(fused, 4)
