"""Regression tests for ``src.backbones`` feature extractors.

Issue 002: the notebook mean-pooled GPT-2's ``last_hidden_state`` over a
*right-padded causal* sequence (pad = eos), producing degenerate sentence
embeddings that pinned every GPT-2 / AG-News cell at chance (~0.25 for 4
classes) — including the IID, no-protocol setting. The fix left-pads the
tokenizer and takes the last real token's hidden state.

This module's job is to make that bug *impossible to reintroduce silently*:
``test_gpt2_iid_accuracy_above_chance`` trains a plain linear head (the protocol's
own ``ClassifierHead``) on GPT-2 features of a small AG-News subset — IID, no
Phase 0, no distillation, no partition — and asserts the test accuracy clears a
floor (0.80) that sits far above the 0.25 chance line. On the old mean-pool code
the features are near-degenerate and accuracy collapses toward chance, so the
assertion FAILS; on the left-pad + last-token fix the features are linearly
separable and accuracy lands in the ~0.90 band, so it PASSES.

The DistilBERT companion test confirms the bidirectional mean-pool path is
unchanged (it must also clear the floor).

HARD ENV NOTE: this requires torch + transformers + datasets and the GPT-2 /
DistilBERT weights + the AG-News dataset cached on disk. None of that exists on
the local dev Mac, so every test here is guarded with ``pytest.importorskip`` and
an offline-weight probe that ``pytest.skip``s rather than triggering a download.
Run it on a VALAR compute node (``sbatch`` / short ``srun``) with the weights and
dataset pre-fetched on the login node and ``HF_HUB_OFFLINE=1`` set.
"""
from __future__ import annotations

import pytest

# Skip the whole module unless the heavy deps are importable (login-node / local
# Mac have none of these). importorskip raises pytest.Skipped at collection time.
torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("datasets")


# Number of classes in AG News (World / Sports / Business / Sci-Tech).
_AG_NEWS_NUM_CLASSES = 4
# Accuracy floor for the regression assertion: well above the 0.25 chance line,
# comfortably below the ~0.90 a healthy GPT-2 linear probe reaches on AG News.
_ACC_FLOOR = 0.80
# Subset sizes (kept small so the test is fast; balanced across the 4 classes).
_TRAIN_PER_CLASS = 200   # 800 train rows
_TEST_PER_CLASS = 150    # 600 test rows


def _weights_available(model_id: str) -> bool:
    """True iff the HF weights for ``model_id`` can be loaded offline.

    Probes only the lightweight config so we never download a full checkpoint
    just to decide whether to skip. Compute nodes have no internet, so a test
    that cannot load offline must skip, not hang.
    """
    try:
        from transformers import AutoConfig

        AutoConfig.from_pretrained(model_id, local_files_only=True)
        return True
    except Exception:
        return False


def _balanced_subset(texts, labels, num_classes, per_class):
    """Deterministic balanced slice: the first ``per_class`` rows of each label.

    Returns ({"text": [...], "label": [...]}) shaped like a HF dataset split so
    the patched ``load_dataset`` can hand it straight back. Stable across runs
    (no RNG) so the test is reproducible.
    """
    buckets = {c: [] for c in range(num_classes)}
    for t, y in zip(texts, labels):
        y = int(y)
        if y in buckets and len(buckets[y]) < per_class:
            buckets[y].append(t)
    out_texts, out_labels = [], []
    for c in range(num_classes):
        out_texts.extend(buckets[c])
        out_labels.extend([c] * len(buckets[c]))
    return {"text": out_texts, "label": out_labels}


@pytest.fixture()
def small_agnews(monkeypatch):
    """Patch ``datasets.load_dataset`` to return a small *balanced* AG-News subset.

    Loads the genuine AG-News text once via the original ``load_dataset`` (the
    cache pre-fetched on the VALAR login node), then trims it to a few hundred
    balanced rows per split so the extractor runs in seconds instead of over the
    full 120k-row corpus. ``backbones.extract_text_features`` does a function-body
    ``from datasets import load_dataset``, which resolves ``datasets.load_dataset``
    at call time — so patching the module attribute is sufficient.
    """
    import datasets as _ds

    real_load = _ds.load_dataset

    full = real_load("ag_news")
    train = _balanced_subset(
        full["train"]["text"], full["train"]["label"],
        _AG_NEWS_NUM_CLASSES, _TRAIN_PER_CLASS,
    )
    test = _balanced_subset(
        full["test"]["text"], full["test"]["label"],
        _AG_NEWS_NUM_CLASSES, _TEST_PER_CLASS,
    )
    subset = {"train": train, "test": test}

    def _fake_load_dataset(name, *args, **kwargs):
        assert name == "ag_news", f"unexpected dataset {name!r}"
        return subset

    monkeypatch.setattr(_ds, "load_dataset", _fake_load_dataset)
    return subset


def _linear_probe_accuracy(backbone_name, cache_root):
    """Extract features for ``backbone_name`` and return IID linear-probe accuracy.

    This is the 'IID / no-protocol' configuration: features are extracted via the
    public ``extract_text_features`` interface, a single linear head is trained on
    the whole train subset (no Phase 0, no distillation, no Dirichlet partition),
    and accuracy is measured on the held-out test subset. Exercises exactly the
    pooling path under test, plus the protocol's own ``ClassifierHead`` and SGD
    trainer, through their public interfaces.
    """
    from src.backbones import extract_text_features, make_head
    from src.teacher import train_supervised_model
    from src.evaluate import accuracy_on

    X_tr, y_tr, X_te, y_te, in_dim = extract_text_features(
        backbone_name, "ag_news", data_root="data", cache_root=str(cache_root)
    )

    make_model_fn = make_head(in_dim, _AG_NEWS_NUM_CLASSES)
    # Standardise features so a fixed LR converges regardless of backbone scale.
    mu = X_tr.mean(0, keepdim=True)
    sd = X_tr.std(0, keepdim=True).clamp_min(1e-6)
    X_tr = (X_tr - mu) / sd
    X_te = (X_te - mu) / sd

    head = train_supervised_model(
        make_model_fn, X_tr, y_tr,
        epochs=60, lr=0.05, momentum=0.9, bs=64, seed=0,
    )
    return accuracy_on(head, X_te, y_te)


def test_gpt2_iid_accuracy_above_chance(small_agnews, tmp_path):
    """GPT-2 IID/no-protocol linear-probe accuracy must clear the 0.80 floor.

    FAILS on the old mean-pool-over-right-padded-causal code (features degenerate,
    accuracy ~chance ~0.25); PASSES on the left-pad + last-token fix (~0.90).
    """
    if not _weights_available("gpt2"):
        pytest.skip("gpt2 weights not cached offline; pre-fetch on the login node")

    acc = _linear_probe_accuracy("gpt2_small", tmp_path)
    chance = 1.0 / _AG_NEWS_NUM_CLASSES
    assert acc >= _ACC_FLOOR, (
        f"GPT-2 IID accuracy {acc:.4f} is below the {_ACC_FLOOR:.2f} floor "
        f"(chance={chance:.2f}); the left-pad + last-token pooling fix has "
        f"regressed back toward the mean-pool bug."
    )


def test_distilbert_iid_accuracy_unaffected(small_agnews, tmp_path):
    """DistilBERT mean-pool path is unchanged and also clears the floor.

    Guards the fix's other half of the acceptance criterion: the bidirectional
    encoder's masked mean-pool must still produce strong sentence embeddings.
    """
    if not _weights_available("distilbert-base-uncased"):
        pytest.skip("distilbert weights not cached offline; pre-fetch on the login node")

    acc = _linear_probe_accuracy("distilbert", tmp_path)
    assert acc >= _ACC_FLOOR, (
        f"DistilBERT IID accuracy {acc:.4f} is below the {_ACC_FLOOR:.2f} floor; "
        f"the bidirectional mean-pool path should be unaffected by issue 002."
    )
