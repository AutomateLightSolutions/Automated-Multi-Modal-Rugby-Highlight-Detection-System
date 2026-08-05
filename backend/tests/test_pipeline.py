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


if __name__ == "__main__":
    print("=" * 55)
    print("Rugby Highlight Generator — Integration Smoke Tests")
    print("=" * 55 + "\n")

    tests = [
        test_probe_video,
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
