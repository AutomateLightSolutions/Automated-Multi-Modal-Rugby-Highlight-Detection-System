"""
Extracts frames and audio from a raw video file using FFmpeg.
Returns (duration_sec, fps, full_audio_path).
"""
import subprocess
from pathlib import Path


def extract_media(
    video_path: str,
    match_id: str,
    storage_base: Path,
) -> tuple[float, float, str]:
    audio_dir = storage_base / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / f"{match_id}_full.wav"

    # Extract full audio track
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            str(audio_path),
        ],
        check=True,
        capture_output=True,
    )

    # Probe duration and fps
    import json
    probe = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", video_path,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    info = json.loads(probe.stdout)

    duration_sec = float(info["format"]["duration"])

    fps = 25.0  # fallback
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video":
            num, den = stream["avg_frame_rate"].split("/")
            if int(den) > 0:
                fps = int(num) / int(den)
            break

    return duration_sec, fps, str(audio_path)
