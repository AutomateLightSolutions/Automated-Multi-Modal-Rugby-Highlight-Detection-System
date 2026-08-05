"""
Builds one text chunk per cell of the shared 4s master fusion grid
(modules.grid.compute_grid_cells) — the ML+lexicon hybrid pipeline's
equivalent of TestFYP's `create_chunks(..., overlap=0)`.

Unlike TestFYP's chunker, compute_grid_cells() already clamps the final
cell to the clip's actual duration_sec instead of overrunning it, and this
function always emits one entry per grid cell (even silent ones with empty
text) so every cell has a module_predictions row, matching how the rest of
the pipeline (visual tiles, audio windows) covers the whole match.
"""
from modules.grid import compute_grid_cells
from modules.commentary.text_clean import clean_text


def build_grid_chunks(words: list[dict], duration_sec: float) -> list[dict]:
    """
    Args:
        words: word dicts from asr.transcribe_match(), each with "word"
            (already lowercased/stripped) and absolute-time "start"/"end".
        duration_sec: match/clip duration in seconds.

    Returns:
        One dict per grid cell, in cell order:
        {"cell_index", "start_sec", "end_sec", "is_partial", "text_raw", "text_clean"}
    """
    cells = compute_grid_cells(duration_sec)

    chunks = []
    for cell in cells:
        start, end = cell["start_sec"], cell["end_sec"]
        words_in_cell = [w["word"] for w in words if start <= w["start"] < end]
        text_raw = " ".join(words_in_cell).strip()

        chunks.append({
            "cell_index": cell["cell_index"],
            "start_sec": start,
            "end_sec": end,
            "is_partial": cell["is_partial"],
            "text_raw": text_raw,
            "text_clean": clean_text(text_raw) if text_raw else "",
        })

    return chunks
