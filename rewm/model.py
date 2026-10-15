"""Resolution-agnostic forensic CNN.

Design choices (each one answers a limitation listed in the literature review):
  * no early down-sampling: the first two conv layers run at full resolution, because
    watermark residuals live in the highest frequencies;
  * global average + global max pooling: the same network accepts any input size
    (train on small crops, test on full 128 / 256 / 384 / 512 px images);
  * ~1M parameters (width=32): no fingerprint database, no key, no API - it is a plain
    classifier that can run on a laptop.
"""
import torch
import torch.nn as nn


def _conv_bn(cin, cout, stride=1):
    return nn.Sequential(nn.Conv2d(cin, cout, 3, stride, 1, bias=False), nn.BatchNorm2d(cout), nn.ReLU(inplace=True))


class ResBlock(nn.Module):
    def __init__(self, cin, cout, stride):
        super().__init__()
        self.c1 = _conv_bn(cin, cout, stride)
        self.c2 = nn.Sequential(nn.Conv2d(cout, cout, 3, 1, 1, bias=False), nn.BatchNorm2d(cout))
        self.short = (nn.Identity() if (cin == cout and stride == 1) else
                      nn.Sequential(nn.Conv2d(cin, cout, 1, stride, bias=False), nn.BatchNorm2d(cout)))
        self.act = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.act(self.c2(self.c1(x)) + self.short(x))


class HighPass(nn.Module):
    """Fixed (non-trainable) residual filters: KV 5x5 + horizontal/vertical 2nd-order differences.
    They suppress image content and keep the faint watermark residual - the standard first layer of
    steganalysis / forensic CNNs. Applied per RGB channel -> 9 output channels."""
    def __init__(self):
        super().__init__()
        kv = torch.tensor([[-1, 2, -2, 2, -1], [2, -6, 8, -6, 2], [-2, 8, -12, 8, -2],
                           [2, -6, 8, -6, 2], [-1, 2, -2, 2, -1]], dtype=torch.float32) / 12.0
        hz = torch.zeros(5, 5); hz[2, 1:4] = torch.tensor([1.0, -2.0, 1.0])
        k = torch.stack([kv, hz, hz.t()])                          # (3,5,5)
        self.register_buffer("w", k.repeat(3, 1, 1).unsqueeze(1))  # (9,1,5,5)

    def forward(self, x):                                          # x in [0,1]
        x = x * 255.0
        return torch.cat([nn.functional.conv2d(x[:, c:c + 1], self.w[3 * c:3 * c + 3], padding=2)
                          for c in range(3)], dim=1)


class ForensicNet(nn.Module):
    def __init__(self, width=32, dropout=0.2, use_highpass=True):
        super().__init__()
        w = width
        self.use_highpass = use_highpass
        if use_highpass:
            self.stem = nn.Sequential(HighPass(), nn.BatchNorm2d(9), _conv_bn(9, w), _conv_bn(w, w))
        else:
            # ablation (plan item #14): same architecture, but the raw RGB image goes
            # straight into the stem instead of the fixed high-pass residual filters -
            # isolates how much of the model's AUC comes from that one design choice.
            self.stem = nn.Sequential(nn.BatchNorm2d(3), _conv_bn(3, w), _conv_bn(w, w))
        self.stages = nn.Sequential(ResBlock(w, 2 * w, 2), ResBlock(2 * w, 4 * w, 2),
                                    ResBlock(4 * w, 8 * w, 2), ResBlock(8 * w, 8 * w, 2))
        self.drop = nn.Dropout(dropout)
        self.fc = nn.Linear(16 * w, 1)

    def forward(self, x):                       # x in [0, 1]
        f = self.stages(self.stem(x))
        g = torch.cat([f.mean(dim=(2, 3)), f.amax(dim=(2, 3))], dim=1)
        return self.fc(self.drop(g)).squeeze(1)  # logit: > 0  => re-watermarked


class SimpleClassifier(nn.Module):
    """Plan item #14's 'simple classifier' baseline: a plain small CNN with none of
    ForensicNet's design choices (no fixed high-pass front end, no residual blocks,
    no GAP+GMP dual pooling - just stride-2 convs, global average pool, one linear
    layer). Shows how much of the real model's accuracy comes from those choices
    rather than from "any CNN told the two classes apart"."""
    def __init__(self, width=32):
        super().__init__()
        w = width
        self.net = nn.Sequential(
            _conv_bn(3, w, 2), _conv_bn(w, 2 * w, 2), _conv_bn(2 * w, 4 * w, 2),
            _conv_bn(4 * w, 8 * w, 2), _conv_bn(8 * w, 8 * w, 2),
        )
        self.fc = nn.Linear(8 * w, 1)

    def forward(self, x):                       # x in [0, 1]
        f = self.net(x).mean(dim=(2, 3))         # global average pool only
        return self.fc(f).squeeze(1)


class TVResNet18(nn.Module):
    """Optional standard baseline for the paper's ablation (stride-1 stem, no max-pool)."""
    def __init__(self):
        super().__init__()
        import torchvision
        m = torchvision.models.resnet18(weights=None)
        m.conv1 = nn.Conv2d(3, 64, 3, 1, 1, bias=False)
        m.maxpool = nn.Identity()
        m.fc = nn.Linear(512, 1)
        self.m = m

    def forward(self, x):
        return self.m((x - 0.5) * 2.0).squeeze(1)


def build_model(arch="forensic", width=32):
    if arch == "forensic":
        return ForensicNet(width=width)
    if arch == "forensic_nohp":
        return ForensicNet(width=width, use_highpass=False)
    if arch == "simple":
        return SimpleClassifier(width=width)
    if arch == "resnet18":
        return TVResNet18()
    raise ValueError(arch)
