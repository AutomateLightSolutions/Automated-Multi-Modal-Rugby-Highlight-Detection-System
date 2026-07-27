"""
Celery task definitions for the video processing pipeline.
"""
import logging

from celery import chord, group

from config import settings
from db import SyncSessionLocal
from db.crud import (
    sync_create_module_output,
    sync_create_segment,
    sync_get_match,
    sync_update_highlight_job,
    sync_update_match_status,
)
from tasks.celery_app import app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

@app.task(name="tasks.tasks.no_op_callback")
def no_op_callback(_results):
    """Chord callback that discards module results — fusion runs on demand."""
    pass


# ---------------------------------------------------------------------------
# process_match
# ---------------------------------------------------------------------------

@app.task(bind=True, name="tasks.tasks.process_match")
def process_match(_self, match_id: str, video_path: str):
    from pipeline.extractor import extract_media
    from pipeline.segmenter import segment_match

    session = SyncSessionLocal()
    try:
        # b. Mark as extracting
        sync_update_match_status(session, match_id, "extracting")

        # c. Extract duration, fps, and full audio track
        meta = extract_media(video_path, match_id, settings.STORAGE_BASE)

        # d. Persist extraction metadata
        sync_update_match_status(
            session, match_id, "extracting",
            duration_sec=meta["duration_sec"], fps=meta["fps"],
        )

        # e. Segment into fixed-duration chunks
        # Video chunks are sliced from the visual track (no audio);
        # audio chunks are sliced from the full WAV.
        chunks = segment_match(
            meta["visual_path"], match_id, meta["full_audio_path"],
            settings.STORAGE_BASE, settings.CHUNK_DURATION_SEC,
        )

        # f. Persist each segment and keep a reference for chord dispatch
        segment_chunk_pairs = []
        for chunk in chunks:
            segment = sync_create_segment(
                session,
                match_id=match_id,
                global_start_sec=chunk["global_start_sec"],
                global_end_sec=chunk["global_end_sec"],
                video_chunk_path=chunk["video_chunk_path"],
                audio_chunk_path=chunk["audio_chunk_path"],
            )
            segment_chunk_pairs.append((segment, chunk))

        # g. Mark as processing
        sync_update_match_status(session, match_id, "processing")

        # h. Fire a parallel module chord per segment (no-op callback; fusion is on-demand)
        for segment, chunk in segment_chunk_pairs:
            header = group(
                run_visual_module.signature(
                    (
                        str(segment.id),
                        chunk["video_chunk_path"],
                        chunk["global_start_sec"],
                        chunk["global_end_sec"],
                    ),
                    immutable=True,
                ),
                run_commentary_module.signature(
                    (
                        str(segment.id),
                        chunk["audio_chunk_path"],
                        chunk["global_start_sec"],
                        chunk["global_end_sec"],
                    ),
                    immutable=True,
                ),
                run_audio_energy_module.signature(
                    (
                        str(segment.id),
                        chunk["audio_chunk_path"],
                        chunk["global_start_sec"],
                        chunk["global_end_sec"],
                    ),
                    immutable=True,
                ),
            )
            chord(header)(no_op_callback.s())

        # i. All chunks dispatched — mark match done
        sync_update_match_status(session, match_id, "done")

    except Exception:
        logger.exception("process_match failed for %s", match_id)
        sync_update_match_status(session, match_id, "failed")
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Module tasks
# ---------------------------------------------------------------------------

@app.task(name="tasks.tasks.run_visual_module")
def run_visual_module(
    segment_id: str,
    video_path: str,
    global_start_sec: float,
    global_end_sec: float,
) -> dict:
    from modules.visual.inference import run_inference

    result = run_inference(video_path, global_start_sec, global_end_sec)

    session = SyncSessionLocal()
    try:
        sync_create_module_output(
            session,
            segment_id=segment_id,
            module_name="visual",
            confidence=result["confidence"],
            event_type=result["event_type"],
            event_confidence=result["event_confidence"],
            extra_data=result["extra_data"],
        )
    finally:
        session.close()

    return {"segment_id": segment_id, "module": "visual", "confidence": result["confidence"]}


@app.task(name="tasks.tasks.run_commentary_module")
def run_commentary_module(
    segment_id: str,
    audio_path: str,
    global_start_sec: float,
    global_end_sec: float,
) -> dict:
    from modules.commentary.scorer import run_inference

    result = run_inference(audio_path, global_start_sec, global_end_sec)

    session = SyncSessionLocal()
    try:
        sync_create_module_output(
            session,
            segment_id=segment_id,
            module_name="commentary",
            confidence=result["confidence"],
            event_type=result["event_type"],
            event_confidence=None,
            extra_data=result["extra_data"],
        )
    finally:
        session.close()

    return {"segment_id": segment_id, "module": "commentary", "confidence": result["confidence"]}


@app.task(name="tasks.tasks.run_audio_energy_module")
def run_audio_energy_module(
    segment_id: str,
    audio_path: str,
    global_start_sec: float,
    global_end_sec: float,
) -> dict:
    from modules.audio_energy.scorer import run_inference

    result = run_inference(audio_path, global_start_sec, global_end_sec)

    session = SyncSessionLocal()
    try:
        sync_create_module_output(
            session,
            segment_id=segment_id,
            module_name="audio_energy",
            confidence=result["confidence"],
            event_type=None,
            event_confidence=None,
            extra_data=result["extra_data"],
        )
    finally:
        session.close()

    return {"segment_id": segment_id, "module": "audio_energy", "confidence": result["confidence"]}


# ---------------------------------------------------------------------------
# generate_highlight
# ---------------------------------------------------------------------------

@app.task(name="tasks.tasks.generate_highlight")
def generate_highlight(
    job_id: str, match_id: str, highlight_type: str, requested_events: list[str]
):
    from fusion import run_fusion_pipeline
    from pipeline.assembler import assemble_highlight

    session = SyncSessionLocal()
    try:
        sync_update_highlight_job(session, job_id, status="running")

        selected_segments = run_fusion_pipeline(
            match_id, job_id, requested_events, highlight_type, session
        )

        if not selected_segments:
            sync_update_highlight_job(
                session, job_id,
                status="failed",
                error_message="No segments passed the selection criteria.",
            )
            return

        match = sync_get_match(session, match_id)
        original_video_path = str(
            settings.STORAGE_BASE / "raw" / f"{match_id}_{match.filename}"
        )

        output_path = settings.STORAGE_BASE / "outputs" / f"{job_id}_highlight.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        assemble_highlight(
            selected_segments=selected_segments,
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
