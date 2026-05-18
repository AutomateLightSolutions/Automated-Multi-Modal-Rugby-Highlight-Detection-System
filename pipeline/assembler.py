"""
Assembles selected highlight segments into a final output video using FFmpeg concat.
"""
import subprocess
import tempfile
from pathlib import Path


def assemble_highlight(selected_segments, output_path: str) -> None:
    """
    Concatenate video chunks from selected_segments into output_path.
    selected_segments: list of Segment ORM objects with a video_chunk_path attribute,
                       or dicts with key "video_chunk_path".
    """
    def get_path(seg):
        if hasattr(seg, "video_chunk_path"):
            return seg.video_chunk_path
        return seg["video_chunk_path"]

    paths = [get_path(s) for s in selected_segments]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as flist:
        for p in paths:
            flist.write(f"file '{p}'\n")
        concat_file = flist.name

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path,
        ],
        check=True,
        capture_output=True,
    )

    Path(concat_file).unlink(missing_ok=True)
