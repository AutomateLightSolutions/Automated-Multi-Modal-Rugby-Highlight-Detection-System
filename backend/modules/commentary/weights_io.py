"""
Filesystem access + lazy singleton loading for the commentary model/lexicon
artifacts uploaded via POST /api/v1/admin/models/upload.

Layout (mirrors modules/visual/inference.py's checkpoint-path convention):
    weights/commentary/config.json
    weights/commentary/model.safetensors | pytorch_model.bin
    weights/commentary/tokenizer.json, tokenizer_config.json
    weights/commentary/lexicon/lexicon.json

Like visual's get_model() and asr.py's _get_whisper_model(), the loaded
checkpoint/lexicon are cached once per worker process — a newly uploaded
model is only picked up by Celery workers started/restarted after the
upload, not by ones already running.
"""
import torch

from config import settings

MODEL_DIR = settings.MODEL_WEIGHTS_PATH / "commentary"
LEXICON_PATH = MODEL_DIR / "lexicon" / "lexicon.json"

_REQUIRED_MODEL_FILES = ("config.json", "tokenizer_config.json")
_WEIGHT_FILES = ("model.safetensors", "pytorch_model.bin")

_checkpoint_cache: tuple | None = None
_lexicon_cache = None


def is_model_available() -> bool:
    if not MODEL_DIR.is_dir():
        return False
    if not all((MODEL_DIR / name).exists() for name in _REQUIRED_MODEL_FILES):
        return False
    return any((MODEL_DIR / name).exists() for name in _WEIGHT_FILES)


def is_lexicon_available() -> bool:
    return LEXICON_PATH.exists()


def get_checkpoint():
    """Lazy-loaded (model, tokenizer, id2label, device) singleton."""
    global _checkpoint_cache
    if _checkpoint_cache is None:
        from modules.commentary.model import load_checkpoint

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model, tokenizer, id2label = load_checkpoint(str(MODEL_DIR), device=device)
        _checkpoint_cache = (model, tokenizer, id2label, device)
    return _checkpoint_cache


def get_lexicon():
    """Lazy-loaded LexiconModel singleton."""
    global _lexicon_cache
    if _lexicon_cache is None:
        from modules.commentary.lexicon import LexiconModel

        _lexicon_cache = LexiconModel(str(LEXICON_PATH))
    return _lexicon_cache
