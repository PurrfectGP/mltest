import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights


class ResNetBackbone(nn.Module):
    """Feature extractor using ResNet18 backbone.

    Extracts 512-dimensional feature vectors from images.
    """

    def __init__(self, pretrained: bool = True):
        super().__init__()
        # Use standard torchvision resnet18 with ImageNet weights
        weights = ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        base = resnet18(weights=weights)
        # Remove the final FC layer to get features
        self.features = nn.Sequential(*list(base.children())[:-1])
        self.fea_dim = 512

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Extract features from input images.

        Args:
            x: Input tensor of shape (batch, 3, 224, 224)

        Returns:
            Feature tensor of shape (batch, 512)
        """
        x = self.features(x)
        return x.view(x.size(0), -1)
