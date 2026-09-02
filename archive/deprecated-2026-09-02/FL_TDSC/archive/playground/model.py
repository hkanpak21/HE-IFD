"""Model architectures + arch-agnostic state handling.

Supported:
    --arch mlp     -> MLP 784-128-32-10  (110k params)
    --arch lenet5  -> LeNet-5            ( ~60k params)
"""
from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F


def build_mlp(input_dim: int = 784, num_classes: int = 10) -> nn.Sequential:
    return nn.Sequential(
        nn.Flatten(),
        nn.Linear(input_dim, 128),
        nn.ReLU(),
        nn.Linear(128, 32),
        nn.ReLU(),
        nn.Linear(32, num_classes),
    )


class LeNet5(nn.Module):
    """Classic LeNet-5 for 28x28 MNIST (1 channel)."""
    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 6, kernel_size=5, padding=2)   # 28x28 -> 28x28
        self.pool1 = nn.MaxPool2d(2)                              # -> 14x14
        self.conv2 = nn.Conv2d(6, 16, kernel_size=5)              # -> 10x10
        self.pool2 = nn.MaxPool2d(2)                              # -> 5x5
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.conv1(x))
        x = self.pool1(x)
        x = F.relu(self.conv2(x))
        x = self.pool2(x)
        x = x.flatten(1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


def build_model(arch: str = "mlp") -> nn.Module:
    if arch == "mlp":
        return build_mlp()
    if arch == "lenet5":
        return LeNet5()
    raise ValueError(f"unknown arch: {arch}")


def shared_init(seed: int, arch: str, device) -> dict[str, torch.Tensor]:
    torch.manual_seed(seed)
    m = build_model(arch).to(device)
    return state_named(m)


def state_named(m: nn.Module) -> dict[str, torch.Tensor]:
    """Architecture-agnostic: return clones of every parameter+buffer in state_dict."""
    return {k: v.detach().clone() for k, v in m.state_dict().items()}


def load_named(m: nn.Module, s: dict[str, torch.Tensor]) -> None:
    m.load_state_dict(s, strict=True)


def deltas(initial: dict, final: dict) -> dict:
    return {k: final[k] - initial[k] for k in initial}
