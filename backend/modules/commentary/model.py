"""
Dual-head transformer (event classification + highlight scoring) for the
commentary ML branch.

Ported (inference-only — no FocalLoss/Trainer/training code, that lives in
the training project) from
d:/Test FYP/commentary_analysis_system/src/models/transformer_classifier.py.

Unlike the training project, the backbone is built via AutoModel.from_config
(random init) rather than AutoModel.from_pretrained(model_name): the
checkpoint's own state dict already contains the fully fine-tuned backbone
weights, so there is no need to download a pretrained model from the
HuggingFace Hub at inference time — this loader works fully offline.
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
from transformers import AutoConfig, AutoModel, AutoTokenizer
from transformers.modeling_outputs import ModelOutput

logger = logging.getLogger(__name__)

# Old-architecture (plain Linear heads) -> new-architecture
# (Sequential(Dropout, Linear), Linear at index 1) state_dict key remap,
# for backward compatibility with checkpoints exported before the dropout
# layer was added to the heads.
_LEGACY_KEY_MAP = {
    "event_classifier.weight": "event_classifier.1.weight",
    "event_classifier.bias": "event_classifier.1.bias",
    "highlight_scorer.weight": "highlight_scorer.1.weight",
    "highlight_scorer.bias": "highlight_scorer.1.bias",
}


@dataclass
class DualHeadOutput(ModelOutput):
    logits: torch.FloatTensor = None
    highlight_scores: torch.FloatTensor = None


class DualHeadRoBERTa(nn.Module):
    """Transformer backbone (any AutoModel-compatible encoder) + two heads:
    event_classifier (num_labels-way softmax logits) and highlight_scorer
    (sigmoid 0-1 excitement score)."""

    def __init__(self, config, num_labels: int):
        super().__init__()
        # Attribute name "roberta" (not e.g. "backbone") is load-bearing: it
        # must match the state_dict key prefix baked into checkpoints saved
        # by the training project's TransformerClassifier, regardless of
        # which actual backbone architecture (RoBERTa/DeBERTa/BERT/ModernBERT)
        # was fine-tuned.
        self.roberta = AutoModel.from_config(config)

        self.event_classifier = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(config.hidden_size, num_labels),
        )
        self.highlight_scorer = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(config.hidden_size, 1),
        )

    def forward(self, input_ids, attention_mask):
        outputs = self.roberta(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = getattr(outputs, "pooler_output", None)
        if pooled_output is None:
            pooled_output = outputs.last_hidden_state[:, 0, :]

        event_logits = self.event_classifier(pooled_output)
        highlight_score = torch.sigmoid(self.highlight_scorer(pooled_output))

        return DualHeadOutput(logits=event_logits, highlight_scores=highlight_score)


def _load_state_dict(checkpoint_dir: Path) -> dict:
    safetensors_path = checkpoint_dir / "model.safetensors"
    bin_path = checkpoint_dir / "pytorch_model.bin"

    if safetensors_path.exists():
        from safetensors.torch import load_file
        state_dict = load_file(str(safetensors_path))
    elif bin_path.exists():
        state_dict = torch.load(str(bin_path), map_location="cpu")
    else:
        raise FileNotFoundError(
            f"No model.safetensors or pytorch_model.bin found in {checkpoint_dir}"
        )

    return {_LEGACY_KEY_MAP.get(k, k): v for k, v in state_dict.items()}


def load_checkpoint(checkpoint_dir: str, device: Optional[torch.device] = None):
    """
    Load a fine-tuned DualHeadRoBERTa checkpoint directory (config.json +
    model.safetensors|pytorch_model.bin + tokenizer files).

    Returns (model, tokenizer, id2label) with the model on `device` (or
    CUDA if available) in eval mode.
    """
    checkpoint_dir = Path(checkpoint_dir)
    device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

    config = AutoConfig.from_pretrained(str(checkpoint_dir))
    id2label = {int(k): v for k, v in dict(config.id2label).items()}
    num_labels = len(id2label)

    model = DualHeadRoBERTa(config, num_labels=num_labels)
    state_dict = _load_state_dict(checkpoint_dir)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_dir))

    logger.info(
        "Commentary model loaded from %s (%d labels) on %s",
        checkpoint_dir, num_labels, device,
    )
    return model, tokenizer, id2label


@torch.no_grad()
def predict_probs(model, tokenizer, texts: list[str], device: torch.device, batch_size: int = 32):
    """Returns (event_probs: list[list[float]], highlight_scores: list[float])."""
    model.eval()

    all_event_probs: list[list[float]] = []
    all_highlight_scores: list[float] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        inputs = tokenizer(batch, padding=True, truncation=True, max_length=128, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}

        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        all_event_probs.extend(probs.tolist())
        all_highlight_scores.extend(outputs.highlight_scores.view(-1).tolist())

    return all_event_probs, all_highlight_scores
