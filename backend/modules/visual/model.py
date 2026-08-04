"""
SlowFast R50 dual-head model.

Architecture is dictated by the trained checkpoint (best_model.pt), not
chosen freely here:
  - Backbone: pytorchvideo's slowfast_r50, stem + 4 residual stages only
    (blocks[0:5]) — its own pooling/fusion and classification head
    (blocks[5]) are dropped in favour of the custom heads below, matching
    how this checkpoint was trained.
  - Each pathway's final feature map -> AdaptiveAvgPool3d(1) -> flatten ->
    concat -> (batch, 2304) fused vector (2048 slow-pathway channels +
    256 fast-pathway channels).
  - class_head: Linear(2304 -> 10) over EVENT_CLASSES.
  - score_head: Linear(2304 -> 1) + Sigmoid, continuous highlight score.

forward(slow, fast) returns (class_logits, score) as RAW logits — softmax is
applied by the caller (modules/visual/inference.py), not baked in here,
since the checkpoint was trained against raw logits + BCE-on-sigmoid, never
asked to emit softmax directly.
"""
import torch
import torch.nn as nn

from constants import EVENT_CLASSES

FUSED_FEATURE_DIM = 2304  # 2048 (slow pathway) + 256 (fast pathway)


class RugbyVisualClassifier(nn.Module):
    def __init__(self, num_classes: int = len(EVENT_CLASSES)):
        super().__init__()
        self.backbone = _build_backbone()
        self.pool = nn.AdaptiveAvgPool3d(1)
        self.class_head = nn.Linear(FUSED_FEATURE_DIM, num_classes)
        self.score_head = nn.Sequential(nn.Linear(FUSED_FEATURE_DIM, 1), nn.Sigmoid())

    def forward(self, slow: torch.Tensor, fast: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = [slow, fast]
        for block in self.backbone:
            x = block(x)
        # x is now [slow_features, fast_features], each (B, C, T, H, W)
        pooled = [self.pool(pathway).flatten(1) for pathway in x]
        fused = torch.cat(pooled, dim=1)  # (B, 2304)

        class_logits = self.class_head(fused)
        score = self.score_head(fused).squeeze(-1)
        return class_logits, score


def _build_backbone() -> nn.ModuleList:
    from pytorchvideo.models.hub import slowfast_r50

    # pretrained=False always — best_model.pt supplies all weights.
    full_model = slowfast_r50(pretrained=False)
    return nn.ModuleList(list(full_model.blocks.children())[:5])
