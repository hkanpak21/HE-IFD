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
    from torch.utils.data import DataLoader
    from torchvision import datasets, transforms

    cache_dir = Path(cache_root) / "features"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"cifar10_{backbone_name}.pt"
    if cache.exists():
        d = torch.load(cache)
        return d["X_train"], d["y_train"], d["X_test"], d["y_test"], d["in_dim"]

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
    else:
        raise ValueError(backbone_name)

    train_ds = datasets.CIFAR10(data_root, train=True, download=False, transform=tfm)
    test_ds = datasets.CIFAR10(data_root, train=False, download=False, transform=tfm)
    dev = _device()

    def collate(ds):
        loader = DataLoader(ds, batch_size=128, shuffle=False, num_workers=2)
        feats, labels = [], []
        with torch.no_grad():
            for x, y in loader:
                f = extractor(x.to(dev)).cpu()
                feats.append(f)
                labels.append(y)
        return torch.cat(feats), torch.cat(labels)

    X_train, y_train = collate(train_ds)
    X_test, y_test = collate(test_ds)
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

    ds = load_dataset(task_name)
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
