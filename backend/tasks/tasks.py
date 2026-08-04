"""
Celery task definitions for the video processing pipeline.
"""
import logging

from celery import chord

from config import settings
from db import SyncSessionLocal
from db.crud import (
    sync_bulk_create_fusion_cells,
    sync_bulk_create_module_predictions,
    sync_bulk_create_visual_window_predictions,
    sync_create_fusion_run,
    sync_get_match,
    sync_get_module_predictions_by_match,
    sync_update_highlight_job,
    sync_update_match_status,
    sync_update_match_transcript,
)
from tasks.celery_app import app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# process_match
# ---------------------------------------------------------------------------

@app.task(bind=True, name="tasks.tasks.process_match")
def process_match(_self, match_id: str, video_path: str):
    from pipeline.extractor import extract_media

    session = SyncSessionLocal()
    try:
        # b. Mark as extracting
        sync_update_match_status(session, match_id, "extracting")

        # c. Extract duration, fps, full audio track, and visual-only track
        meta = extract_media(video_path, match_id, settings.STORAGE_BASE)

        # d. Persist extraction metadata
        sync_update_match_status(
            session, match_id, "extracting",
            duration_sec=meta["duration_sec"], fps=meta["fps"],
            audio_offset_sec=meta["audio_offset_sec"], pipeline_version=2,
        )

        # e. Mark as processing
        sync_update_match_status(session, match_id, "processing")

        # f. All three modules run once per match, directly against the
        # extracted visual/audio tracks — no fixed-duration chunk files.
        # Each module tiles/windows the track internally at its own
        # resolution (visual: 8s tiles; audio/commentary: 4s/2s-hop windows).
        # A chord fuses the match automatically once all three finish.
        chord(
            [
                run_visual_analysis.s(match_id, meta["visual_path"], meta["duration_sec"]),
                run_audio_energy_analysis.s(match_id, meta["full_audio_path"], meta["duration_sec"]),
                run_commentary_analysis.s(
                    match_id, meta["full_audio_path"], meta["duration_sec"], settings.COMMENTARY_LAG_SEC,
                ),
            ]
        )(fuse_match.s(match_id))

        # g. Analyses dispatched and running — status stays "processing" until
        # fuse_match (the chord callback) marks it "done". Highlight generation
        # requires status=="done", so this must reflect real completion, not
        # just dispatch — analysis on a full match can take a while.

    except Exception:
        logger.exception("process_match failed for %s", match_id)
        sync_update_match_status(session, match_id, "failed")
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Module tasks — each runs once per match, not per segment
# ---------------------------------------------------------------------------

@app.task(name="tasks.tasks.run_visual_analysis")
def run_visual_analysis(match_id: str, video_path: str, duration_sec: float) -> dict:
    """Tiled SlowFast analysis over one match's full visual-only track.
    Writes to module_predictions (window_sec=8, one row per tile) and
    visual_window_predictions (the raw 8s/16s/32s audit trail behind each
    tile's merged prediction)."""
    from modules.visual.inference import analyze_match

    result = analyze_match(video_path, duration_sec)

    module_prediction_rows = [
        {
            "window_sec": 8,
            "index_in_module": tile["tile_index"],
            "global_start_sec": tile["global_start_sec"],
            "global_end_sec": tile["global_end_sec"],
            "predicted_event": tile["predicted_event"],
            "event_confidence": tile["event_confidence"],
            "highlight_score": tile["highlight_score"],
            "event_probs": tile["event_probs"],
            "extra": tile["extra"],
        }
        for tile in result["tiles"]
    ]

    session = SyncSessionLocal()
    try:
        sync_bulk_create_module_predictions(session, match_id, "visual", module_prediction_rows)
        sync_bulk_create_visual_window_predictions(session, match_id, result["raw_windows"])
    finally:
        session.close()

    return {"match_id": match_id, "module": "visual", "tiles": len(result["tiles"])}


@app.task(name="tasks.tasks.run_audio_energy_analysis")
def run_audio_energy_analysis(match_id: str, audio_path: str, duration_sec: float) -> dict:
    """Windowed RMS energy analysis over one match's full audio track.
    Writes to module_predictions (window_sec=4, one row per grid cell)."""
    from modules.audio_energy.scorer import analyze_match

    result = analyze_match(audio_path, duration_sec)

    module_prediction_rows = [
        {
            "window_sec": 4,
            "index_in_module": cell["cell_index"],
            "global_start_sec": cell["global_start_sec"],
            "global_end_sec": cell["global_end_sec"],
            "predicted_event": cell["predicted_event"],
            "event_confidence": cell["event_confidence"],
            "highlight_score": cell["highlight_score"],
            "extra": cell["extra"],
        }
        for cell in result["cells"]
    ]

    session = SyncSessionLocal()
    try:
        sync_bulk_create_module_predictions(session, match_id, "audio", module_prediction_rows)
    finally:
        session.close()

    return {"match_id": match_id, "module": "audio", "cells": len(result["cells"])}


@app.task(name="tasks.tasks.run_commentary_analysis")
def run_commentary_analysis(match_id: str, audio_path: str, duration_sec: float,
                             lag_sec: float = 0.0) -> dict:
    """One Whisper pass over the match's full audio track, gridded onto 4s
    cells. Writes to module_predictions (window_sec=4) and persists the full
    word-timestamped transcript onto the match row."""
    from modules.commentary.scorer import analyze_match

    result = analyze_match(audio_path, duration_sec, lag_sec=lag_sec)

    module_prediction_rows = [
        {
            "window_sec": 4,
            "index_in_module": cell["cell_index"],
            "global_start_sec": cell["global_start_sec"],
            "global_end_sec": cell["global_end_sec"],
            "predicted_event": cell["predicted_event"],
            "event_confidence": cell["event_confidence"],
            "highlight_score": cell["highlight_score"],
            "extra": cell["extra"],
        }
        for cell in result["cells"]
    ]

    session = SyncSessionLocal()
    try:
        sync_bulk_create_module_predictions(session, match_id, "commentary", module_prediction_rows)
        sync_update_match_transcript(session, match_id, result["transcript"])
    finally:
        session.close()

    return {"match_id": match_id, "module": "commentary", "cells": len(result["cells"])}


# ---------------------------------------------------------------------------
# fuse_match — chord callback, runs once all 3 module tasks finish
# ---------------------------------------------------------------------------

def _module_prediction_to_dict(row) -> dict:
    return {
        "index_in_module": row.index_in_module,
        "predicted_event": row.predicted_event,
        "event_confidence": row.event_confidence,
        "highlight_score": row.highlight_score,
        "event_probs": row.event_probs,
    }


@app.task(name="tasks.tasks.fuse_match")
def fuse_match(_module_results, match_id: str) -> dict:
    """Chord callback: fires once run_visual_analysis, run_audio_energy_analysis,
    and run_commentary_analysis have all finished. Fuses their module_predictions
    onto the 4s grid and stores a new (active) fusion_run + its fusion_cells."""
    from fusion.grid_fusion import DEFAULT_WEIGHTS, SIGMOID_K, run_fusion

    session = SyncSessionLocal()
    try:
        match = sync_get_match(session, match_id)
        if not match or not match.duration_sec:
            logger.error("fuse_match: match %s missing or has no duration_sec", match_id)
            return {"match_id": match_id, "fused_cells": 0}

        visual_rows = [_module_prediction_to_dict(r) for r in
                       sync_get_module_predictions_by_match(session, match_id, "visual")]
        commentary_rows = [_module_prediction_to_dict(r) for r in
                            sync_get_module_predictions_by_match(session, match_id, "commentary")]
        audio_rows = [_module_prediction_to_dict(r) for r in
                      sync_get_module_predictions_by_match(session, match_id, "audio")]

        fused_cells = run_fusion(match.duration_sec, visual_rows, commentary_rows, audio_rows,
                                  weights=DEFAULT_WEIGHTS)

        run = sync_create_fusion_run(
            session, match_id,
            weights=DEFAULT_WEIGHTS, grid_sec=4.0, sigmoid_k=SIGMOID_K,
            commentary_lag_sec=settings.COMMENTARY_LAG_SEC,
        )
        sync_bulk_create_fusion_cells(session, str(run.id), match_id, fused_cells)
        sync_update_match_status(session, match_id, "done")

        logger.info("fuse_match: match %s fused into run %s (%d cells)", match_id, run.id, len(fused_cells))
        return {"match_id": match_id, "fusion_run_id": str(run.id), "fused_cells": len(fused_cells)}
    except Exception:
        logger.exception("fuse_match failed for %s", match_id)
        sync_update_match_status(session, match_id, "failed")
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# generate_highlight
# ---------------------------------------------------------------------------

@app.task(name="tasks.tasks.generate_highlight")
def generate_highlight(
    job_id: str, match_id: str, highlight_type: str, requested_events: list[str]
):
    from constants import PROFILES, HighlightType
    from db.crud import sync_bulk_create_highlight_clips
    from fusion import generate_highlight_clips
    from pipeline.assembler import assemble_highlight

    session = SyncSessionLocal()
    try:
        sync_update_highlight_job(session, job_id, status="running")

        match = sync_get_match(session, match_id)
        if not match or not match.duration_sec:
            sync_update_highlight_job(
                session, job_id, status="failed",
                error_message="Match not found or still extracting (no duration yet).",
            )
            return

        result = generate_highlight_clips(match_id, requested_events, highlight_type, match.duration_sec, session)
        clips = result["clips"]

        if not clips:
            sync_update_highlight_job(
                session, job_id,
                status="failed",
                error_message=(
                    "No fusion data yet for this match — processing may still be running."
                    if result["fusion_run_id"] is None else
                    "No clips passed the selection criteria for the requested events."
                ),
            )
            return

        clip_rows = [
            {
                "rank": c["rank"],
                "global_start_sec": c["global_start_sec"],
                "global_end_sec": c["global_end_sec"],
                "duration_sec": c["duration_sec"],
                "event": c["event"],
                "peak_score": c["peak_score"],
                "mean_score": c["mean_score"],
                "source_cell_start": c["source_cell_start"],
                "source_cell_end": c["source_cell_end"],
                "cells": c["cells"],
                "was_expanded": c["was_expanded"],
                "was_trimmed": c["was_trimmed"],
            }
            for c in clips
        ]
        sync_bulk_create_highlight_clips(session, job_id, clip_rows)

        profile = PROFILES[HighlightType(highlight_type)]
        total_duration_sec = sum(c["duration_sec"] for c in clips)
        sync_update_highlight_job(
            session, job_id,
            status="running",
            fusion_run_id=result["fusion_run_id"],
            params=profile,
            total_duration_sec=total_duration_sec,
            clip_count=len(clips),
        )

        original_video_path = str(
            settings.STORAGE_BASE / "raw" / f"{match_id}_{match.filename}"
        )

        output_path = settings.STORAGE_BASE / "outputs" / f"{job_id}_highlight.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        assemble_highlight(
            selected_segments=clips,
            original_video_path=original_video_path,
            output_path=str(output_path),
            total_duration=match.duration_sec,
        )

        sync_update_highlight_job(
            session, job_id,
            status="done",
            output_path=str(output_path),
        )

    except Exception as exc:
        logger.exception("generate_highlight failed for job %s", job_id)
        sync_update_highlight_job(
            session, job_id,
            status="failed",
            error_message=str(exc),
        )
    finally:
        session.close()
