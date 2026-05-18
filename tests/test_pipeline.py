"""
Integration smoke tests for the core pipeline.
Run with: python tests/test_pipeline.py
No pytest required — plain assertions.
Requires FFmpeg installed on the system.
"""

import sys
import subprocess
import tempfile
from pathlib import Path


def create_dummy_video(output_path: str, duration_sec: int = 5):
    """Create a minimal test video using FFmpeg lavfi source."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=blue:size=320x240:rate=25:duration={duration_sec}",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={duration_sec}",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac",
        "-t", str(duration_sec),
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Could not create dummy video: {result.stderr}")


def test_probe_video():
    """Test that probe_video returns correct metadata."""
    print("TEST: probe_video...")
    from pipeline.extractor import probe_video

    with tempfile.TemporaryDirectory() as tmp:
        video_path = str(Path(tmp) / "test.mp4")
        create_dummy_video(video_path, duration_sec=5)

        info = probe_video(video_path)
        assert "duration" in info, "Missing duration"
        assert "fps" in info, "Missing fps"
        assert abs(info["duration"] - 5.0) < 0.5, \
            f"Duration mismatch: {info['duration']}"
        assert info["fps"] > 0, "FPS must be positive"
        assert info["has_audio"] is True, "Should detect audio"

    print("  PASS: probe_video\n")


def test_segmentation_timeline_integrity():
    """
    CRITICAL TEST: Verifies master timeline correctness.
    global_start_sec must equal chunk_index × chunk_duration.
    PTS drift must be within 0.5s of computed start.
    """
    print("TEST: segmentation timeline integrity...")
    from pipeline.extractor import extract_media
    from pipeline.segmenter import segment_match
    import uuid

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        video_path = str(tmp_path / "test_match.mp4")
        create_dummy_video(video_path, duration_sec=6)

        match_id = str(uuid.uuid4())
        meta = extract_media(video_path, match_id, tmp_path)
        chunks = segment_match(
            video_path, match_id,
            meta["full_audio_path"],
            tmp_path,
            chunk_duration=2,
        )

        assert len(chunks) == 3, \
            f"Expected 3 chunks for 6s video with 2s chunks, got {len(chunks)}"

        for i, chunk in enumerate(chunks):
            expected_start = i * 2.0
            assert abs(chunk["global_start_sec"] - expected_start) < 0.01, \
                f"Chunk {i}: global_start_sec={chunk['global_start_sec']} " \
                f"expected {expected_start}"
            assert Path(chunk["video_chunk_path"]).exists(), \
                f"Video chunk file missing: {chunk['video_chunk_path']}"
            assert Path(chunk["audio_chunk_path"]).exists(), \
                f"Audio chunk file missing: {chunk['audio_chunk_path']}"
            drift = abs(chunk["pts_offset"] - chunk["global_start_sec"])
            assert drift < 0.5, \
                f"Chunk {i}: PTS drift too large: {drift:.3f}s"

        starts = [c["global_start_sec"] for c in chunks]
        assert starts == sorted(starts), "Chunks not in chronological order"

    print("  PASS: segmentation timeline integrity\n")


def test_fusion_scorer():
    """Test fusion score is in valid range and weighted correctly."""
    print("TEST: fusion scorer...")
    from fusion.scorer import compute_fused_score

    aligned = {
        "visual":       {"confidence": 0.9, "event_type": "try",
                         "event_confidence": 0.88},
        "commentary":   {"confidence": 0.6, "event_type": "try",
                         "event_confidence": None},
        "audio_energy": {"confidence": 0.3, "event_type": None,
                         "event_confidence": None},
    }
    score = compute_fused_score(aligned)
    assert 0.0 <= score <= 1.0, f"Score out of range: {score}"
    assert score > 0.5, f"High-confidence segment should score > 0.5, got {score}"

    zero_aligned = {
        "visual":       {"confidence": 0.0, "event_type": None,
                         "event_confidence": None},
        "commentary":   {"confidence": 0.0, "event_type": None,
                         "event_confidence": None},
        "audio_energy": {"confidence": 0.0, "event_type": None,
                         "event_confidence": None},
    }
    zero_score = compute_fused_score(zero_aligned)
    assert zero_score < 0.5, \
        f"All-zero segment should score < 0.5, got {zero_score}"

    print("  PASS: fusion scorer\n")


def test_nms_selector():
    """Test NMS suppresses overlapping segments correctly."""
    print("TEST: NMS selector...")
    from fusion.selector import select_segments
    import uuid

    segments = [
        {"segment_id": str(uuid.uuid4()), "global_start_sec": 0,
         "global_end_sec": 30, "fused_confidence": 0.9,
         "visual_event_type": "try", "visual_event_confidence": 0.9},
        {"segment_id": str(uuid.uuid4()), "global_start_sec": 10,
         "global_end_sec": 40, "fused_confidence": 0.7,
         "visual_event_type": None, "visual_event_confidence": None},
        {"segment_id": str(uuid.uuid4()), "global_start_sec": 12,
         "global_end_sec": 42, "fused_confidence": 0.85,
         "visual_event_type": "scrum", "visual_event_confidence": 0.75},
        {"segment_id": str(uuid.uuid4()), "global_start_sec": 100,
         "global_end_sec": 130, "fused_confidence": 0.6,
         "visual_event_type": None, "visual_event_confidence": None},
        {"segment_id": str(uuid.uuid4()), "global_start_sec": 105,
         "global_end_sec": 135, "fused_confidence": 0.8,
         "visual_event_type": "lineout", "visual_event_confidence": 0.65},
    ]

    selected = select_segments(segments, top_n=10, min_gap_sec=5.0)

    # Segments in the 0-42s cluster: winner is t=0 (conf 0.9).
    # t=10 (conf 0.7) and t=12 (conf 0.85) overlap with t=0 → suppressed.
    # Segments in the 100-135s cluster: winner is t=105 (conf 0.8).
    # t=100 (conf 0.6) overlaps with t=105 → suppressed.
    # Expected selections: t=0, t=105 → 2 segments.
    assert len(selected) == 2, \
        f"Expected 2 segments after NMS, got {len(selected)}"

    starts = [s["global_start_sec"] for s in selected]
    assert starts == sorted(starts), \
        "Selected segments must be in chronological order"

    for seg in selected:
        assert "rank" in seg, "rank field missing from selected segment"

    print("  PASS: NMS selector\n")


def test_user_filter():
    """Test event filter keeps only matching segments."""
    print("TEST: user filter...")
    from fusion.filter import apply_user_filter
    import uuid

    segments = [
        {"segment_id": str(uuid.uuid4()), "global_start_sec": 0,
         "fused_confidence": 0.9, "visual_event_type": "scrum",
         "visual_event_confidence": 0.85},
        {"segment_id": str(uuid.uuid4()), "global_start_sec": 30,
         "fused_confidence": 0.7, "visual_event_type": "try",
         "visual_event_confidence": 0.90},
        {"segment_id": str(uuid.uuid4()), "global_start_sec": 60,
         "fused_confidence": 0.6, "visual_event_type": None,
         "visual_event_confidence": None},
    ]

    scrum_filtered = apply_user_filter(segments, "scrums only")
    assert len(scrum_filtered) == 1, \
        f"Expected 1 scrum segment, got {len(scrum_filtered)}"
    assert scrum_filtered[0]["visual_event_type"] == "scrum"

    all_segments = apply_user_filter(segments, "magic moments")
    assert len(all_segments) == 3, \
        "Unknown filter should return all segments"

    none_filter = apply_user_filter(segments, None)
    assert len(none_filter) == 3

    print("  PASS: user filter\n")


def test_module_output_contract():
    """Verify all three module stubs return correct dict structure."""
    print("TEST: module output contract...")
    from modules.visual.inference import run_inference as v_infer
    from modules.commentary.scorer import run_inference as c_infer
    from modules.audio_energy.scorer import run_inference as a_infer

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = str(Path(tmp) / "test.wav")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "sine=frequency=440:duration=5",
            "-ar", "16000", "-ac", "1", audio_path,
        ], capture_output=True)

        video_path = str(Path(tmp) / "test.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "color=c=red:size=320x240:rate=25:duration=5",
            "-c:v", "libx264", "-preset", "ultrafast", video_path,
        ], capture_output=True)

        required_keys = {
            "module", "global_start_sec", "global_end_sec",
            "confidence", "event_type", "event_confidence", "extra_data",
        }

        for name, fn, vpath, apath in [
            ("visual", v_infer, video_path, None),
            ("commentary", c_infer, None, audio_path),
            ("audio_energy", a_infer, None, audio_path),
        ]:
            if name == "visual":
                result = fn(vpath, 0.0, 5.0)
            else:
                result = fn(apath, 0.0, 5.0)

            missing = required_keys - set(result.keys())
            assert not missing, \
                f"{name} module missing keys: {missing}"
            assert 0.0 <= result["confidence"] <= 1.0, \
                f"{name} confidence out of range: {result['confidence']}"
            if name != "visual":
                assert result["event_confidence"] is None, \
                    f"{name} must have event_confidence=None"

    print("  PASS: module output contract\n")


if __name__ == "__main__":
    print("=" * 55)
    print("Rugby Highlight Generator — Integration Smoke Tests")
    print("=" * 55 + "\n")

    tests = [
        test_probe_video,
        test_segmentation_timeline_integrity,
        test_fusion_scorer,
        test_nms_selector,
        test_user_filter,
        test_module_output_contract,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {test_fn.__name__}: {e}\n")
            failed += 1

    print("=" * 55)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 55)
    if failed > 0:
        sys.exit(1)
