"""Login-node prefetch of pretrained weights + HF datasets into local caches.

Run ONCE on the VALAR **login node** (which has internet); compute nodes then
load everything offline (HF_HUB_OFFLINE=1 / local_files_only). This is the
sanctioned login-node exception in CLAUDE.md — it is DOWNLOAD-ONLY (no forward
pass, no training), it just populates ~/.cache/huggingface and
~/.cache/torch/hub/checkpoints so the pretrained sweeps don't try to download
from a compute node (which has no internet and would blow the 3h job cap).

    cd /scratch/hkanpak21/HE_IFD && python jobs/prefetch_login.py
    cd /scratch/hkanpak21/HE_IFD && python jobs/prefetch_login.py --include-cifar100
    cd /scratch/hkanpak21/HE_IFD && python jobs/prefetch_login.py --include-cifar100 --include-tiny-imagenet

Datasets MNIST / FashionMNIST / CIFAR-10 are already on VALAR under data/ —
not fetched here. AG News (HF), the four pretrained backbones, plus the
optional CIFAR-100 + Tiny-ImageNet datasets (issue 012, harder-vision-dataset
extension) are.
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

# Make the repo root (parent of jobs/) importable so `import src.*` resolves
# regardless of cwd / launcher (python jobs/prefetch_login.py, setsid, etc.).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _prefetch_cifar100(data_root: str) -> None:
    """Trigger torchvision's CIFAR-100 download once so compute nodes can load
    offline (download=False). Idempotent: torchvision skips the download if the
    python batches are already on disk.
    """
    from torchvision.datasets import CIFAR100

    Path(data_root).mkdir(parents=True, exist_ok=True)
    CIFAR100(root=data_root, train=True, download=True)
    CIFAR100(root=data_root, train=False, download=True)
    print(f"[prefetch] cifar100 ok ({data_root}/cifar-100-python/)", flush=True)


def _prefetch_tiny_imagenet(data_root: str) -> None:
    """Download + extract Stanford CS231n Tiny-ImageNet-200 (~250MB on disk).

    Idempotent: skipped entirely if ``data/tiny-imagenet-200/wnids.txt``
    already exists (the canonical sentinel for a complete extraction).

    Layout after extraction:
        data/tiny-imagenet-200/
            wnids.txt
            train/<wnid>/images/<filename>.JPEG
            val/images/<filename>.JPEG
            val/val_annotations.txt
    """
    out_dir = Path(data_root) / "tiny-imagenet-200"
    sentinel = out_dir / "wnids.txt"
    if sentinel.exists():
        print(f"[prefetch] tiny-imagenet already present at {out_dir} (skip)",
              flush=True)
        return

    url = "http://cs231n.stanford.edu/tiny-imagenet-200.zip"
    Path(data_root).mkdir(parents=True, exist_ok=True)
    zip_path = Path(data_root) / "tiny-imagenet-200.zip"

    if not zip_path.exists():
        print(f"[prefetch] tiny-imagenet downloading from {url} -> {zip_path}",
              flush=True)
        urllib.request.urlretrieve(url, str(zip_path))
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"[prefetch] tiny-imagenet download done ({size_mb:.1f} MB)",
              flush=True)
    else:
        print(f"[prefetch] tiny-imagenet zip already at {zip_path} (skip dl)",
              flush=True)

    print(f"[prefetch] tiny-imagenet extracting into {data_root}/", flush=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(data_root)
    if not sentinel.exists():
        # Defensive: if the extraction did not produce the expected layout,
        # fail loudly rather than letting downstream loaders silently 404.
        raise RuntimeError(
            f"Tiny-ImageNet extraction completed but {sentinel} not found. "
            f"The CS231n zip may have changed layout."
        )
    # Keep the zip around (idempotent re-runs skip re-download); user can
    # delete it manually to reclaim ~250MB if desired.
    print(f"[prefetch] tiny-imagenet ok ({out_dir})", flush=True)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=("Login-node prefetch (no compute). Always pulls AG News + "
                     "the four pretrained backbones (ViT-B/32, ResNet-18, "
                     "DistilBERT, GPT-2). Optional flags pull the harder "
                     "vision datasets used by issue 012."))
    p.add_argument("--data-root", type=str, default="data",
                   help="Root for torchvision/Tiny-ImageNet downloads "
                        "(default: data/ relative to cwd).")
    p.add_argument("--include-cifar100", action="store_true",
                   help="Also fetch CIFAR-100 (~170MB). Idempotent.")
    p.add_argument("--include-tiny-imagenet", action="store_true",
                   help="Also fetch + extract Tiny-ImageNet-200 (~250MB). "
                        "Idempotent (skipped if already extracted).")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # AG News dataset (the only HF dataset always pre-fetched here).
    from datasets import load_dataset
    load_dataset("ag_news")
    print("[prefetch] ag_news ok", flush=True)

    # Text backbones (DistilBERT, GPT-2) — tokenizer + weights.
    from transformers import AutoModel, AutoTokenizer
    for mid in ("distilbert-base-uncased", "gpt2"):
        AutoTokenizer.from_pretrained(mid)
        AutoModel.from_pretrained(mid)
        print(f"[prefetch] hf {mid} ok", flush=True)

    # Vision backbones — download exactly what src/backbones builds/uses.
    import src.backbones as bk
    bk.build_resnet18_extractor()
    print("[prefetch] resnet18 ok", flush=True)
    bk.build_vit_extractor()
    print("[prefetch] vit ok", flush=True)

    # Optional, issue-012 harder-vision-dataset extension.
    if args.include_cifar100:
        _prefetch_cifar100(args.data_root)
    if args.include_tiny_imagenet:
        _prefetch_tiny_imagenet(args.data_root)

    print("[prefetch] PREFETCH DONE", flush=True)


if __name__ == "__main__":
    main()
