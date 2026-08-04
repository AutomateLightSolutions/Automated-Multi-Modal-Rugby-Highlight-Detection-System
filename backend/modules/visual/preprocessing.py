"""
Frame sampling and tensor preprocessing for SlowFast clips.

Samples frames directly from the video-only track via PyAV (seek + decode) —
deliberately avoids writing ~thousands of physical clip files per match,
which an FFmpeg-cut-per-window approach would require.
"""
import cv2
import numpy as np
import torch

SLOW_NUM_FRAMES = 8
FAST_NUM_FRAMES = 32
FRAME_SIZE = 224
# NOT ImageNet stats — these are the stats this checkpoint was trained with.
NORM_MEAN = (0.45, 0.45, 0.45)
NORM_STD = (0.225, 0.225, 0.225)


def decode_clip_frames(video_path: str, start_sec: float, end_sec: float) -> list[np.ndarray]:
    """Decode all frames whose timestamp falls in [start_sec, end_sec) via PyAV seek+decode.

    Returns a list of RGB uint8 ndarrays (H, W, 3), in presentation order.
    """
    import av

    frames: list[np.ndarray] = []
    container = av.open(video_path)
    try:
        stream = container.streams.video[0]
        # Seek to the nearest keyframe at/before start_sec, then decode forward —
        # PyAV seeking is keyframe-granular, so we filter by actual timestamp below.
        seek_offset = max(0, int(start_sec * av.time_base))
        container.seek(seek_offset, any_frame=False, backward=True, stream=None)

        for frame in container.decode(stream):
            if frame.pts is None:
                continue
            t = float(frame.pts * stream.time_base)
            if t < start_sec:
                continue
            if t >= end_sec:
                break
            frames.append(frame.to_ndarray(format="rgb24"))
    finally:
        container.close()

    return frames


def _sample_with_padding(frames: list[np.ndarray], n_samples: int) -> list[np.ndarray]:
    """Uniformly sample n_samples frames from `frames`. Pads by repeating the
    last frame if there are fewer available frames than requested."""
    if not frames:
        # Degenerate case (e.g. a clip clamped to zero width at t=0): emit black frames.
        return [np.zeros((FRAME_SIZE, FRAME_SIZE, 3), dtype=np.uint8) for _ in range(n_samples)]

    if len(frames) >= n_samples:
        indices = np.linspace(0, len(frames) - 1, n_samples).round().astype(int)
        return [frames[i] for i in indices]

    # Fewer frames than needed — use them all, then repeat the last one.
    padded = list(frames) + [frames[-1]] * (n_samples - len(frames))
    return padded


def _to_tensor(frames: list[np.ndarray]) -> torch.Tensor:
    """(list of (H,W,3) uint8 RGB) -> normalized (C, T, H, W) float32 tensor."""
    mean = np.array(NORM_MEAN, dtype=np.float32)
    std = np.array(NORM_STD, dtype=np.float32)

    processed = []
    for frame in frames:
        resized = cv2.resize(frame, (FRAME_SIZE, FRAME_SIZE), interpolation=cv2.INTER_LINEAR)
        normalized = (resized.astype(np.float32) / 255.0 - mean) / std
        processed.append(normalized)

    stacked = np.stack(processed, axis=0)          # (T, H, W, C)
    chw = np.transpose(stacked, (3, 0, 1, 2))       # (C, T, H, W)
    return torch.from_numpy(chw).float()


def build_pathway_tensors(video_path: str, start_sec: float, end_sec: float) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Decode [start_sec, end_sec) once, then derive both SlowFast pathways from
    the same decoded frames.

    Returns:
        (slow, fast): batched tensors, slow (1,3,8,224,224), fast (1,3,32,224,224).
    """
    frames = decode_clip_frames(video_path, start_sec, end_sec)

    slow_frames = _sample_with_padding(frames, SLOW_NUM_FRAMES)
    fast_frames = _sample_with_padding(frames, FAST_NUM_FRAMES)

    slow = _to_tensor(slow_frames).unsqueeze(0)  # (1, 3, 8, 224, 224)
    fast = _to_tensor(fast_frames).unsqueeze(0)  # (1, 3, 32, 224, 224)
    return slow, fast
