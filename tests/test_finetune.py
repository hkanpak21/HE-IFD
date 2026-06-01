"""Behaviour tests for the issue-ft01 fine-tuning pivot.

Two contracts under test (issue ft01 "What to build" §4):

(a) **`aggregate` is byte-compatible with the LoRA(+head) displacement.** The
    server combine (``src.aggregate.aggregate``) is the depth-1 task-arithmetic
    crypto contract and is UNCHANGED by ft01. A LoRA+head cumulative displacement
    is just a ``state_dict``-shaped param dict with extra tensors; because
    ``aggregate`` iterates element-wise (PT-scalar × CT + CT + CT) over every
    tensor key, a LoRA+head Δ aggregates IDENTICALLY to a head-only Δ that
    carries the same total scalar count laid out as one flat tensor. This test
    pins that equivalence at the public ``aggregate`` interface — so the
    "flatten/reshape contract" (Δ is a dict of trainable tensors; aggregate is
    key-wise linear) keeps the LoRA path byte-compatible without ANY change to
    ``aggregate``.

(b) **LoRA fine-tuning actually fine-tunes.** ``local_finetune_trajectory`` with
    the LoRA(+head) trainable unit (i) genuinely trains the adapter — the LoRA
    ``lora_B.weight`` starts at zero and is NON-zero after the bounded trajectory
    — and (ii) reaches IID accuracy at least as high as the head-only linear
    probe fine-tuned under the SAME budget on a small hard-task subset. (In
    cached-feature space the LoRA head is still a linear map, so its win over the
    linear probe is capacity/optimisation, not expressivity; the load-bearing
    "LoRA actually fine-tunes" signal is the non-zero, accuracy-non-decreasing
    adapter.) Both assertions go through the public ``local_finetune_trajectory``
    + ``backbones.make_trainable_unit`` interfaces.

HARD ENV NOTE: every test needs a tensor backend (``aggregate``/the trajectory
operate on torch param dicts and call ``.backward()``). torch is therefore
imported via ``pytest.importorskip`` so a collection pass on the local dev Mac
(no torch) SKIPS rather than errors. NONE of these tests needs a pretrained
backbone, a dataset, or a GPU — they run on tiny synthetic CPU tensors — so on
Colab / VALAR (where torch is present) the whole module runs in seconds.
"""
from __future__ import annotations

import pytest


# --- tiny helpers -----------------------------------------------------------
def _allclose_dict(torch, a, b, *, atol=1e-6, rtol=1e-5):
    assert a.keys() == b.keys()
    return all(torch.allclose(a[k], b[k], atol=atol, rtol=rtol) for k in a)


def _flat(torch, d):
    """Concatenate a param dict into one flat vector in sorted-key order."""
    return torch.cat([d[k].reshape(-1) for k in sorted(d.keys())])


# ===========================================================================
# (a) aggregate on a LoRA+head displacement == aggregate on a head-only
#     displacement of the same flattened length (task-arithmetic invariant).
# ===========================================================================
def test_aggregate_lora_head_equals_flat_head_of_same_length():
    """A LoRA+head Δ and a single flat head Δ of the SAME total scalar count
    aggregate to byte-identical flat vectors.

    Construction: a realistic resnet18-scale LoRA(+head) param spec
        fc.weight (nc×in), fc.bias (nc), lora_A.weight (r×in), lora_B.weight (nc×r)
    has ``P`` total trainable scalars. We build per-client displacements over
    that spec, run them through ``aggregate``, then ALSO pack the very same
    scalars (θ₀ and each Δ_i) into a single ``{"flat": (P,)}`` head-only spec and
    aggregate THAT. The flattened outputs must match to floating tolerance —
    proving ``aggregate`` is invariant to how the P scalars are partitioned into
    tensors, i.e. the LoRA layout is byte-compatible with the existing head
    layout under the unchanged depth-1 combine.
    """
    torch = pytest.importorskip("torch")
    from src.aggregate import aggregate, sample_weights

    in_dim, nc, rank = 512, 10, 8
    # LoRA(+head) trainable-unit spec — exactly the tensors make_lora_head puts
    # in state_dict (fc.weight, fc.bias, lora_A.weight, lora_B.weight).
    lora_spec = {
        "fc.weight": (nc, in_dim),
        "fc.bias": (nc,),
        "lora_A.weight": (rank, in_dim),
        "lora_B.weight": (nc, rank),
    }
    P = sum(int(torch.empty(s).numel()) for s in lora_spec.values())

    torch.manual_seed(2026)
    n_clients = 4
    theta0_lora = {name: torch.randn(*shape) for name, shape in lora_spec.items()}
    deltas_lora = [
        {name: torch.randn(*shape) for name, shape in lora_spec.items()}
        for _ in range(n_clients)
    ]
    w = sample_weights([10, 20, 30, 40])  # asymmetric sample weights

    out_lora = aggregate(theta0_lora, deltas_lora, w)

    # Re-pack the SAME scalars into a single flat head-only tensor of length P,
    # preserving the sorted-key concatenation order so the values line up 1:1.
    theta0_flat = {"flat": _flat(torch, theta0_lora)}
    deltas_flat = [{"flat": _flat(torch, d)} for d in deltas_lora]
    assert theta0_flat["flat"].numel() == P
    out_flat = aggregate(theta0_flat, deltas_flat, w)

    # The flattened LoRA+head aggregate must equal the flat head-only aggregate
    # element-for-element: aggregate did the SAME PT×CT + CT+CT on each scalar,
    # regardless of the tensor partitioning. This is the byte-compatibility claim.
    assert torch.allclose(
        _flat(torch, out_lora), out_flat["flat"], atol=1e-6, rtol=1e-5)

    # And the LoRA aggregate equals the hand-computed linear reference built with
    # ONLY the FHE-legal primitives (CT+CT, PT×CT) — so no hidden non-linearity
    # crept in for the extra LoRA tensors.
    ref = {name: theta0_lora[name].clone() for name in lora_spec}
    for i in range(n_clients):
        for name in lora_spec:
            ref[name] = ref[name] + w[i] * deltas_lora[i][name]  # CT+CT ; PT×CT
    assert _allclose_dict(torch, out_lora, ref, atol=1e-6, rtol=1e-5)
    # Shapes/keys preserved (no reshape/pad/subset of state_dict).
    assert set(out_lora.keys()) == set(lora_spec.keys())
    for name, shape in lora_spec.items():
        assert tuple(out_lora[name].shape) == shape


def test_lora_head_displacement_flows_through_run_cell_aggregate_path():
    """End-to-end *layout* check: the displacement a real LoRA(+head) unit
    produces has exactly the tensor keys ``aggregate`` will combine, and those
    keys are a strict superset of the head-only unit's keys (the head plus the
    two adapter matrices). Confirms the flatten/reshape contract the protocol
    relies on: every trainable tensor is in the dict ``aggregate`` iterates.
    """
    torch = pytest.importorskip("torch")
    from src.backbones import get_params, make_trainable_unit

    in_dim, nc = 32, 4
    head_fn = make_trainable_unit(in_dim, nc, "head")
    lora_fn = make_trainable_unit(in_dim, nc, "lora")  # bare lora -> rank 8

    head_keys = set(get_params(head_fn()).keys())
    lora_keys = set(get_params(lora_fn()).keys())

    # head_only is the legacy linear head: exactly fc.weight + fc.bias.
    assert head_keys == {"fc.weight", "fc.bias"}
    # LoRA unit carries the head PLUS the two adapter matrices — and nothing the
    # aggregate cannot combine element-wise (no buffers that would change algebra;
    # the scaling is a plain python float, NOT a state_dict entry).
    assert {"fc.weight", "fc.bias", "lora_A.weight", "lora_B.weight"} <= lora_keys
    assert lora_keys >= head_keys


# ===========================================================================
# (b) LoRA fine-tuning actually fine-tunes (adapter trains; acc ≥ head-only).
# ===========================================================================
def _make_separable_blobs(torch, *, n_per_class, in_dim, nc, seed):
    """Deterministic linearly-separable multi-class blobs in feature space.

    Each class is a tight Gaussian around a distinct random mean. Returned
    (X, y) live on CPU; the trajectory moves them to-device internally.
    """
    g = torch.Generator().manual_seed(seed)
    means = torch.randn(nc, in_dim, generator=g) * 4.0
    xs, ys = [], []
    for c in range(nc):
        blob = means[c][None, :] + 0.5 * torch.randn(
            n_per_class, in_dim, generator=g)
        xs.append(blob)
        ys.append(torch.full((n_per_class,), c, dtype=torch.long))
    X = torch.cat(xs)
    y = torch.cat(ys)
    # Shuffle so minibatches are class-mixed.
    perm = torch.randperm(X.shape[0], generator=g)
    return X[perm], y[perm]


def test_lora_finetune_trains_adapter_and_matches_head_probe():
    """``local_finetune_trajectory`` on the LoRA unit (i) moves the adapter off
    its zero init and (ii) reaches IID accuracy ≥ the head-only linear probe
    fine-tuned under the SAME bounded budget — i.e. LoRA actually fine-tunes.

    Public interfaces only: ``backbones.make_trainable_unit`` (the unit
    factories) + ``distill.local_finetune_trajectory`` (the headline local step)
    + ``evaluate.accuracy_on``. No teacher, no backbone weights, no dataset — a
    tiny separable synthetic task stands in for the "small hard-task subset", so
    the regression is deterministic and runs anywhere torch is importable.
    """
    torch = pytest.importorskip("torch")
    from src.backbones import get_params, make_trainable_unit
    from src.distill import local_finetune_trajectory
    from src.evaluate import accuracy_on

    in_dim, nc = 24, 4
    X_tr, y_tr = _make_separable_blobs(
        torch, n_per_class=60, in_dim=in_dim, nc=nc, seed=7)
    X_te, y_te = _make_separable_blobs(
        torch, n_per_class=40, in_dim=in_dim, nc=nc, seed=99)

    K, lr, bs = 400, 0.05, 32

    # Shared init θ₀ for each unit (a fresh model's params). Fine-tuning both
    # units from their OWN fresh init under the identical bounded K-step budget.
    head_fn = make_trainable_unit(in_dim, nc, "head")
    lora_fn = make_trainable_unit(in_dim, nc, "lora")

    torch.manual_seed(0)
    head_init = get_params(head_fn())
    torch.manual_seed(0)
    lora_init = get_params(lora_fn())

    # Sanity: the LoRA adapter B starts at exactly zero (LoRA-standard init), so
    # any post-trajectory non-zero is unambiguously training signal.
    assert torch.count_nonzero(lora_init["lora_B.weight"]) == 0

    head_delta = local_finetune_trajectory(
        head_init, head_fn, X_tr, y_tr, K_steps=K, lr=lr, momentum=0.0, bs=bs)
    lora_delta = local_finetune_trajectory(
        lora_init, lora_fn, X_tr, y_tr, K_steps=K, lr=lr, momentum=0.0, bs=bs)

    # (i) The adapter genuinely trained: Δ on lora_B is non-trivially non-zero.
    assert float(lora_delta["lora_B.weight"].abs().sum()) > 1e-4, (
        "LoRA adapter B did not move during fine-tuning — the LoRA branch is a "
        "frozen passenger, not a trained unit.")

    # Reconstruct each fine-tuned model: θ_K = θ₀ + Δ, then measure IID accuracy.
    def _acc(make_fn, init, delta):
        m = make_fn()
        m.load_state_dict({k: init[k] + delta[k] for k in init})
        return accuracy_on(m, X_te, y_te)

    head_acc = _acc(head_fn, head_init, head_delta)
    lora_acc = _acc(lora_fn, lora_init, lora_delta)

    # The task is separable, so the head probe should already classify well —
    # this guards that the budget is adequate (else the comparison is vacuous).
    assert head_acc >= 0.80, (
        f"head-only probe acc {head_acc:.3f} too low; budget inadequate to make "
        f"the LoRA comparison meaningful.")
    # (ii) LoRA fine-tuning is at least as accurate as the linear probe (it adds
    # capacity, must not regress). Small tolerance for SGD/minibatch noise.
    assert lora_acc >= head_acc - 0.05, (
        f"LoRA fine-tune acc {lora_acc:.3f} fell below the head-only probe "
        f"{head_acc:.3f} by more than the tolerance — LoRA should not hurt.")
