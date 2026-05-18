"""
Command-line interface for local testing without running the full
Docker stack. Useful for testing individual pipeline stages.
"""

import argparse
import sys


def cmd_health(args):
    """Check DB and Redis connectivity."""
    print("Checking system health...\n")

    try:
        from config import settings
        import sqlalchemy
        engine = sqlalchemy.create_engine(settings.SYNC_DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        print("[OK] PostgreSQL: connected")
    except Exception as e:
        print(f"[FAIL] PostgreSQL: {e}")

    try:
        import redis
        from config import settings
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        print("[OK] Redis: connected")
    except Exception as e:
        print(f"[FAIL] Redis: {e}")


def cmd_process(args):
    """
    Run extraction and segmentation locally without Celery.
    Useful for verifying the timeline is correct before full run.
    """
    from config import settings
    from pipeline.extractor import extract_media
    from pipeline.segmenter import segment_match
    import uuid

    match_id = str(uuid.uuid4())
    video_path = args.video
    output_base = settings.STORAGE_BASE

    print(f"\nProcessing: {video_path}")
    print(f"Match ID:   {match_id}\n")

    print("Step 1: Extracting media metadata...")
    meta = extract_media(video_path, match_id, output_base)
    print(f"  Duration: {meta['duration_sec']:.2f}s")
    print(f"  FPS:      {meta['fps']:.2f}")
    print(f"  Audio:    {meta['full_audio_path']}")

    print("\nStep 2: Segmenting into chunks...")
    chunks = segment_match(
        video_path, match_id,
        meta["full_audio_path"],
        output_base,
        chunk_duration=30,
    )

    print(f"\n{'Chunk':<8} {'Start':>10} {'End':>10} {'PTS':>10} {'Drift':>8}")
    print("-" * 50)
    for c in chunks:
        drift = abs(c["pts_offset"] - c["global_start_sec"])
        flag = " ⚠" if drift > 0.5 else ""
        print(
            f"{c['chunk_index']:<8} "
            f"{c['global_start_sec']:>10.2f} "
            f"{c['global_end_sec']:>10.2f} "
            f"{c['pts_offset']:>10.3f} "
            f"{drift:>8.3f}{flag}"
        )

    print(f"\nTotal chunks: {len(chunks)}")


def cmd_test_modules(args):
    """
    Run all three module stubs on a single chunk and show fusion score.
    """
    from modules.visual.inference import run_inference as visual_inference
    from modules.commentary.scorer import run_inference as commentary_inference
    from modules.audio_energy.scorer import run_inference as audio_inference
    from fusion.aligner import align_module_outputs
    from fusion.scorer import compute_fused_score

    start = float(args.start)
    end = float(args.end)

    print(f"\nTesting modules on chunk: {start}s - {end}s\n")

    print("Running visual module...")
    v = visual_inference(args.chunk_video, start, end)
    print(f"  confidence:       {v['confidence']}")
    print(f"  event_type:       {v['event_type']}")
    print(f"  event_confidence: {v['event_confidence']}")

    print("\nRunning commentary module...")
    c = commentary_inference(args.chunk_audio, start, end)
    print(f"  confidence:   {c['confidence']}")
    print(f"  event_type:   {c['event_type']}")
    print(f"  keywords:     {c['extra_data'].get('keywords_found')}")

    print("\nRunning audio energy module...")
    a = audio_inference(args.chunk_audio, start, end)
    print(f"  confidence:    {a['confidence']}")
    print(f"  peak_rms:      {a['extra_data']['peak_rms']}")
    print(f"  peak_time:     {a['extra_data']['peak_time_global_sec']}s")

    print("\nRunning fusion...")
    aligned = align_module_outputs("test_segment", [v, c, a])
    fused = compute_fused_score(aligned)
    print(f"  Fused score:  {fused}")
    print(f"  Verdict:      {'HIGHLIGHT' if fused >= 0.5 else 'not highlight'}")


def main():
    parser = argparse.ArgumentParser(
        description="Rugby Highlight Generator CLI"
    )
    subparsers = parser.add_subparsers(dest="command")

    # health
    subparsers.add_parser("health", help="Check DB and Redis connectivity")

    # process
    p_process = subparsers.add_parser(
        "process", help="Extract and segment a match video locally"
    )
    p_process.add_argument("--video", required=True,
                            help="Path to full match .mp4 file")

    # test-modules
    p_test = subparsers.add_parser(
        "test-modules", help="Run all three modules on a single chunk"
    )
    p_test.add_argument("--chunk-video", required=True)
    p_test.add_argument("--chunk-audio", required=True)
    p_test.add_argument("--start", required=True, type=float)
    p_test.add_argument("--end", required=True, type=float)

    args = parser.parse_args()

    if args.command == "health":
        cmd_health(args)
    elif args.command == "process":
        cmd_process(args)
    elif args.command == "test-modules":
        cmd_test_modules(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
