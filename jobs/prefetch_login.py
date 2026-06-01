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
    # issue 018 Part A (ViT-L needs CIFAR-100 too):
    cd /scratch/hkanpak21/HE_IFD && python jobs/prefetch_login.py --include-cifar100 --include-big-backbones
    # issue ft02 harder datasets (text always-fetchable; FGVC via live mirror;
    # CUB/Cars are manual — see src/data.py loader docstrings):
    cd /scratch/hkanpak21/HE_IFD && python jobs/prefetch_login.py --include-text019 --include-ft02-text --include-ft02-fgvc

Datasets MNIST / FashionMNIST / CIFAR-10 are already on VALAR under data/ —
not fetched here. AG News (HF), the four pretrained backbones, plus the
optional CIFAR-100 + Tiny-ImageNet datasets (issue 012, harder-vision-dataset
extension) and the optional big backbones (issue 018: ViT-L, BERT-large,
GPT-2-medium, behind --include-big-backbones) are.
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
    p.add_argument("--include-big-backbones", action="store_true",
                   help="Also fetch the issue-018 big pretrained backbones "
                        "(ViT-L/16 ~1.2GB via timm, BERT-large-uncased ~1.3GB, "
                        "GPT-2-medium ~1.5GB via HF). Idempotent (each loader "
                        "is a cache no-op if the weights are already present). "
                        "Off by default so the normal prefetch is unchanged.")
    p.add_argument("--include-text019", action="store_true",
                   help="Also fetch the issue-019 strong frozen text backbones "
                        "(roberta-base ~0.5GB, sentence-transformers/"
                        "all-mpnet-base-v2 ~0.4GB via plain HF AutoModel — NO "
                        "sentence-transformers package needed) plus the "
                        "DBpedia-14 HF dataset (~70MB). Idempotent. Off by "
                        "default so the normal prefetch is unchanged.")
    p.add_argument("--include-ft02-text", action="store_true",
                   help="Also fetch the issue-ft02 harder TEXT datasets: "
                        "Banking77 (~5MB), 20-Newsgroups (SetFit mirror, ~50MB), "
                        "TREC (~1MB) HF datasets. Idempotent. (The frozen text "
                        "backbones roberta-base / all-mpnet-base-v2 come with "
                        "--include-text019.) Off by default.")
    p.add_argument("--include-ft02-fgvc", action="store_true",
                   help="Also fetch FGVC-Aircraft (~2.7GB, VGG mirror live via "
                        "torchvision) — the one ft02 fine-grained-vision dataset "
                        "with a working auto-download. CUB-200 and Stanford Cars "
                        "have dead/manual mirrors and must be placed by hand (see "
                        "src/data.py loader docstrings for the curl/Kaggle "
                        "commands). Idempotent. Off by default.")
    return p.parse_args()


def _prefetch_ft02_text() -> None:
    """Fetch the issue-ft02 harder many-class TEXT datasets into the HF cache.

    Login-node only (DOWNLOAD-ONLY, no compute). Idempotent: each
    ``load_dataset`` is a cache hit once present. Pulls:
      * Banking77      (HF ``PolyAI/banking77``; 77 intents; ~5MB)
                       LICENSE: CC-BY-4.0 (PolyAI). Cite Casanueva et al. 2020.
      * 20-Newsgroups  (HF ``SetFit/20_newsgroups``; 20 topics; ~50MB)
                       LICENSE: public domain / research (the classic 20NG corpus,
                       Lang 1995). Cite the 20 Newsgroups dataset.
      * TREC           (HF ``CogComp/trec``; 6 coarse / 50 fine classes; ~1MB)
                       LICENSE: research use (Li & Roth 2002). Cite TREC QC.
    The 3 namespaced ids match ``src.backbones.extract_text_features``'s
    ``_DS_FALLBACK`` so the same code loads them offline on the compute node.
    """
    from datasets import load_dataset
    for ds_id in ("PolyAI/banking77", "SetFit/20_newsgroups", "CogComp/trec"):
        load_dataset(ds_id)
        print(f"[prefetch] hf dataset {ds_id} ok", flush=True)


def _prefetch_ft02_fgvc(data_root: str) -> None:
    """Trigger torchvision's FGVC-Aircraft download once (VGG mirror is live).

    Login-node only. Idempotent: torchvision skips the download if the
    ``fgvc-aircraft-2013b`` tree is already present. Pulls both the ``trainval``
    and ``test`` splits so the compute node loads offline with download=False.
    LICENSE: research / non-commercial (Maji et al. 2013). ~2.7GB.

    NOTE: CUB-200-2011 and Stanford Cars are NOT auto-fetchable here — CUB has no
    torchvision class (manual curl from the Caltech mirror) and the Stanford Cars
    torchvision URL is dead (manual Kaggle/HF placement). Their exact fetch
    commands live in the ``src.data.make_cub200_datasets`` /
    ``make_stanford_cars_datasets`` docstrings; run them by hand on the login node.
    """
    from torchvision.datasets import FGVCAircraft

    Path(data_root).mkdir(parents=True, exist_ok=True)
    FGVCAircraft(root=data_root, split="trainval", download=True)
    FGVCAircraft(root=data_root, split="test", download=True)
    print(f"[prefetch] fgvc-aircraft ok ({data_root}/fgvc-aircraft-2013b/)",
          flush=True)


def _prefetch_big_backbones() -> None:
    """Download the issue-018 big backbones into the HF/timm caches (no compute).

    Idempotent: each ``from_pretrained`` / ``timm.create_model(pretrained=True)``
    is a cache hit (no network) once the weights are present. Pulls:
      * ViT-L/16  (timm ``vit_large_patch16_224``, ~1.2GB)
      * BERT-large-uncased  (HF, ~1.3GB)
      * GPT-2-medium  (HF, ~1.5GB)
    These are the Large variants of the existing ViT/BERT-family/GPT-2
    extractors; the feature-extraction code paths in ``src.backbones`` are the
    same (timm num_classes=0 / HF AutoModel), only the model id differs.
    """
    from transformers import AutoModel, AutoTokenizer
    for mid in ("bert-large-uncased", "gpt2-medium"):
        AutoTokenizer.from_pretrained(mid)
        AutoModel.from_pretrained(mid)
        print(f"[prefetch] hf {mid} ok", flush=True)

    import src.backbones as bk
    bk.build_vit_l_extractor()
    print("[prefetch] vit_l ok", flush=True)


def _prefetch_text019() -> None:
    """Download the issue-019 strong frozen text backbones + DBpedia-14 dataset
    into the HF caches (no compute, login-node only).

    Idempotent: each ``from_pretrained`` / ``load_dataset`` is a cache hit once
    present. Both models load via plain ``transformers`` AutoModel/AutoTokenizer
    — the ``sentence-transformers`` package is NOT required (the masked mean-pool
    in ``src.backbones.extract_text_features`` reproduces all-mpnet-base-v2's
    embedding). Pulls:
      * roberta-base                               (HF, ~0.5GB)
      * sentence-transformers/all-mpnet-base-v2    (HF, ~0.4GB)
      * dbpedia_14                                 (HF dataset, ~70MB)
    """
    from transformers import AutoModel, AutoTokenizer
    for mid in ("roberta-base", "sentence-transformers/all-mpnet-base-v2"):
        AutoTokenizer.from_pretrained(mid)
        AutoModel.from_pretrained(mid)
        print(f"[prefetch] hf {mid} ok", flush=True)

    from datasets import load_dataset
    load_dataset("dbpedia_14")
    print("[prefetch] dbpedia_14 ok", flush=True)


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

    # Optional, issue-018 big-backbone extension (ViT-L, BERT-large, GPT-2-medium).
    if args.include_big_backbones:
        _prefetch_big_backbones()

    # Optional, issue-019 strong-text-backbone extension (roberta-base,
    # all-mpnet-base-v2, DBpedia-14).
    if args.include_text019:
        _prefetch_text019()

    # Optional, issue-ft02 harder-dataset extension.
    if args.include_ft02_text:
        _prefetch_ft02_text()
    if args.include_ft02_fgvc:
        _prefetch_ft02_fgvc(args.data_root)

    print("[prefetch] PREFETCH DONE", flush=True)


if __name__ == "__main__":
    main()
