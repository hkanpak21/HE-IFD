"""Login-node prefetch of pretrained weights + HF datasets into local caches.

Run ONCE on the VALAR **login node** (which has internet); compute nodes then
load everything offline (HF_HUB_OFFLINE=1 / local_files_only). This is the
sanctioned login-node exception in CLAUDE.md — it is DOWNLOAD-ONLY (no forward
pass, no training), it just populates ~/.cache/huggingface and
~/.cache/torch/hub/checkpoints so the pretrained sweeps don't try to download
from a compute node (which has no internet and would blow the 3h job cap).

    cd /scratch/hkanpak21/HE_IFD && python jobs/prefetch_login.py

Datasets MNIST / FashionMNIST / CIFAR-10 are already on VALAR under data/ —
not fetched here. Only AG News (HF) + the four pretrained backbones are.
"""
from __future__ import annotations

import os
import sys

# Make the repo root (parent of jobs/) importable so `import src.*` resolves
# regardless of cwd / launcher (python jobs/prefetch_login.py, setsid, etc.).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> None:
    # AG News dataset (the only dataset not already under data/).
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

    print("[prefetch] PREFETCH DONE", flush=True)


if __name__ == "__main__":
    main()
