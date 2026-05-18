"""
Extracts frames and audio from a raw video file using FFmpeg.
"""
import json
import subprocess
from pathlib import Path


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
    Extract full audio track from video and probe metadata.

    Returns:
        dict with keys: duration_sec, fps, full_audio_path
    """
    audio_dir = storage_base / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / f"{match_id}_full.wav"

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            str(audio_path),
        ],
        check=True,
        capture_output=True,
    )

    info = probe_video(video_path)

    return {
        "duration_sec": info["duration"],
        "fps": info["fps"],
        "full_audio_path": str(audio_path),
    }
