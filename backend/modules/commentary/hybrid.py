"""
Combines the ML branch (modules.commentary.model) and lexicon branch
(modules.commentary.lexicon) into one per-chunk prediction.

Ported from d:/Test FYP/commentary_analysis_system/src/models/hybrid_model.py
(HybridModel.predict), adapted to operate on pre-tokenized grid chunks
(modules.commentary.chunking.build_grid_chunks) and to always clamp the
event-selection score to [0, 1] before it's used as event_confidence — the
raw weighted-sum formula (roberta_prob + lexicon_prob*weight, weights not
normalized to sum to 1) can exceed 1.0, which is fine as an internal ranking
signal but not as a "confidence" fed into fusion.
"""
import torch

from modules.commentary.model import predict_probs

# Booster-formula weights (roberta term is never down-weighted; the lexicon
# term only ever boosts it). Kept as module-level constants — same pattern
# as modules/visual/merge.py::SCORE_WEIGHTS — rather than a settings file.
ROBERTA_WEIGHT = 1.0
HIGHLIGHT_LEXICON_WEIGHT = 0.75
EVENT_LEXICON_WEIGHT = 0.35


def _empty_result() -> dict:
    """Result for a grid cell with no transcribed words (silence)."""
    return {
        "predicted_event": "normal_play",
        "event_confidence": 1.0,
        "highlight_score": 0.0,
        "extra": {"roberta_score": 0.0, "lexicon_score": 0.0, "predicted_event_prob_raw": 0.0},
    }


def _combine(text: str, r_probs: list[float], r_h_score: float, id2label: dict, lexicon) -> dict:
    l_prob = lexicon.score_chunk(text)
    hybrid_score = min(1.0, (r_h_score * ROBERTA_WEIGHT) + (l_prob * HIGHLIGHT_LEXICON_WEIGHT))

    lexicon_features = lexicon.generate_features(text)

    max_hybrid_prob = -1.0
    predicted_event_id = 0
    for i, p in enumerate(r_probs):
        event_name = id2label.get(i, "normal_play")
        l_for_event = lexicon_features.get(event_name, 0.0)
        l_normalized = min(1.0, float(l_for_event) * 100.0)

        event_hybrid_prob = (p * ROBERTA_WEIGHT) + (l_normalized * EVENT_LEXICON_WEIGHT)
        if event_hybrid_prob > max_hybrid_prob:
            max_hybrid_prob = event_hybrid_prob
            predicted_event_id = i

    predicted_event = id2label.get(predicted_event_id, "normal_play")

    return {
        "predicted_event": predicted_event,
        "event_confidence": round(min(1.0, max(0.0, max_hybrid_prob)), 4),
        "highlight_score": round(hybrid_score, 4),
        "extra": {
            "roberta_score": round(float(r_h_score), 4),
            "lexicon_score": round(l_prob, 4),
            "predicted_event_prob_raw": round(max_hybrid_prob, 4),
        },
    }


def predict_chunks(
    chunks: list[dict], model, tokenizer, id2label: dict, lexicon, device: torch.device,
) -> list[dict]:
    """
    Args:
        chunks: from chunking.build_grid_chunks — one dict per grid cell,
            each with "text_clean" (may be empty for silent cells).

    Returns:
        One result dict per chunk, same order, each with
        {"predicted_event", "event_confidence", "highlight_score", "extra"}.
    """
    non_empty_idx = [i for i, c in enumerate(chunks) if c["text_clean"]]
    texts = [chunks[i]["text_clean"] for i in non_empty_idx]

    if texts:
        event_probs_list, highlight_scores_list = predict_probs(model, tokenizer, texts, device)
    else:
        event_probs_list, highlight_scores_list = [], []

    results: list[dict | None] = [None] * len(chunks)
    for pos, i in enumerate(non_empty_idx):
        results[i] = _combine(
            chunks[i]["text_clean"], event_probs_list[pos], highlight_scores_list[pos], id2label, lexicon,
        )

    for i, result in enumerate(results):
        if result is None:
            results[i] = _empty_result()

    return results
