"""
Visual model architecture definition.

HOW TO REPLACE THE STUB WITH YOUR REAL MODEL:
1. Define your model class here (CNN, ViT, SlowFast, etc.)
2. The class must accept video frames as input.
   Recommended input: (batch, channels, frames, height, width)
   for 3D CNNs, or (batch, frames, channels, height, width) for ViTs.
3. Output should be a tuple: (excitement_score, event_logits)
   where excitement_score is a scalar in [0,1] and event_logits
   is a vector over your event classes.
4. Save weights with:
   torch.save(model.state_dict(), "weights/visual/rugby_action_classifier.pth")
5. In inference.py, load with:
   model = RugbyVisualClassifier(num_classes=len(EVENT_CLASSES))
   model.load_state_dict(torch.load(weights_path))
   model.eval()
"""

import torch
import torch.nn as nn

# Rugby event classes your visual model should detect
EVENT_CLASSES = [
    "none", "scrum", "try", "lineout",
    "tackle", "penalty", "conversion",
    "kick", "breakdown", "ruck"
]


class RugbyVisualClassifier(nn.Module):
    """
    Placeholder architecture. Replace with your actual model.
    Current stub: simple CNN feature extractor + classifier head.
    """
    def __init__(self, num_classes: int = len(EVENT_CLASSES)):
        super().__init__()
        self.num_classes = num_classes
        # TODO: replace with your real architecture
        self.feature_extractor = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.classifier = nn.Linear(64 * 4 * 4, num_classes)
        self.excitement_head = nn.Linear(64 * 4 * 4, 1)

    def forward(self, x):
        # x: (batch, channels, height, width)
        features = self.feature_extractor(x)
        features = features.flatten(1)
        event_logits = self.classifier(features)
        excitement = torch.sigmoid(self.excitement_head(features))
        return excitement, event_logits
