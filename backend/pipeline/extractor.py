"""
Extracts frames and audio from a raw video file using FFmpeg.
"""
import json
import subprocess
from pathlib import Path

# Both extracted tracks are cut from the same uploaded file, but ffmpeg's
# "-c:v copy" can snap to the nearest keyframe and stream durations can be
# reported slightly differently per codec — this is the max drift we tolerate
# before treating it as a real mismatch (which would make every downstream
# absolute timestamp wrong).
MAX_AUDIO_VIDEO_DRIFT_SEC = 0.5


def _probe_duration_sec(media_path: str) -> float:
    """Return the container duration (seconds) of any media file via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", media_path,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def probe_video(video_path: str) -> dict:
    """
    Return basic metadata for a video file.

    Returns:
        dict with keys: duration (float, seconds), fps (float),
        has_audio (bool), width (int), height (int)
    """
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", video_path,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    info = json.loads(result.stdout)

    duration = float(info["format"]["duration"])
    fps = 25.0
    width = 0
    height = 0
    has_audio = False

    for stream in info.get("streams", []):
        codec_type = stream.get("codec_type")
        if codec_type == "video":
            num, den = stream.get("avg_frame_rate", "25/1").split("/")
            if int(den) > 0:
                fps = int(num) / int(den)
            width = stream.get("width", 0)
            height = stream.get("height", 0)
        elif codec_type == "audio":
            has_audio = True

    return {
        "duration": duration,
        "fps": fps,
        "has_audio": has_audio,
        "width": width,
        "height": height,
    }


def extract_media(
    video_path: str,
    match_id: str,
    storage_base: Path,
) -> dict:
    """
    Extract full audio track and visual frames from video and probe metadata.

    Returns:
        dict with keys: duration_sec, fps, full_audio_path, visual_frames_dir
    """
    # --- Audio extraction ---
    audio_dir = storage_base / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / f"{match_id}_full.wav"

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", video_path,
            # 22050 Hz, not 16000 — the audio_energy models need real content
            # up to ~11kHz (spectral_contrast's top band lands right there;
            # at 16000 Hz that band is past the 8kHz Nyquist limit and just
            # measures resampling noise). Whisper doesn't need this file at
            # 16000 either — it resamples internally regardless of input rate.
            "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1",
            str(audio_path),
        ],
        check=True,
        capture_output=True,
    )

    # --- Visual track extraction (video only, no audio) ---
    visual_dir = storage_base / "visual"
    visual_dir.mkdir(parents=True, exist_ok=True)
    visual_path = visual_dir / f"{match_id}_visual.mp4"

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", video_path,
            "-an",        # strip audio stream
            "-c:v", "copy",  # copy video codec — no re-encoding, fast
            str(visual_path),
        ],
        check=True,
        capture_output=True,
    )

    info = probe_video(video_path)

    # Same-source timebase check: both tracks were cut from `video_path` above,
    # but verify the *resulting files* actually agree before anything downstream
    # (tiling, fusion) trusts their timestamps as interchangeable.
    video_duration = _probe_duration_sec(str(visual_path))
    audio_duration = _probe_duration_sec(str(audio_path))
    audio_offset_sec = audio_duration - video_duration
    if abs(audio_offset_sec) > MAX_AUDIO_VIDEO_DRIFT_SEC:
        raise RuntimeError(
            f"Audio/video duration mismatch for match {match_id}: "
            f"video={video_duration:.3f}s audio={audio_duration:.3f}s "
            f"(diff={audio_offset_sec:.3f}s, tolerance={MAX_AUDIO_VIDEO_DRIFT_SEC}s). "
            f"Both tracks must be extracted from the same untrimmed upload — "
            f"every absolute timestamp downstream would otherwise be wrong."
        )

    return {
        "duration_sec": info["duration"],
        "fps": info["fps"],
        "full_audio_path": str(audio_path),
        "visual_path": str(visual_path),
        "audio_offset_sec": audio_offset_sec,
    }
