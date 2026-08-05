"""
Whisper transcript text cleaning for the commentary ML+lexicon pipeline.

Ported from d:/Test FYP/commentary_analysis_system/src/data_processing/parser.py
(clean_text / apply_rugby_corrections / RUGBY_CORRECTIONS) — the same cleaning
rules the uploaded model and lexicon were trained/tuned against, so text
handed to them at inference time must match exactly.
"""
import re

# Maps common Whisper misrecognitions -> correct rugby terms.
# Keys are lowercase, matched as whole words before punctuation is stripped.
RUGBY_CORRECTIONS = {
    # Scoring
    "tries": "try",
    "trys": "try",
    "tri": "try",
    "touchdown": "try",
    "tryed": "try",

    # Set piece
    "lineouts": "lineout",
    "scrums": "scrum",
    "scrummage": "scrum",
    "malls": "maul",
    "mauling": "maul",
    "rucks": "ruck",
    "rucking": "ruck",

    # Breakdown / play
    "offloads": "offload",
    "offloaded": "offload",
    "tackled": "tackle",
    "tackles": "tackle",
    "turnovers": "turnover",
    "knockon": "knock on",
    "knock-on": "knock on",
    "forward-pass": "forward pass",
    "linebreak": "line break",
    "line-break": "line break",
    "counterattack": "counter attack",
    "counter-attack": "counter attack",
    "breakdown": "breakdown",

    # Referee
    "penalty's": "penalty",
    "penalties": "penalty",
    "penalised": "penalty",
    "penalized": "penalty",
    "tmo": "tmo",
    "t.m.o": "tmo",
    "yellow-card": "yellow card",
    "red-card": "red card",
    "sin-bin": "sin bin",
    "sinbin": "sin bin",

    # Kicking
    "conversions": "conversion",
    "converting": "conversion",
    "converted": "conversion",
    "dropgoal": "drop goal",
    "drop-goal": "drop goal",
    "grubbers": "grubber kick",
    "garryowen": "garryowen",
    "boxkick": "box kick",
    "box-kick": "box kick",

    # Excitement / commentary phrases (common mishearings)
    "sensational": "sensational",
    "unbelieveable": "unbelievable",
    "magnificant": "magnificent",
    "incredable": "incredible",
    "brillient": "brilliant",

    # Common player name fixes observed in training data
    "bundee": "Bundee Aki",
    "aki": "Bundee Aki",
    "kolisi": "Siya Kolisi",
    "kolbe": "Cheslin Kolbe",
    "sexton": "Johnny Sexton",
    "furlong": "Tadhg Furlong",
    "keenan": "Hugo Keenan",
    "pollard": "Handre Pollard",
    "etzebeth": "Eben Etzebeth",
}


def apply_rugby_corrections(text: str) -> str:
    """Replaces known Whisper misrecognitions with correct rugby terms."""
    for wrong, correct in RUGBY_CORRECTIONS.items():
        text = re.sub(rf"\b{re.escape(wrong)}\b", correct, text, flags=re.IGNORECASE)
    return text


def clean_text(text: str) -> str:
    """Cleans up raw Whisper transcript text for the model/lexicon."""
    text = apply_rugby_corrections(text)
    text = text.lower()

    fillers = ["uh", "umm", "um", "ah", "oh"]
    for w in fillers:
        text = re.sub(rf"\b{w}\b", "", text)

    text = re.sub(r'(.)\1{2,}', r'\1', text)   # collapse repeated letters
    text = re.sub(r"['\u2019]", "", text)      # remove apostrophes
    text = re.sub(r"[^a-z0-9 ]", " ", text)    # remove punctuation
    text = re.sub(r"\s+", " ", text).strip()   # collapse whitespace

    return text
