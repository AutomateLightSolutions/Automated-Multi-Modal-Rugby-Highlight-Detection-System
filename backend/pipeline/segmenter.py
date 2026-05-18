"""
Splits a video and its audio into fixed-duration chunks for parallel processing.
Returns a list of dicts with keys: chunk_index, video_chunk_path, audio_chunk_path,
global_start_sec, global_end_sec, pts_offset.
"""
import json
import math
import subprocess
from pathlib import Path


def _probe_chunk_start(video_path: str) -> float:
    """Return the PTS start time of the first video frame in a chunk file."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-select_streams", "v:0", video_path,
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return 0.0
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if streams:
        return float(streams[0].get("start_time", 0.0))
    return 0.0


def segment_match(
    video_path: str,
    match_id: str,
    audio_path: str,
    storage_base: Path,
    chunk_duration: int,
) -> list[dict]:
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

    n_chunks = math.ceil(duration_sec / chunk_duration)
    chunks = []

    for i in range(n_chunks):
        start = i * chunk_duration
        end = min(start + chunk_duration, duration_sec)

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

        # Actual PTS of first frame = requested start + chunk's internal start_time.
        # With input seeking (-ss before -i) and -c copy, start_time is typically ~0.
        chunk_pts_start = _probe_chunk_start(str(video_chunk))
        pts_offset = start + chunk_pts_start

        chunks.append(
            {
                "chunk_index": i,
                "video_chunk_path": str(video_chunk),
                "audio_chunk_path": str(audio_chunk),
                "global_start_sec": float(start),
                "global_end_sec": float(end),
                "pts_offset": pts_offset,
            }
        )

    return chunks
