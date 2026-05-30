"""Model factories and pretrained feature extractors.

Two kinds of "model" travel through the protocol:

1. **From-scratch nets** trained on raw inputs (e.g. ``MLP_MNIST`` 784->128->64->10,
   ported verbatim from notebook Section A.2). The student IS the whole net.
2. **Linear heads** on top of frozen pretrained features (``ClassifierHead``,
   notebook Section B.2). The backbone is run once to cache features; only the
   head is distilled/aggregated. This keeps the FHE object tiny and is why the
   protocol is backbone-agnostic.

Feature extractors (vision: ResNet-18 / ViT-B/32 on CIFAR-10; text: DistilBERT /
GPT-2 on AG News) are ported from notebook Sections B.1 and C.1. They are
*deferred imports* — torch/torchvision/timm/transformers are only imported when
an extractor is actually called, so login-node syntax checks stay clean.

DEVICE is resolved lazily (``_device()``) for the same reason: importing this
module must not require CUDA or even torch.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Tuple


# ----------------------------------------------------------------------------
# Device + param-dict helpers (notebook Section 0.3 globals)
# ----------------------------------------------------------------------------
def _device() -> str:
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


def get_params(model) -> Dict:
    """Detached clone of a model's full state_dict (the parameter vector θ)."""
    return {k: v.detach().clone() for k, v in model.state_dict().items()}


def set_params(model, params: Dict) -> None:
    model.load_state_dict(params)


# ----------------------------------------------------------------------------
# From-scratch MNIST MLP (notebook Section A.2)
# ----------------------------------------------------------------------------
def _build_mlp_class():
    import torch.nn as nn

    class MLP_MNIST(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(784, 128), nn.ReLU(),
                nn.Linear(128, 64), nn.ReLU(),
                nn.Linear(64, 10),
            )

        def forward(self, x):
            return self.net(x)

    return MLP_MNIST


def make_mnist_mlp() -> Callable:
    """Return a zero-arg factory that builds a fresh MLP on DEVICE.

    The protocol passes ``make_model_fn`` around (notebook convention); every
    fresh model must land on the same device so distillation/aggregation tensors
    are co-located.
    """
    MLP_MNIST = _build_mlp_class()
    dev = _device()

    def _factory():
        return MLP_MNIST().to(dev)

    return _factory


# ----------------------------------------------------------------------------
# From-scratch LeNet-5 for FashionMNIST (1x28x28)
# ----------------------------------------------------------------------------
def _build_lenet5_class():
    """Classic LeNet-5 sized for 1x28x28 inputs (the Co-Boosting / DENSE / FedLPA
    "LeNet-5 for MNIST and FMNIST" convention; see comparators/REPORTED_RESULTS.md
    rows 5/11). Two 5x5 conv blocks with 2x2 max-pool, then 3 FC layers, ReLU
    throughout. Unlike ``MLP_MNIST`` (which consumes flat 784-vectors), this is a
    CONV net: ``forward`` expects an image-shaped batch ``(B, 1, 28, 28)`` and
    flattens internally before the FC head, so the loader must hand it
    ``(N, 1, 28, 28)`` tensors (see ``data.load_fmnist_tensors``). Output logits
    are 10-way; activations are all ReLU (FHE-friendliness lives in the linear
    server aggregate, not in the student, so no polynomial approximation here)."""
    import torch.nn as nn

    class LeNet5_FMNIST(nn.Module):
        def __init__(self, num_classes: int = 10):
            super().__init__()
            # conv1: 1->6, 5x5, pad 2 keeps 28x28; pool -> 14x14
            # conv2: 6->16, 5x5, no pad -> 10x10; pool -> 5x5
            self.features = nn.Sequential(
                nn.Conv2d(1, 6, kernel_size=5, padding=2), nn.ReLU(),
                nn.MaxPool2d(kernel_size=2, stride=2),
                nn.Conv2d(6, 16, kernel_size=5), nn.ReLU(),
                nn.MaxPool2d(kernel_size=2, stride=2),
            )
            self.classifier = nn.Sequential(
                nn.Linear(16 * 5 * 5, 120), nn.ReLU(),
                nn.Linear(120, 84), nn.ReLU(),
                nn.Linear(84, num_classes),
            )

        def forward(self, x):
            x = self.features(x)
            x = x.flatten(1)  # (B, 16*5*5); image -> flat happens INSIDE the net
            return self.classifier(x)

    return LeNet5_FMNIST


def make_fmnist_lenet5(num_classes: int = 10) -> Callable:
    """Zero-arg factory for a fresh LeNet-5 on DEVICE (FashionMNIST, 1x28x28).

    Parameter-free factory matching the ``scratch`` make_model_fn contract used
    by ``protocol.run_cell`` (it calls ``model_fn_src()`` with no args for scratch
    backbones). Every fresh model lands on the resolved DEVICE so distillation /
    aggregation tensors stay co-located, exactly as for the MNIST MLP."""
    LeNet5_FMNIST = _build_lenet5_class()
    dev = _device()

    def _factory():
        return LeNet5_FMNIST(num_classes).to(dev)

    return _factory


# ----------------------------------------------------------------------------
# From-scratch CNN-5 for CIFAR-10 (3x32x32)
# ----------------------------------------------------------------------------
def _build_cnn5_class():
    """5-layer conv net for 3x32x32 inputs (the Co-Boosting / DENSE / FedLPA
    "CNN with 5 layers for SVHN/CIFAR-10/CIFAR-100" convention; see
    comparators/REPORTED_RESULTS.md rows 5/11). Three 3x3 conv blocks (each
    conv+ReLU+2x2 max-pool, 32->64->128 channels) reduce 32x32 -> 4x4, then 2 FC
    layers (5 weight layers total: 3 conv + 2 linear), ReLU throughout. Like
    LeNet-5 it is a CONV net: ``forward`` expects ``(B, 3, 32, 32)`` and flattens
    internally before the FC head, so the loader hands it ``(N, 3, 32, 32)``
    IMAGE tensors (``data.load_cifar10_raw_tensors``) — distinct from the
    pretrained-feature path in ``extract_cifar10_features``. 10-way logits."""
    import torch.nn as nn

    class CNN5_CIFAR10(nn.Module):
        def __init__(self, num_classes: int = 10):
            super().__init__()
            # 3x conv blocks, each halves H,W via 2x2 pool: 32->16->8->4
            self.features = nn.Sequential(
                nn.Conv2d(3, 32, kernel_size=3, padding=1), nn.ReLU(),
                nn.MaxPool2d(2, 2),
                nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(),
                nn.MaxPool2d(2, 2),
                nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(),
                nn.MaxPool2d(2, 2),
            )
            self.classifier = nn.Sequential(
                nn.Linear(128 * 4 * 4, 256), nn.ReLU(),
                nn.Linear(256, num_classes),
            )

        def forward(self, x):
            x = self.features(x)
            x = x.flatten(1)  # (B, 128*4*4); image -> flat happens INSIDE the net
            return self.classifier(x)

    return CNN5_CIFAR10


def make_cifar10_cnn5(num_classes: int = 10) -> Callable:
    """Zero-arg factory for a fresh CNN-5 on DEVICE (CIFAR-10, 3x32x32).

    Parameter-free factory matching the ``scratch`` make_model_fn contract (see
    ``make_fmnist_lenet5``). Consumes raw image tensors, NOT pretrained features."""
    CNN5_CIFAR10 = _build_cnn5_class()
    dev = _device()

    def _factory():
        return CNN5_CIFAR10(num_classes).to(dev)

    return _factory


# ----------------------------------------------------------------------------
# Linear classifier head on pretrained features (notebook Section B.2)
# ----------------------------------------------------------------------------
def _build_head_class():
    import torch.nn as nn

    class ClassifierHead(nn.Module):
        def __init__(self, in_dim, num_classes):
            super().__init__()
            self.fc = nn.Linear(in_dim, num_classes)

        def forward(self, x):
            return self.fc(x)

    return ClassifierHead


def make_head(in_dim: int, num_classes: int) -> Callable:
    """Zero-arg factory for a linear head sized (in_dim -> num_classes) on DEVICE."""
    ClassifierHead = _build_head_class()
    dev = _device()

    def _factory():
        return ClassifierHead(in_dim, num_classes).to(dev)

    return _factory


# ----------------------------------------------------------------------------
# Trainable-scope variants of the head (issue 011)
# ----------------------------------------------------------------------------
# Issue 011 introduces a ``trainable_scope`` knob on the protocol. For
# pretrained "head" backbones the features are pre-cached (notebook Section B.1
# / C.1), so the only model the protocol ever instantiates is the head on top
# of those features — the entire frozen backbone is amortised away. The
# scope-versus-architecture choices below realise the spirit of the issue
# ("LoRA on the last 1-2 blocks + head" / "full FT of last 1-2 blocks + head")
# *in the cached-feature space*, which is the natural place to expand head
# capacity without re-architecting the pipeline. The issue's own implementation
# pointer endorses this minimal interpretation: "Linear-only LoRA in the head
# is the simplest and still tests the hypothesis."
#
# Critical FHE invariant: every trainable tensor (base Linear weights + bias,
# LoRA A/B matrices, MLP hidden-layer weights) ends up in ``state_dict`` and
# therefore in the cumulative displacement ``Δᵢ`` the server aggregates. Since
# ``aggregate`` operates element-wise (PT-scalar × CT  and  CT + CT) on every
# tensor in the dict, the linearity invariant is preserved regardless of which
# scope is selected. The unit test in ``tests/test_aggregate.py`` exercises a
# 10× larger parameter dict to make this explicit.


def _build_lora_head_class():
    """Linear head + parallel rank-r LoRA residual update (hand-rolled).

    Forward:  y = W·x + b + (α/r) · B·A·x
        - (W, b) is the BASE linear head (same as ``ClassifierHead``);
        - A is r×in_dim, B is num_classes×r; both initialised so the LoRA branch
          starts at zero (A=Kaiming-uniform, B=zero) — equivalent to a pure
          linear head at step 0.
        - α/r is the standard LoRA scaling. All five tensors (fc.weight,
          fc.bias, lora_A.weight, lora_B.weight, and the scaling buffer for
          checkpoint friendliness) live in state_dict and so flow through
          aggregate exactly as for ``ClassifierHead`` — element-wise PT × CT
          and CT + CT only, no new non-linear ops.

    Capacity: ~ r·(in_dim + num_classes) extra trainable scalars on top of the
    base in_dim·num_classes head. For resnet18/CIFAR-10 (in_dim=512, nc=10) at
    r=8 that is ~4176 extra params vs the base 5130, so trainable scope expands
    roughly 1.8× — still tiny in absolute terms but enough to test the "adapter
    suffices" hypothesis from issue 011.
    """
    import math

    import torch
    import torch.nn as nn

    class LoRAHead(nn.Module):
        def __init__(self, in_dim: int, num_classes: int, rank: int,
                     alpha: float):
            super().__init__()
            self.in_dim = in_dim
            self.num_classes = num_classes
            self.rank = int(rank)
            # ``alpha / rank`` is the conventional LoRA scaling; stored as a
            # plain Python float (NOT a Parameter) so it never enters state_dict
            # and never has to be aggregated — it is a *constant* shared by all
            # clients (protocol-wide hyperparam, not per-client tensor).
            self.scaling = float(alpha) / max(1, int(rank))

            self.fc = nn.Linear(in_dim, num_classes)
            # LoRA matrices: A: (rank, in_dim), B: (num_classes, rank).
            # Bias-less so trainable params are exactly A.weight + B.weight.
            self.lora_A = nn.Linear(in_dim, self.rank, bias=False)
            self.lora_B = nn.Linear(self.rank, num_classes, bias=False)
            # LoRA-standard initialisation: A ~ Kaiming-uniform, B = 0, so the
            # residual update starts at zero and the model is a pure linear
            # head at iteration 0 (matches ``ClassifierHead`` initial output).
            nn.init.kaiming_uniform_(self.lora_A.weight, a=math.sqrt(5))
            nn.init.zeros_(self.lora_B.weight)

        def forward(self, x):
            return self.fc(x) + self.scaling * self.lora_B(self.lora_A(x))

    return LoRAHead


def make_lora_head(in_dim: int, num_classes: int, rank: int = 8,
                   alpha: float = 8.0) -> Callable:
    """Zero-arg factory for ``LoRAHead`` sized (in_dim -> num_classes) on DEVICE.

    Default ``rank=8``, ``alpha=8`` matches issue 011's ``lora_8`` scope. The
    factory contract matches ``make_head`` so ``_load_features`` can swap one
    for the other transparently — ``protocol.run_cell`` never sees the
    difference, and aggregation continues to operate element-wise over the
    expanded state_dict (FHE-linearity invariant preserved by construction).
    """
    LoRAHead = _build_lora_head_class()
    dev = _device()

    def _factory():
        return LoRAHead(in_dim, num_classes, rank, alpha).to(dev)

    return _factory


def _build_mlp_head_class():
    """Two-layer MLP head: (in_dim -> hidden -> num_classes), ReLU between.

    The "last_block" scope from issue 011: more trainable capacity than the
    pure linear head, full FT (no rank constraint), still strictly local to
    the cached-feature space. Three trainable tensors (fc1.weight, fc1.bias,
    fc2.weight, fc2.bias) all sit in state_dict and aggregate element-wise.
    """
    import torch.nn as nn

    class MLPHead(nn.Module):
        def __init__(self, in_dim: int, num_classes: int, hidden_dim: int):
            super().__init__()
            self.fc1 = nn.Linear(in_dim, hidden_dim)
            self.act = nn.ReLU()
            self.fc2 = nn.Linear(hidden_dim, num_classes)

        def forward(self, x):
            return self.fc2(self.act(self.fc1(x)))

    return MLPHead


def make_mlp_head(in_dim: int, num_classes: int,
                  hidden_dim: int = 128) -> Callable:
    """Zero-arg factory for a 2-layer MLP head on DEVICE.

    Default ``hidden_dim=128`` realises the "last_block + head" scope at
    moderate capacity (~ in_dim·128 + 128·nc parameters; for resnet18 ≈ 66k,
    an order of magnitude beyond the linear head). Factory contract matches
    ``make_head`` so the protocol-side dispatch in ``_load_features`` only
    has to choose which factory builder to call.
    """
    MLPHead = _build_mlp_head_class()
    dev = _device()

    def _factory():
        return MLPHead(in_dim, num_classes, hidden_dim).to(dev)

    return _factory


def parse_scope(scope: str) -> Dict:
    """Parse a ``trainable_scope`` token into a structured config.

    Tokens (issue 011):
      * ``head_only``               -> {"kind": "head_only"}
      * ``lora_<rank>``             -> {"kind": "lora",  "rank": <int>,
                                         "alpha": <float, default = rank>}
      * ``last_block`` /
        ``last_n_blocks_<n>``       -> {"kind": "last_block",
                                         "hidden_dim": 128, "n_blocks": n|1}

    The "n_blocks" knob is recorded but not currently consumed by the
    head-on-cached-features pathway (the cached-feature MLPHead has a single
    hidden layer regardless of n; the field is preserved so the deferred
    ``last_n_blocks_2`` variant for the un-cached-backbone path can land later
    without changing this function's signature).
    """
    if scope == "head_only":
        return {"kind": "head_only"}
    if scope.startswith("lora_"):
        rest = scope[len("lora_"):]
        rank = int(rest)
        # LoRA standard: alpha defaults to rank so scaling = alpha/rank = 1.
        return {"kind": "lora", "rank": rank, "alpha": float(rank)}
    if scope == "last_block":
        return {"kind": "last_block", "hidden_dim": 128, "n_blocks": 1}
    if scope.startswith("last_n_blocks_"):
        n = int(scope[len("last_n_blocks_"):])
        return {"kind": "last_block", "hidden_dim": 128, "n_blocks": n}
    raise ValueError(
        f"unknown trainable_scope {scope!r}; expected "
        f"'head_only' | 'lora_<rank>' | 'last_block' | 'last_n_blocks_<n>'"
    )


def make_head_for_scope(in_dim: int, num_classes: int, scope: str) -> Callable:
    """Dispatch (in_dim, num_classes, scope) -> the zero-arg factory.

    Same contract as ``make_head`` (returns a parameter-free factory) so
    ``protocol._load_features`` can call this in place of ``make_head``
    whenever a non-default scope is requested. ``head_only`` returns the
    legacy ``make_head`` factory verbatim — byte-identical to pre-issue-011
    behaviour, so existing per-cell JSONs reproduce exactly.
    """
    cfg = parse_scope(scope)
    if cfg["kind"] == "head_only":
        return make_head(in_dim, num_classes)
    if cfg["kind"] == "lora":
        return make_lora_head(in_dim, num_classes,
                              rank=cfg["rank"], alpha=cfg["alpha"])
    if cfg["kind"] == "last_block":
        return make_mlp_head(in_dim, num_classes, hidden_dim=cfg["hidden_dim"])
    raise ValueError(scope)


# ----------------------------------------------------------------------------
# Vision feature extractors (notebook Section B.1)
# ----------------------------------------------------------------------------
def build_resnet18_extractor():
    import torch.nn as nn
    from torchvision import models

    m = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    m.fc = nn.Identity()
    return m.to(_device()).eval(), 512


def build_vit_extractor():
    import timm

    m = timm.create_model("vit_base_patch32_224", pretrained=True, num_classes=0)
    return m.to(_device()).eval(), m.num_features


def build_vit_l_extractor():
    """Frozen ViT-L/16 (timm ``vit_large_patch16_224``) feature extractor (issue 018).

    The "big-backbone" analogue of ``build_vit_extractor``: identical timm
    ``num_classes=0`` global-pooled-feature pattern, just the Large variant
    (≈304M params, 1024-d features vs ViT-B/32's 768-d). Patch-16 (not 32) is
    the standard ImageNet-21k→1k ViT-L checkpoint timm ships and the one whose
    published CIFAR-100 linear-probe transfer the Part-A sanity gate
    (IID ≥ 0.78) is calibrated against. Weights are large (~1.2GB) so the
    login-node prefetch (``jobs/prefetch_login.py --include-big-backbones``)
    must populate the timm/HF cache before any compute-node run.
    """
    import timm

    m = timm.create_model("vit_large_patch16_224", pretrained=True, num_classes=0)
    return m.to(_device()).eval(), m.num_features


def _build_vision_extractor(backbone_name: str):
    """Build a frozen vision extractor + the input transform appropriate for it.

    Returns (extractor, in_dim, tfm). Centralised here so the CIFAR-10 /
    CIFAR-100 / Tiny-ImageNet feature paths share one set of (backbone, tfm)
    decisions — adding a new dataset only requires a new ``extract_*_features``
    wrapper around this builder.

    The transforms exactly match notebook Section B.1 (the CIFAR-10 path):
    ResNet-18 expects ImageNet normalisation; ViT-B/32 (timm
    vit_base_patch32_224) expects [0.5,0.5,0.5] mean/std. Both backbones are
    designed for 224×224 ImageNet-sized inputs, so 32×32 (CIFAR) and 64×64
    (Tiny-ImageNet) images are ``Resize(224)``-upsampled identically.
    """
    from torchvision import transforms

    if backbone_name == "resnet18":
        extractor, in_dim = build_resnet18_extractor()
        tfm = transforms.Compose([
            transforms.Resize(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
    elif backbone_name == "vit_b32":
        extractor, in_dim = build_vit_extractor()
        tfm = transforms.Compose([
            transforms.Resize(224),
            transforms.ToTensor(),
            transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5]),
        ])
    elif backbone_name == "vit_l":
        # ViT-L/16 (issue 018 big-backbone). The timm augreg ImageNet-21k→1k
        # ViT-L checkpoint uses ImageNet mean/std normalisation (unlike the
        # vit_base_patch32_224 weights this repo loads, which expect
        # [0.5,0.5,0.5]). Resize to the backbone's native 224×224 as for the
        # other vision extractors.
        extractor, in_dim = build_vit_l_extractor()
        tfm = transforms.Compose([
            transforms.Resize(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
    else:
        raise ValueError(backbone_name)
    return extractor, in_dim, tfm


def _collate_features(extractor, ds, dev):
    """Run a torchvision dataset through a frozen extractor; return (X, y) on CPU.

    Identical to the ``collate`` helper that used to be nested inside
    ``extract_cifar10_features`` — pulled out so CIFAR-100 / Tiny-ImageNet
    share the iteration logic. ``num_workers=2`` keeps the loader behaviour
    byte-identical to the legacy CIFAR-10 path.
    """
    import torch
    from torch.utils.data import DataLoader

    loader = DataLoader(ds, batch_size=128, shuffle=False, num_workers=2)
    feats, labels = [], []
    with torch.no_grad():
        for x, y in loader:
            f = extractor(x.to(dev)).cpu()
            feats.append(f)
            labels.append(y)
    return torch.cat(feats), torch.cat(labels)


def extract_cifar10_features(
    backbone_name: str,
    data_root: str = "data",
    cache_root: str = "cache",
) -> Tuple:
    """Extract & cache CIFAR-10 features for a pretrained vision backbone.

    Returns (X_train, y_train, X_test, y_test, in_dim). Ported verbatim from
    notebook Section B.1 (same transforms, same ResNet-18 IMAGENET1K_V1 / ViT
    vit_base_patch32_224 backbones). ``download=False`` per CLAUDE.md.
    """
    import torch
    from torchvision import datasets

    cache_dir = Path(cache_root) / "features"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"cifar10_{backbone_name}.pt"
    if cache.exists():
        d = torch.load(cache)
        return d["X_train"], d["y_train"], d["X_test"], d["y_test"], d["in_dim"]

    extractor, in_dim, tfm = _build_vision_extractor(backbone_name)
    train_ds = datasets.CIFAR10(data_root, train=True, download=False, transform=tfm)
    test_ds = datasets.CIFAR10(data_root, train=False, download=False, transform=tfm)
    dev = _device()

    X_train, y_train = _collate_features(extractor, train_ds, dev)
    X_test, y_test = _collate_features(extractor, test_ds, dev)
    torch.save(
        {"X_train": X_train, "y_train": y_train, "X_test": X_test,
         "y_test": y_test, "in_dim": in_dim},
        cache,
    )
    del extractor
    torch.cuda.empty_cache()
    return X_train, y_train, X_test, y_test, in_dim


def extract_cifar100_features(
    backbone_name: str,
    data_root: str = "data",
    cache_root: str = "cache",
) -> Tuple:
    """Extract & cache CIFAR-100 features for a pretrained vision backbone (issue 012).

    Returns (X_train, y_train, X_test, y_test, in_dim). Mirrors
    ``extract_cifar10_features`` — same transforms, same ResNet-18 /
    ViT-B/32 backbones — but for the 100-class variant. CIFAR-10 saturates
    ViT linear-probe at 0.97 IID (no headroom to demonstrate distillation
    value); CIFAR-100's ~0.75-0.80 ceiling is the harder regime issue 012
    targets. ``download=False`` per CLAUDE.md (the prefetch script populates
    ``data/cifar-100-python/`` on the login node).
    """
    import torch
    from torchvision import datasets

    cache_dir = Path(cache_root) / "features"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"cifar100_{backbone_name}.pt"
    if cache.exists():
        d = torch.load(cache)
        return d["X_train"], d["y_train"], d["X_test"], d["y_test"], d["in_dim"]

    extractor, in_dim, tfm = _build_vision_extractor(backbone_name)
    train_ds = datasets.CIFAR100(data_root, train=True, download=False, transform=tfm)
    test_ds = datasets.CIFAR100(data_root, train=False, download=False, transform=tfm)
    dev = _device()

    X_train, y_train = _collate_features(extractor, train_ds, dev)
    X_test, y_test = _collate_features(extractor, test_ds, dev)
    torch.save(
        {"X_train": X_train, "y_train": y_train, "X_test": X_test,
         "y_test": y_test, "in_dim": in_dim},
        cache,
    )
    del extractor
    torch.cuda.empty_cache()
    return X_train, y_train, X_test, y_test, in_dim


def extract_tiny_imagenet_features(
    backbone_name: str,
    data_root: str = "data",
    cache_root: str = "cache",
) -> Tuple:
    """Extract & cache Tiny-ImageNet features for a pretrained vision backbone (issue 012).

    Returns (X_train, y_train, X_test, y_test, in_dim). Tiny-ImageNet is 200
    classes × 500 train images × 50 val images, native 64×64; the linear-probe
    ceiling on ImageNet-pretrained ResNet/ViT is ~0.55-0.65 (Tiny-ImageNet's
    classes overlap ImageNet so the frozen features are still informative,
    just less than on CIFAR).

    Uses ``data.load_tiny_imagenet_tensors`` to pull pre-decoded (N, 3, 64, 64)
    tensors and runs them through the frozen vision extractor in batches.
    Unlike CIFAR-10/100 (which read torchvision datasets directly under the
    ``Resize(224)``-into-PIL transform), the Tiny-ImageNet loader normalises
    on disk in ImageNet stats; here we **un-normalise** to [0,1] image space
    and re-apply the backbone's native transform pipeline so the extractor
    sees the same input distribution as the ImageNet training data — the
    cleanest way to share the existing ``_build_vision_extractor`` plumbing
    without forking transforms.

    ``download=False`` per CLAUDE.md (the prefetch script populates
    ``data/tiny-imagenet-200/`` on the login node when
    ``--include-tiny-imagenet`` is set).
    """
    import torch

    from . import data as dt

    cache_dir = Path(cache_root) / "features"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"tiny_imagenet_{backbone_name}.pt"
    if cache.exists():
        d = torch.load(cache)
        return d["X_train"], d["y_train"], d["X_test"], d["y_test"], d["in_dim"]

    # The raw loader normalises with ImageNet stats. Un-normalise before
    # passing to ``_build_vision_extractor``'s tfm (which expects PIL-ish
    # [0,1] input → its own normalisation). We do this in a small helper
    # that ingests (N, 3, 64, 64) ImageNet-normalised tensors and yields
    # back the same shape *as if* it were the ToTensor() output.
    X_train_raw, y_train, X_test_raw, y_test = dt.load_tiny_imagenet_tensors(
        data_root, cache_root)
    extractor, in_dim, _tfm_pil = _build_vision_extractor(backbone_name)
    dev = _device()

    # Tiny-ImageNet on-disk tensors are already ImageNet-normalised and
    # 64×64. For the backbone we need the *backbone's own* normalisation
    # (ImageNet for ResNet, [0.5,0.5,0.5] for ViT) at 224×224. Approach:
    # un-normalise to [0,1], optionally re-normalise to ViT stats, then
    # bilinear-resize to 224. This avoids a second PIL round-trip and works
    # on GPU.
    mean_in = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
    std_in = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
    if backbone_name == "vit_b32":
        mean_out = torch.tensor([0.5, 0.5, 0.5]).view(1, 3, 1, 1)
        std_out = torch.tensor([0.5, 0.5, 0.5]).view(1, 3, 1, 1)
    else:
        # resnet18: backbone shares ImageNet stats with the loader. We can
        # skip the un-/re-normalise pair entirely.
        mean_out = mean_in
        std_out = std_in

    def _extract_batched(X_raw, bs=128):
        import torch.nn.functional as F

        feats = []
        with torch.no_grad():
            for i in range(0, X_raw.shape[0], bs):
                x = X_raw[i:i + bs].to(dev, non_blocking=True)
                # ImageNet-norm -> [0,1] -> backbone-norm. For resnet18 this is
                # a no-op pair (mean_in/std_in == mean_out/std_out).
                x = x * std_in.to(dev) + mean_in.to(dev)
                x = (x - mean_out.to(dev)) / std_out.to(dev)
                # 64×64 -> 224×224 bilinear so the ImageNet backbones see their
                # native input size.
                x = F.interpolate(x, size=(224, 224), mode="bilinear",
                                  align_corners=False)
                f = extractor(x).cpu()
                feats.append(f)
        return torch.cat(feats)

    X_train = _extract_batched(X_train_raw)
    X_test = _extract_batched(X_test_raw)
    torch.save(
        {"X_train": X_train, "y_train": y_train, "X_test": X_test,
         "y_test": y_test, "in_dim": in_dim},
        cache,
    )
    del extractor
    torch.cuda.empty_cache()
    return X_train, y_train, X_test, y_test, in_dim


# ----------------------------------------------------------------------------
# Text feature extractors (notebook Section C.1)
# ----------------------------------------------------------------------------
def extract_text_features(
    backbone_name: str,
    task_name: str = "ag_news",
    data_root: str = "data",
    cache_root: str = "cache",
) -> Tuple:
    """Extract & cache text features for a pretrained text backbone.

    Returns (X_train, y_train, X_test, y_test, in_dim). Ported from notebook
    Section C.1.

    Pooling depends on the backbone's attention pattern:

    * **DistilBERT** is a *bidirectional* encoder: every token's hidden state
      sees the whole sentence, so a masked **mean-pool** over real tokens is a
      sound sentence embedding (verbatim from the notebook).
    * **GPT-2** is a *causal* LM: a token's hidden state attends only to itself
      and earlier tokens, so only the **last** real token has seen the entire
      sentence. The notebook mean-pooled GPT-2 over a *right-padded* causal
      sequence (pad = eos), which mixes low-context early states (and GPT-2's
      large-magnitude outlier dims) into a degenerate vector — pinning every
      GPT-2 / AG-News cell at chance (~0.25 for 4 classes), even IID α=1.0 with
      no protocol. The fix (this code) **left-pads** the tokenizer so the final
      sequence position is always a real token, then takes that last token's
      hidden state (``last_hidden_state[:, -1, :]``) as the sentence embedding.

    ``task_name`` selects the HF dataset. AG-News (default) exposes its input
    under a ``"text"`` column; DBpedia-14 (``dbpedia_14``, issue 019 Part 2,
    14 topic classes) exposes ``"title"`` + ``"content"`` and ships only a
    huge train/test split, so the text column and an optional test-subsample
    cap are resolved per-dataset below. Every other dataset keeps the verbatim
    AG-News path, so existing ``text:distilbert`` / ``text:gpt2_small`` etc.
    cells reproduce byte-for-byte.
    """
    import torch
    from transformers import AutoModel, AutoTokenizer
    from datasets import load_dataset

    cache_dir = Path(cache_root) / "features"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"{task_name}_{backbone_name}.pt"
    if cache.exists():
        d = torch.load(cache)
        return d["X_train"], d["y_train"], d["X_test"], d["y_test"], d["in_dim"]

    if backbone_name == "distilbert":
        model_id = "distilbert-base-uncased"
        causal = False
    elif backbone_name == "gpt2_small":
        model_id = "gpt2"
        causal = True
    elif backbone_name == "roberta_base":
        # RoBERTa-base (issue 019). A *bidirectional* encoder like DistilBERT,
        # so it takes the SAME masked mean-pool over real tokens (right-pad)
        # path — explicitly NOT the GPT-2 causal last-token path. 125M params,
        # 768-d hidden size. Stronger frozen AG-News linear-probe (~0.92+) than
        # the 66M DistilBERT, lifting the heterogeneous α=0.05 regime per 019.
        model_id = "roberta-base"
        causal = False
    elif backbone_name == "mpnet_st":
        # all-mpnet-base-v2 (issue 019). A sentence-transformers embedding model
        # whose training-time pooling is a masked mean over the last hidden
        # state — exactly the bidirectional mean-pool path below (right-pad), so
        # NO sentence-transformers package is needed: the plain transformers
        # AutoModel/AutoTokenizer + the existing manual mean-pool reproduce its
        # embedding. 768-d, purpose-built for linearly-separable sentence
        # embeddings → strongest frozen AG-News linear-probe candidate (≥0.93).
        model_id = "sentence-transformers/all-mpnet-base-v2"
        causal = False
    elif backbone_name == "bert_large":
        # BERT-large-uncased (issue 018 big-backbone). Like DistilBERT it is a
        # *bidirectional* encoder, so masked mean-pool over real tokens is the
        # sound sentence embedding and default right-padding is fine. 1024-d
        # hidden size (vs DistilBERT's 768).
        model_id = "bert-large-uncased"
        causal = False
    elif backbone_name == "gpt2_medium":
        # GPT-2-medium (issue 018 big-backbone). Same *causal* LM family as
        # gpt2_small, so it inherits the issue-002 left-pad + last-token pooling
        # fix below (NOT mean-pool, which pins GPT-2 at chance). 1024-d hidden
        # size (vs gpt2_small's 768).
        model_id = "gpt2-medium"
        causal = True
    else:
        raise ValueError(backbone_name)

    tok = AutoTokenizer.from_pretrained(model_id)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    # GPT-2 fix: left-pad so the LAST sequence position is always a real token
    # (the final token of the sentence, which has attended to the whole sequence
    # under causal attention). DistilBERT keeps its default right padding —
    # bidirectional mean-pooling is unaffected by pad side.
    if causal:
        tok.padding_side = "left"
    dev = _device()
    model = AutoModel.from_pretrained(model_id).to(dev).eval()
    in_dim = model.config.hidden_size if hasattr(model.config, "hidden_size") else 768

    # Robust dataset id. Newer ``datasets`` (e.g. on Colab) reject the bare
    # canonical name with ``HfUriError: ... Repository id must be 'namespace/name',
    # got 'ag_news'`` and require a namespaced repo id; VALAR's older ``datasets``
    # (and the existing feature cache, which short-circuits this call) use the bare
    # name. Try the bare name first (byte-identical on VALAR), then fall back to the
    # namespaced canonical mirror so the same code runs on Colab unchanged.
    _DS_FALLBACK = {"ag_news": "fancyzhx/ag_news", "dbpedia_14": "fancyzhx/dbpedia_14"}
    try:
        ds = load_dataset(task_name)
    except Exception:
        _alt = _DS_FALLBACK.get(task_name)
        if _alt is None:
            raise
        ds = load_dataset(_alt)
    if task_name == "dbpedia_14":
        # DBpedia-14 (issue 019 Part 2). 14 topic classes; columns are
        # ``title`` + ``content`` (no ``text`` column). Compose the input as
        # "<title>. <content>" — the standard DBpedia text-classification
        # input. The test split is 70k; subsample to 10k (seeded) for speed,
        # matching the issue's "subsample test to ~10k" instruction. The train
        # split (560k) is consumed in full — the protocol's probe/partition
        # logic downstream selects from it. Labels are already 0..13.
        def _dbpedia_text(split):
            titles = split["title"]
            contents = split["content"]
            return [f"{t}. {c}" for t, c in zip(titles, contents)]

        train_texts = _dbpedia_text(ds["train"])
        train_labels = torch.tensor(ds["train"]["label"], dtype=torch.long)
        test_split = ds["test"]
        if len(test_split) > 10000:
            import numpy as _np
            rng = _np.random.RandomState(12345)
            idx = rng.choice(len(test_split), size=10000, replace=False)
            idx = sorted(int(i) for i in idx)
            test_split = test_split.select(idx)
        test_texts = _dbpedia_text(test_split)
        test_labels = torch.tensor(test_split["label"], dtype=torch.long)
    else:
        # AG-News (default) and any other ``text``-column HF dataset — verbatim
        # legacy path, so existing text:distilbert/gpt2_small/bert_large cells
        # reproduce byte-for-byte.
        train_texts = ds["train"]["text"]
        train_labels = torch.tensor(ds["train"]["label"], dtype=torch.long)
        test_texts = ds["test"]["text"]
        test_labels = torch.tensor(ds["test"]["label"], dtype=torch.long)

    def extract(texts, bs=32, max_len=128):
        feats = []
        with torch.no_grad():
            for i in range(0, len(texts), bs):
                batch = texts[i:i + bs]
                enc = tok(batch, padding=True, truncation=True, max_length=max_len,
                          return_tensors="pt").to(dev)
                out = model(**enc)
                last = out.last_hidden_state
                if causal:
                    # GPT-2: last real token. Under left padding the final
                    # position (-1) is always the sentence's last token.
                    pooled = last[:, -1, :]
                else:
                    # DistilBERT: masked mean-pool over real tokens (unchanged).
                    mask = enc["attention_mask"].unsqueeze(-1).float()
                    pooled = (last * mask).sum(1) / mask.sum(1).clamp_min(1)
                feats.append(pooled.cpu())
        return torch.cat(feats)

    X_train = extract(train_texts)
    X_test = extract(test_texts)
    torch.save(
        {"X_train": X_train, "y_train": train_labels, "X_test": X_test,
         "y_test": test_labels, "in_dim": in_dim},
        cache,
    )
    del model
    torch.cuda.empty_cache()
    return X_train, train_labels, X_test, test_labels, in_dim
