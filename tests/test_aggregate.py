"""Behaviour tests for ``src.aggregate`` — the server's only crypto operation.

The contract under test (CLAUDE.md "current method" + PRD "Deep-module
interfaces" + the module docstring):

    theta = theta0 + Sum_i w_i * Delta_i ,   w_i = n_i / Sum_j n_j

and the *telescoping identity* that makes the bounded-trajectory framing valid:
aggregating the cumulative displacements ``Delta_i = theta_i^(K) - theta0``
yields exactly the same parameters as (a) aggregating the per-step deltas whose
sum is each ``Delta_i`` and (b) the sample-weighted average of the per-client
finals ``theta_i^(K)``. This equality is *why* collapsing the K-step trajectory
to one ciphertext-set is legitimate, so it is the most rigorously checked
property here.

All tensors are tiny CPU tensors; nothing needs a GPU. torch is imported via
``importorskip`` because ``aggregate`` calls ``.detach().clone()`` on its inputs
(it operates on torch parameter dicts), so the tests need a tensor backend.
"""
from __future__ import annotations

import pytest


# --- tiny helpers -----------------------------------------------------------
def _params(torch, spec, *, seed=None):
    """Build a parameter dict {name: tensor} from a {name: shape} spec.

    Deterministic given ``seed`` so constructed scenarios are reproducible.
    """
    if seed is not None:
        torch.manual_seed(seed)
    return {name: torch.randn(*shape) for name, shape in spec.items()}


def _allclose_dict(torch, a, b, *, atol=1e-6, rtol=1e-5):
    assert a.keys() == b.keys()
    return all(torch.allclose(a[k], b[k], atol=atol, rtol=rtol) for k in a)


# ---------------------------------------------------------------------------
# (b) sample_weights: w_i = n_i / Sum_j n_j, with degenerate fallback
# ---------------------------------------------------------------------------
def test_sample_weights_are_normalised_sample_shares():
    from src.aggregate import sample_weights

    sizes = [10, 30, 60]
    w = sample_weights(sizes)

    assert w == pytest.approx([0.1, 0.3, 0.6])
    assert sum(w) == pytest.approx(1.0)
    # each weight is exactly that client's share of the total
    total = sum(sizes)
    assert w == pytest.approx([s / total for s in sizes])


def test_sample_weights_unequal_then_proportional():
    from src.aggregate import sample_weights

    w = sample_weights([1, 3])
    assert w == pytest.approx([0.25, 0.75])


def test_sample_weights_not_uniform_when_sizes_differ():
    """Guards the PRD requirement that aggregation is sample-weighted, NOT the
    deprecated uniform 1/N (``src/v1``)."""
    from src.aggregate import sample_weights

    w = sample_weights([1, 99])
    assert w != pytest.approx([0.5, 0.5])
    assert w == pytest.approx([0.01, 0.99])


def test_sample_weights_degenerate_all_zero_falls_back_to_uniform():
    from src.aggregate import sample_weights

    w = sample_weights([0, 0, 0, 0])
    assert w == pytest.approx([0.25, 0.25, 0.25, 0.25])
    assert sum(w) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# (a.1) FHE-compat: aggregate result == sample-weighted average of finals
# ---------------------------------------------------------------------------
def test_aggregate_equals_sample_weighted_average_of_finals():
    """With Delta_i = theta_i_final - theta0, theta0 + Sum_i w_i Delta_i must
    equal Sum_i w_i theta_i_final whenever Sum_i w_i == 1.

    This is the externally observable "sample-weighted average of finals"
    identity from the PRD/Testing-Decisions."""
    torch = pytest.importorskip("torch")
    from src.aggregate import aggregate, sample_weights

    spec = {"fc.weight": (4, 3), "fc.bias": (4,)}
    theta0 = _params(torch, spec, seed=0)
    finals = [_params(torch, spec, seed=s) for s in (1, 2, 3)]
    sizes = [10, 30, 60]
    w = sample_weights(sizes)

    deltas = [{k: finals[i][k] - theta0[k] for k in spec} for i in range(len(finals))]
    out = aggregate(theta0, deltas, w)

    expected = {
        k: sum(w[i] * finals[i][k] for i in range(len(finals))) for k in spec
    }
    assert _allclose_dict(torch, out, expected)


def test_aggregate_identity_when_all_deltas_zero_returns_theta0():
    torch = pytest.importorskip("torch")
    from src.aggregate import aggregate

    spec = {"w": (3, 3), "b": (3,)}
    theta0 = _params(torch, spec, seed=7)
    zero_deltas = [{k: torch.zeros_like(v) for k, v in theta0.items()} for _ in range(3)]
    out = aggregate(theta0, zero_deltas, [1 / 3, 1 / 3, 1 / 3])
    assert _allclose_dict(torch, out, theta0)


def test_aggregate_does_not_mutate_inputs():
    """Linearity invariant aside, the server must not clobber theta0 / deltas
    (it clones). Observable via the caller's tensors being unchanged."""
    torch = pytest.importorskip("torch")
    from src.aggregate import aggregate

    spec = {"w": (2, 2)}
    theta0 = _params(torch, spec, seed=5)
    theta0_ref = {k: v.clone() for k, v in theta0.items()}
    deltas = [_params(torch, spec, seed=6)]
    delta_ref = {k: v.clone() for k, v in deltas[0].items()}

    aggregate(theta0, deltas, [1.0])

    assert _allclose_dict(torch, theta0, theta0_ref)
    assert _allclose_dict(torch, deltas[0], delta_ref)


# ---------------------------------------------------------------------------
# (a.2) telescoping identity (THE load-bearing test):
#   aggregate(theta0, [cumulative Delta_i])
#       == aggregate_step_deltas(theta0, [per-step lists])
# ---------------------------------------------------------------------------
def test_telescoping_cumulative_equals_per_step():
    """The cornerstone. Each client i runs K per-step deltas d[i][0..K-1]; its
    cumulative displacement is Delta_i = Sum_step d[i][step]. The server must get
    the SAME parameters whether it sums the per-step deltas (notebook
    ``server_aggregate``) or the collapsed cumulative displacements (the
    transported ciphertext-set). If a refactor ever made the server step
    non-linear / order-dependent, this equality breaks and the test fails loudly.
    """
    torch = pytest.importorskip("torch")
    from src.aggregate import aggregate, aggregate_step_deltas, sample_weights

    spec = {"l1.weight": (5, 4), "l1.bias": (5,), "l2.weight": (3, 5)}
    n_clients, K = 4, 7
    torch.manual_seed(123)
    theta0 = {name: torch.randn(*shape) for name, shape in spec.items()}

    # per-client list of K per-step deltas
    all_step_deltas = [
        [{name: torch.randn(*shape) for name, shape in spec.items()} for _ in range(K)]
        for _ in range(n_clients)
    ]
    # cumulative displacement Delta_i = sum over steps
    cumulative = [
        {name: sum(step[name] for step in all_step_deltas[i]) for name in spec}
        for i in range(n_clients)
    ]

    w = sample_weights([5, 15, 30, 50])
    via_cumulative = aggregate(theta0, cumulative, w)
    via_steps = aggregate_step_deltas(theta0, all_step_deltas, w)

    assert _allclose_dict(torch, via_cumulative, via_steps, atol=1e-5, rtol=1e-4)


def test_telescoping_holds_for_uneven_but_padded_trajectories():
    """Even if a client's later steps are zero (a shorter effective trajectory
    padded to K), the cumulative-vs-per-step equality must still hold — the
    server cannot tell K apart from the collapsed Delta."""
    torch = pytest.importorskip("torch")
    from src.aggregate import aggregate, aggregate_step_deltas

    spec = {"w": (3, 3), "b": (3,)}
    K = 5
    torch.manual_seed(99)
    theta0 = {name: torch.randn(*shape) for name, shape in spec.items()}
    all_step_deltas = []
    for _ in range(3):
        steps = [{name: torch.randn(*shape) for name, shape in spec.items()} for _ in range(2)]
        steps += [{name: torch.zeros(*shape) for name, shape in spec.items()} for _ in range(K - 2)]
        all_step_deltas.append(steps)
    cumulative = [
        {name: sum(step[name] for step in client) for name in spec}
        for client in all_step_deltas
    ]
    w = [0.2, 0.3, 0.5]
    assert _allclose_dict(
        torch,
        aggregate(theta0, cumulative, w),
        aggregate_step_deltas(theta0, all_step_deltas, w),
        atol=1e-5,
        rtol=1e-4,
    )


# ---------------------------------------------------------------------------
# (a.3) FHE-linearity, observed behaviourally:
#   the aggregate is an AFFINE function of the deltas (additivity + scaling)
# ---------------------------------------------------------------------------
def test_aggregate_is_additive_in_the_deltas():
    """A linear (PT x CT, CT + CT only) combine satisfies superposition in the
    displacements: aggregating (a_i + b_i) equals aggregating a_i plus
    aggregating b_i, minus the shared theta0 baseline counted once. We test the
    delta-linear core directly: with theta0 = 0, aggregate is exactly Sum w_i d_i,
    which must be additive. A non-linear op (e.g. a squaring or clamp) on the
    deltas would break this."""
    torch = pytest.importorskip("torch")
    from src.aggregate import aggregate

    spec = {"w": (3, 4), "b": (4,)}
    zero0 = {name: torch.zeros(*shape) for name, shape in spec.items()}
    w = [0.25, 0.75]
    a = [_params(torch, spec, seed=11), _params(torch, spec, seed=12)]
    b = [_params(torch, spec, seed=13), _params(torch, spec, seed=14)]
    ab = [{k: a[i][k] + b[i][k] for k in spec} for i in range(2)]

    out_a = aggregate(zero0, a, w)
    out_b = aggregate(zero0, b, w)
    out_ab = aggregate(zero0, ab, w)

    summed = {k: out_a[k] + out_b[k] for k in spec}
    assert _allclose_dict(torch, out_ab, summed, atol=1e-5, rtol=1e-4)


def test_aggregate_is_scalar_homogeneous_in_the_deltas():
    """Scaling every delta by c scales the (theta0=0) aggregate by c — the PT x CT
    half of the invariant."""
    torch = pytest.importorskip("torch")
    from src.aggregate import aggregate

    spec = {"w": (2, 3)}
    zero0 = {name: torch.zeros(*shape) for name, shape in spec.items()}
    w = [0.4, 0.6]
    d = [_params(torch, spec, seed=21), _params(torch, spec, seed=22)]
    c = 3.5
    scaled = [{k: c * d[i][k] for k in spec} for i in range(2)]

    base = aggregate(zero0, d, w)
    out_scaled = aggregate(zero0, scaled, w)
    expected = {k: c * base[k] for k in spec}
    assert _allclose_dict(torch, out_scaled, expected, atol=1e-5, rtol=1e-4)


# ---------------------------------------------------------------------------
# (c) basin coherence: bounded-from-shared-init aggregates coherently;
#     a constructed divergent (different-init) set does not.
# ---------------------------------------------------------------------------
def _l2_to(torch, params, ref):
    sq = sum((params[k] - ref[k]).pow(2).sum() for k in params)
    return float(sq.sqrt())


def test_basin_coherent_bounded_deltas_stay_near_shared_init():
    """All clients depart the SAME theta0 and move a bounded distance eps. Their
    aggregate must also stay within ~eps of theta0 (a convex combination of
    points in an eps-ball is in that ball). 'Coherent' = lands near the shared
    init, i.e. inside the basin."""
    torch = pytest.importorskip("torch")
    from src.aggregate import aggregate, sample_weights

    spec = {"w": (8, 8), "b": (8,)}
    torch.manual_seed(2024)
    theta0 = {name: torch.randn(*shape) for name, shape in spec.items()}

    eps = 0.1
    deltas = []
    for s in range(5):
        g = torch.Generator().manual_seed(s)
        d = {}
        for name, shape in spec.items():
            v = torch.randn(*shape, generator=g)
            v = v / v.norm() * eps  # bounded: ||delta|| == eps per tensor
            d[name] = v
        deltas.append(d)

    w = sample_weights([20, 20, 20, 20, 20])
    out = aggregate(theta0, deltas, w)

    # aggregate displacement from theta0 is bounded by max client displacement
    disp = _l2_to(torch, out, theta0)
    n_tensors = len(spec)
    per_client_norm = (n_tensors * eps**2) ** 0.5
    assert disp <= per_client_norm + 1e-4


def test_basin_divergent_different_inits_does_not_cohere():
    """Constructed counter-example: clients that did NOT share theta0 (each
    'final' is a wildly different point). Naively averaging them (theta0 + Sum w_i
    (final_i - theta0)) lands far from every client's final — the average is not
    close to any single model. We assert the aggregate is *not* near any client
    final, demonstrating why the bounded-from-shared-init structure is necessary
    rather than cosmetic."""
    torch = pytest.importorskip("torch")
    from src.aggregate import aggregate, sample_weights

    spec = {"w": (16,)}
    torch.manual_seed(7)
    theta0 = {name: torch.zeros(*shape) for name, shape in spec.items()}

    # three mutually antipodal finals (different inits / diverged solutions),
    # each at a large, well-separated location.
    finals = [
        {"w": torch.full((16,), 10.0)},
        {"w": torch.full((16,), -10.0)},
        {"w": torch.cat([torch.full((8,), 10.0), torch.full((8,), -10.0)])},
    ]
    deltas = [{k: finals[i][k] - theta0[k] for k in spec} for i in range(3)]
    w = sample_weights([1, 1, 1])
    out = aggregate(theta0, deltas, w)

    # the equal-weight average of antipodal points is ~origin: far (>> a small
    # tolerance) from every individual diverged final.
    coherent_radius = 1.0
    for f in finals:
        assert _l2_to(torch, out, f) > coherent_radius

    # and compared with the coherent case, the displacement here is large.
    assert _l2_to(torch, out, finals[0]) > 10.0


def test_basin_coherent_vs_divergent_contrast():
    """Side-by-side: bounded-from-shared-init aggregate is far closer to the
    cluster centroid than a divergent set's aggregate is to any of its members.
    Encodes the qualitative 'coherent vs diverges' claim as a numeric gap."""
    torch = pytest.importorskip("torch")
    from src.aggregate import aggregate, sample_weights

    spec = {"w": (32,)}
    torch.manual_seed(0)
    theta0 = {name: torch.zeros(*shape) for name, shape in spec.items()}
    w = sample_weights([1, 1, 1, 1])

    # coherent: all within eps of theta0
    eps = 0.05
    coh = []
    for s in range(4):
        g = torch.Generator().manual_seed(100 + s)
        v = torch.randn(32, generator=g)
        coh.append({"w": v / v.norm() * eps})
    coh_out = aggregate(theta0, coh, w)
    coh_spread = max(_l2_to(torch, coh_out, {"w": theta0["w"] + d["w"]}) for d in coh)

    # divergent: spread far apart
    div_finals = [{"w": torch.full((32,), float(v))} for v in (50, -50, 25, -25)]
    div = [{k: f[k] - theta0[k] for k in spec} for f in div_finals]
    div_out = aggregate(theta0, div, w)
    div_spread = min(_l2_to(torch, div_out, f) for f in div_finals)

    assert coh_spread < div_spread


# ---------------------------------------------------------------------------
# (a.4) Issue 011 — FHE-linearity invariant for the larger trainable parameter
#       sets introduced by lora_<rank> / last_n_blocks scopes. The
#       aggregate operation must remain PT-scalar × CT + CT + CT only,
#       REGARDLESS of how many tensors live in state_dict.
# ---------------------------------------------------------------------------
def _bytes_in_paramdict(params):
    """Total scalar count across every tensor in the state-dict-shaped param
    dict (used to verify the synthetic 'large' spec is genuinely ≥10× the
    head-only baseline). Pure-Python int, no torch ops."""
    return sum(int(_prod(p.shape)) for p in params.values())


def _prod(shape):
    p = 1
    for s in shape:
        p *= int(s)
    return p


def test_aggregate_linearity_invariant_holds_for_lora_sized_param_dict():
    """Issue 011 — the aggregate stays element-wise linear when the trainable
    parameter set grows by a LoRA adapter or an MLP "last block" head.

    Spec rationale (mirrors ``src.backbones`` per issue 011):
      * Baseline ``head_only`` for the resnet18 head is in_dim=512 × nc=10
        + nc bias = 5130 trainable scalars.
      * The synthetic 'expanded' spec below adds a rank-8 LoRA pair
        (A: 8×512, B: 10×8) AND an MLP "last block" (fc1: 128×512 + 128
        bias, fc2: 10×128 + 10 bias) — totalling ~71200 scalars, which is
        ~14× the head-only baseline. This is the 10× threshold the issue
        requires from a "synthetic large-tensor mock".

    Invariant: ``aggregate(theta0, deltas, weights)`` must equal, scalar-by-
    scalar, the hand-computed reference
        ref[k] = theta0[k] + Σᵢ wᵢ · deltas[i][k]
    where the ONLY arithmetic primitives are ``+`` (CT+CT) and scalar ``*``
    (PT×CT). The reference is constructed using exactly those two primitives
    so any non-linear leakage in ``aggregate`` (e.g. a hidden clamp, square,
    re-scaling) would break ``allclose``. Behavioural equivalence across two
    clients (the minimum to exercise summation) is sufficient.

    Why this matters: issue 011 introduces ``trainable_scope`` knobs that
    *change which tensors* live in state_dict but must NOT change the algebra
    of the server step (which is the FHE-compatibility invariant). This
    assertion guards that property at the public ``aggregate`` interface,
    regardless of how many tensors flow through.
    """
    torch = pytest.importorskip("torch")
    from src.aggregate import aggregate, sample_weights

    # Realistic resnet18-scale spec with LoRA + MLP last-block expansion.
    in_dim, nc, rank, hidden = 512, 10, 8, 128
    spec = {
        # Base linear head (head_only baseline)
        "fc.weight": (nc, in_dim),
        "fc.bias": (nc,),
        # LoRA rank-r adapter on the head
        "lora_A.weight": (rank, in_dim),
        "lora_B.weight": (nc, rank),
        # MLP "last block" head (a separate sub-module mimicking the
        # last_n_blocks scope's added capacity in feature space)
        "mlp.fc1.weight": (hidden, in_dim),
        "mlp.fc1.bias": (hidden,),
        "mlp.fc2.weight": (nc, hidden),
        "mlp.fc2.bias": (nc,),
    }

    # Sanity guard: the synthetic spec must be ≥10× the head-only baseline.
    baseline_params = nc * in_dim + nc  # head_only ResNet18-head scalar count
    expanded_params = sum(_prod(shape) for shape in spec.values())
    assert expanded_params >= 10 * baseline_params, (
        f"large-spec sanity guard: expanded {expanded_params} vs baseline "
        f"{baseline_params} — must be ≥10×"
    )

    torch.manual_seed(2026)
    theta0 = {name: torch.randn(*shape) for name, shape in spec.items()}
    n_clients = 4
    deltas = [
        {name: torch.randn(*shape) for name, shape in spec.items()}
        for _ in range(n_clients)
    ]
    w = sample_weights([10, 20, 30, 40])  # asymmetric sample weights

    out = aggregate(theta0, deltas, w)

    # Hand-computed reference using ONLY PT×CT (scalar * tensor) and CT+CT
    # (tensor + tensor) primitives — the FHE-compatible algebra. If aggregate
    # leaks a non-linear op (e.g. clamp, square, mul of two ciphertexts),
    # any mismatched element here would fail allclose at 1e-5 tolerance.
    ref = {name: theta0[name].clone() for name in spec}
    for i in range(n_clients):
        for name in spec:
            ref[name] = ref[name] + w[i] * deltas[i][name]   # CT+CT ; PT×CT

    assert _allclose_dict(torch, out, ref, atol=1e-5, rtol=1e-4)

    # Confirm every tensor in the expanded dict was touched (no silent
    # subsetting of state_dict during aggregation).
    assert set(out.keys()) == set(spec.keys())
    # And the per-tensor shapes are preserved exactly (no reshape / pad).
    for name, shape in spec.items():
        assert tuple(out[name].shape) == shape


def test_aggregate_linearity_invariant_count_independent():
    """Scaling the number of tensors (parameter dict size) by ~100× must not
    change the aggregation algebra — purely a count-independence check.

    The test runs aggregate twice on the same data laid out as (a) 4 large
    tensors and (b) 200 small tensors; the resulting flat-vector concatenated
    output must equal the same hand-computed PT×CT+CT+CT reference in both
    cases. Demonstrates that the FHE invariant ('only + and scalar * on
    tensors') depends on the operation, not the cardinality of the dict —
    issue 011's central correctness claim for the trainable-scope expansion.
    """
    torch = pytest.importorskip("torch")
    from src.aggregate import aggregate, sample_weights

    torch.manual_seed(11)

    # (a) wide spec: 4 tensors, ~4096 scalars each (similar to LoRA-8 on ResNet)
    spec_wide = {
        "t0": (64, 64), "t1": (64, 64), "t2": (64, 64), "t3": (64, 64),
    }
    # (b) thin spec: 200 tensors, 64 scalars each — same total scalar count.
    spec_thin = {f"u{i}": (64,) for i in range(64 * 4)}  # 256 tensors, 64 each

    n_clients = 3
    weights = sample_weights([5, 15, 30])

    def _flat(d):
        return torch.cat([d[k].flatten() for k in sorted(d.keys())])

    def _runs_and_returns_flat(spec):
        theta0 = {name: torch.randn(*shape) for name, shape in spec.items()}
        deltas = [
            {name: torch.randn(*shape) for name, shape in spec.items()}
            for _ in range(n_clients)
        ]
        ref = {name: theta0[name].clone() for name in spec}
        for i in range(n_clients):
            for name in spec:
                ref[name] = ref[name] + weights[i] * deltas[i][name]
        out = aggregate(theta0, deltas, weights)
        # Internal: out must equal the linear reference, regardless of count.
        assert _allclose_dict(torch, out, ref, atol=1e-5, rtol=1e-4)
        return _flat(out), _flat(ref)

    # Both shapes pass the same invariant assertion (above); the test is the
    # combined cross-shape statement that aggregate is count-invariant.
    out_wide, ref_wide = _runs_and_returns_flat(spec_wide)
    out_thin, ref_thin = _runs_and_returns_flat(spec_thin)
    assert torch.allclose(out_wide, ref_wide, atol=1e-5, rtol=1e-4)
    assert torch.allclose(out_thin, ref_thin, atol=1e-5, rtol=1e-4)
