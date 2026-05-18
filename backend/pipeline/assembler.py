"""
Assembles the final highlight video from selected segments.
Re-cuts clips from the ORIGINAL full match video (not the chunks)
for best quality. Adds padding around each segment. Concatenates
in chronological order using FFmpeg concat demuxer.
"""

import subprocess
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PADDING_SEC = 2.0  # seconds added before and after each selected segment


def assemble_highlight(selected_segments: list[dict],
                       original_video_path: str,
                       output_path: str,
                       padding_sec: float = PADDING_SEC,
                       total_duration: float = None) -> str:
    """
    Build the highlight video from selected segments.

    Args:
        selected_segments: chronologically sorted list of segment dicts.
            Each must have: global_start_sec, global_end_sec, rank
        original_video_path: path to the full match video
        output_path: where to write the final highlight .mp4
        padding_sec: seconds of context to add around each segment
        total_duration: total match duration (for clamping end padding)

    Returns:
        output_path on success. Raises RuntimeError on FFmpeg failure.
    """
    if not selected_segments:
        raise ValueError("No segments provided to assemble_highlight.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        clip_paths = []

        for idx, segment in enumerate(selected_segments):
            padded_start = max(0.0, segment["global_start_sec"] - padding_sec)
            padded_end = segment["global_end_sec"] + padding_sec
            if total_duration:
                padded_end = min(padded_end, total_duration)

            clip_path = str(tmp_path / f"clip_{idx:04d}.mp4")

            _cut_clip(
                original_video_path,
                padded_start,
                padded_end - padded_start,
                clip_path,
            )
            clip_paths.append(clip_path)
            logger.info(
                "Cut clip %d/%d: %.1fs - %.1fs (rank=%s)",
                idx + 1, len(selected_segments),
                padded_start, padded_end,
                segment.get("rank"),
            )

        concat_list_path = str(tmp_path / "concat_list.txt")
        with open(concat_list_path, "w") as f:
            for clip_path in clip_paths:
                f.write(f"file '{clip_path}'\n")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        _concat_clips(concat_list_path, output_path)

    logger.info("Highlight assembled: %s", output_path)
    return output_path


def _cut_clip(input_path: str, start_sec: float,
              duration: float, output_path: str):
    """Cut a single clip from the source video with re-encoding."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-i", input_path,
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-avoid_negative_ts", "make_zero",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg clip cut failed at {start_sec}s: {result.stderr[-500:]}"
        )


def _concat_clips(concat_list_path: str, output_path: str):
    """Concatenate clips using FFmpeg concat demuxer."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg concat failed: {result.stderr[-500:]}"
        )
