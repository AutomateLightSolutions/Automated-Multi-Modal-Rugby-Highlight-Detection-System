"""
Rule-based lexicon branch of the commentary hybrid pipeline.

Ported from d:/Test FYP/commentary_analysis_system/src/models/lexicon_model.py.
Categories/terms/weights come from the lexicon.json uploaded via the Models
admin page (backend/weights/commentary/lexicon/lexicon.json) — no hardcoded
keyword table, unlike the legacy RUGBY_KEYWORDS scorer this replaces.
"""
import json
import re

# Negation/qualifier words checked immediately before a keyword match — covers
# near-misses, failed attempts, and preventions common in rugby commentary
# ("no try", "missed the penalty", "held up over the line").
_NEGATIONS = [
    "no", "not", "missed", "missed the",
    "almost", "nearly", "just", "prevented",
    "stopped", "denied", "failed", "attempt",
    "trying to", "going for", "couldn't", "could not",
    "short of", "held up", "short",
]


class LexiconModel:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config: dict = {"categories": []}
        self.load_config()

    def load_config(self) -> None:
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def _count_matches_weighted(self, text: str, terms: list) -> float:
        score = 0.0

        for term_obj in terms:
            if isinstance(term_obj, str):
                term = term_obj
                weight = 1.0
            else:
                term = term_obj.get("text", "")
                weight = float(term_obj.get("weight", 1.0))

            if not term:
                continue

            if "\\" in term:
                pattern = term
            else:
                escaped_term = re.escape(term)
                # Allow common suffixes (e.g. score -> scores, scored, scoring)
                pattern = rf"\b{escaped_term}(?:s|ed|ing|d)?\b"

            for match in re.finditer(pattern, text, re.IGNORECASE):
                start_idx = match.start()
                preceding_text = text[max(0, start_idx - 15):start_idx].lower()

                is_negated = any(preceding_text.strip().endswith(neg) for neg in _NEGATIONS)
                if not is_negated:
                    score += weight

        return score

    def generate_features(self, text: str) -> dict:
        """Weighted per-category keyword-match strength (uncategorized-weight)."""
        text = text.lower()
        features = {}
        for category in self.config.get("categories", []):
            cat_id = category["id"]
            terms = category.get("terms", [])
            features[cat_id] = self._count_matches_weighted(text, terms)
        return features

    def score_chunk(self, text: str) -> float:
        """Overall lexicon excitement score (0.0-1.0), category-weight-scaled."""
        feats = self.generate_features(text)

        raw_score = 0.0
        for category in self.config.get("categories", []):
            cat_id = category["id"]
            weight = category.get("weight", 0.0)
            count = feats.get(cat_id, 0)

            # Term weights are fractional (often < 0.05) — scale up so one
            # solid keyword match (e.g. 0.01) triggers the category fully.
            scaled_count = float(count) * 100.0
            raw_score += min(1.0, scaled_count) * weight

        return min(raw_score, 1.0)
