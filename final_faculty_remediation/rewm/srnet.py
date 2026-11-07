"""SRNet: Steganalysis Residual Network (Boroumand et al., IEEE TIFS 2019).

Reference:
    Mehdi Boroumand, Mo Chen, and Jessica Fridrich,
    "Deep Residual Network for Steganalysis of Digital Images",
    IEEE Transactions on Information Forensics and Security, 14(5):1181-1193, 2019.
    DOI: 10.1109/TIFS.2018.2871749

Architecture:
    - Layers 1-2: Unpooled convolutional layers (filter extraction without downsampling)
    - Layers 3-7: Type 2 Residual Blocks (skip connection without pooling)
    - Layers 8-11: Type 3 Residual Blocks (downsampling with average pooling + 1x1 projection)
    - Layer 12: Type 4 Residual Block (residual block before global pooling)
    - Pooling: Global Average Pooling (GAP)
    - Head: Fully connected linear layer to scalar logit
"""

import torch
import torch.nn as nn


class Type2Block(nn.Module):
    """Type 2 Residual Block: Conv-BN-ReLU -> Conv-BN -> Element-wise addition."""
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        res = self.conv2(self.relu(self.bn1(self.conv1(x))))
        res = self.bn2(res)
        return x + res


class Type3Block(nn.Module):
    """Type 3 Residual Block: Downsampling with average pooling and 1x1 shortcut."""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.pool = nn.AvgPool2d(kernel_size=3, stride=2, padding=1)

        self.shortcut = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=2, bias=False),
            nn.BatchNorm2d(out_channels)
        )

    def forward(self, x):
        main = self.conv2(self.relu(self.bn1(self.conv1(x))))
        main = self.pool(self.bn2(main))
        short = self.shortcut(x)
        return main + short


class Type4Block(nn.Module):
    """Type 4 Residual Block: Conv-BN-ReLU -> Conv-BN -> Element-wise addition."""
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        res = self.conv2(self.relu(self.bn1(self.conv1(x))))
        res = self.bn2(res)
        return x + res


class SRNet(nn.Module):
    """Full 12-layer SRNet architecture for digital steganalysis and forensic detection."""
    def __init__(self, in_channels=3, num_classes=1, use_highpass=False):
        super().__init__()
        self.use_highpass = use_highpass
        if use_highpass:
            from rewm.model import HighPass
            self.hp = HighPass()
            in_ch = 9
        else:
            self.hp = None
            in_ch = in_channels

        # Layer 1 & 2: Unpooled filter layers
        self.layer1 = nn.Sequential(
            nn.Conv2d(in_ch, 64, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True)
        )
        self.layer2 = nn.Sequential(
            nn.Conv2d(64, 16, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True)
        )

        # Layers 3-7: 5 Type 2 Residual Blocks (16 channels, unpooled)
        self.layers3_7 = nn.Sequential(
            Type2Block(16),
            Type2Block(16),
            Type2Block(16),
            Type2Block(16),
            Type2Block(16)
        )

        # Layers 8-11: 4 Type 3 Residual Blocks (downsampling)
        self.layer8 = Type3Block(16, 64)
        self.layer9 = Type3Block(64, 128)
        self.layer10 = Type3Block(128, 256)
        self.layer11 = Type3Block(256, 512)

        # Layer 12: Type 4 Residual Block (512 channels)
        self.layer12 = Type4Block(512)

        # Global Average Pooling and Linear Head
        self.fc = nn.Linear(512, num_classes)

    def forward(self, x):
        if self.use_highpass:
            x = self.hp(x)
        else:
            x = (x - 0.5) * 2.0  # normalize [0, 1] to [-1, 1]

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layers3_7(x)
        x = self.layer8(x)
        x = self.layer9(x)
        x = self.layer10(x)
        x = self.layer11(x)
        x = self.layer12(x)

        # Global Average Pooling
        x = x.mean(dim=(2, 3))
        out = self.fc(x)
        return out.squeeze(1) if out.shape[1] == 1 else out
