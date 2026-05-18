"""
Aligns outputs from all three modules for a single segment.
Validates that all modules report the same time window.
"""

import logging

logger = logging.getLogger(__name__)

TIMESTAMP_TOLERANCE_SEC = 0.1  # max allowed divergence between modules


def align_module_outputs(segment_id: str,
                          module_outputs: list[dict]) -> dict:
    """
    Takes a list of module output dicts (one per module) for a single
    segment. Returns a dict keyed by module name.

    Raises ValueError if timestamps diverge beyond tolerance.
    """
    aligned = {}
    reference_start = None

    for output in module_outputs:
        module_name = output["module"]
        start = output["global_start_sec"]

        if reference_start is None:
            reference_start = start
        else:
            if abs(start - reference_start) > TIMESTAMP_TOLERANCE_SEC:
                raise ValueError(
                    f"Timestamp misalignment in segment {segment_id}: "
                    f"module '{module_name}' reports start={start:.3f}s "
                    f"but reference is {reference_start:.3f}s. "
                    f"Check extraction pipeline."
                )

        aligned[module_name] = output

    # Warn if any module is missing
    expected = {"visual", "commentary", "audio_energy"}
    missing = expected - set(aligned.keys())
    if missing:
        logger.warning(
            "Segment %s missing outputs from: %s. "
            "Missing modules will use confidence=0.0 in fusion.",
            segment_id, missing
        )

    return aligned
