"""LoRA modules + helpers for federated low-rank fine-tuning.

LoRA (Hu et al., 2021) decomposes a weight update as W = W_0 + (α/r) · B · A,
where W_0 is frozen, A ∈ R^{r × in} and B ∈ R^{out × r}. Only A, B are trained.

For our protocol:
  - Backbone (W_0) is the shared deterministic init θ_0 from the public seed.
  - Each client trains only its LoRA adapters {A_i, B_i} for each wrapped layer.
  - The "delta" the client sends is the LoRA params (A, B) themselves
    (since A starts at random init and B starts at zero, the "delta" of A
    from its public init is small at first; the delta of B is just B itself).
  - Server aggregates A's and B's separately, linearly, weighted by sample
    count. This is what every LoRA-FL paper does (e.g., FedLoRA, FFA-LoRA).

FHE compatibility:
  - Aggregation is linear in (A, B) -- two separate sums + PT × CT scaling.
  - Final model uses W_eff = W_0 + (α/r) · B̄ · Ā at inference; this product
    happens on plaintext W_E after threshold decryption (not on ciphertexts),
    so no CT × CT depth is needed in the protocol.
"""
from __future__ import annotations
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class LoRALinear(nn.Module):
    """Wraps a frozen Linear with a trainable rank-r adapter."""
    def __init__(self, base_layer: nn.Linear, rank: int = 8, alpha: float = 16.0):
        super().__init__()
        self.base = base_layer
        for p in self.base.parameters():
            p.requires_grad = False
        out_features = base_layer.weight.shape[0]
        in_features = base_layer.weight.shape[1]
        self.rank = rank
        self.scale = alpha / rank
        # Standard LoRA init: A kaiming, B zero. B=0 means initial update is 0.
        self.lora_A = nn.Parameter(torch.empty(rank, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, rank))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.base(x) + self.scale * F.linear(F.linear(x, self.lora_A), self.lora_B)


def wrap_with_lora(model: nn.Module, rank: int = 8, alpha: float = 16.0,
                   target_names: tuple[str, ...] | None = None) -> nn.Module:
    """Recursively replace nn.Linear children with LoRALinear.

    If `target_names` is given, only layers whose attribute name matches one
    of the entries are wrapped. Default: wrap every Linear we find.
    Conv layers are NOT wrapped here -- they stay frozen as-is.
    """
    for name, child in list(model.named_children()):
        if isinstance(child, nn.Linear):
            if target_names is None or name in target_names:
                setattr(model, name, LoRALinear(child, rank=rank, alpha=alpha))
                continue
        wrap_with_lora(child, rank=rank, alpha=alpha, target_names=target_names)
    return model


def freeze_non_lora(model: nn.Module) -> None:
    """Set requires_grad=False on every parameter that isn't a LoRA A/B matrix."""
    for n, p in model.named_parameters():
        p.requires_grad = ("lora_A" in n or "lora_B" in n)


def lora_state(model: nn.Module) -> dict[str, torch.Tensor]:
    """Return only the LoRA A and B tensors from the model's state dict."""
    return {k: v.detach().clone() for k, v in model.state_dict().items()
            if "lora_A" in k or "lora_B" in k}


def load_lora_state(model: nn.Module, lora_sd: dict[str, torch.Tensor]) -> None:
    """Load only the LoRA params, leaving other params untouched."""
    own = model.state_dict()
    for k, v in lora_sd.items():
        if k in own:
            own[k] = v
    model.load_state_dict(own, strict=False)


def lora_deltas(initial: dict, final: dict) -> dict:
    """Per-LoRA-tensor delta. Same keys as the lora_state output."""
    return {k: final[k] - initial[k] for k in initial}


def trainable_param_count(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
