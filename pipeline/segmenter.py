"""
Splits a video and its audio into fixed-duration chunks for parallel processing.
Returns a list of dicts with keys: video_chunk_path, audio_chunk_path,
global_start_sec, global_end_sec.
"""
import math
import subprocess
from pathlib import Path


def segment_match(
    video_path: str,
    match_id: str,
    audio_path: str,
    storage_base: Path,
    chunk_duration_sec: int,
) -> list[dict]:
    import json

    # Determine total duration
    probe = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", video_path,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    duration_sec = float(json.loads(probe.stdout)["format"]["duration"])

    video_chunks_dir = storage_base / "chunks" / "video" / match_id
    audio_chunks_dir = storage_base / "chunks" / "audio" / match_id
    video_chunks_dir.mkdir(parents=True, exist_ok=True)
    audio_chunks_dir.mkdir(parents=True, exist_ok=True)

    n_chunks = math.ceil(duration_sec / chunk_duration_sec)
    chunks = []

    for i in range(n_chunks):
        start = i * chunk_duration_sec
        end = min(start + chunk_duration_sec, duration_sec)

        video_chunk = video_chunks_dir / f"chunk_{i:04d}.mp4"
        audio_chunk = audio_chunks_dir / f"chunk_{i:04d}.wav"

        subprocess.run(
            [
                "ffmpeg", "-y", "-ss", str(start), "-t", str(end - start),
                "-i", video_path, "-c", "copy", str(video_chunk),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "ffmpeg", "-y", "-ss", str(start), "-t", str(end - start),
                "-i", audio_path,
                "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                str(audio_chunk),
            ],
            check=True,
            capture_output=True,
        )

        chunks.append(
            {
                "video_chunk_path": str(video_chunk),
                "audio_chunk_path": str(audio_chunk),
                "global_start_sec": start,
                "global_end_sec": end,
            }
        )

    return chunks
