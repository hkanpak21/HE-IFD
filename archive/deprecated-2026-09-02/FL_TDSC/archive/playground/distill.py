"""Client-side local distillation with method hooks.

Each method = a (use_probe, use_anchors, output_mask) triple.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

from .model import build_model, load_named, state_named, deltas


@dataclass
class DistillCfg:
    use_probe: bool = False
    use_anchors: bool = False
    anchor_lambda: float = 1.0
    pre_align_epochs: int = 0
    pre_align_lr: float = 0.05
    K: int = 5
    lr: float = 1e-2
    batch_size: int = 64
    tau: float = 4.0
    momentum: float = 0.9


def kl(s_logits, t_logits, tau):
    s = F.log_softmax(s_logits / tau, dim=1)
    t = F.softmax(t_logits / tau, dim=1)
    return F.kl_div(s, t, reduction="batchmean") * (tau ** 2)


def local_distill(teacher: nn.Module, distill_ds: Dataset, theta0: dict,
                  *, cfg: DistillCfg, device, seed: int, arch: str = "mlp",
                  anchors: Optional[tuple[torch.Tensor, torch.Tensor]] = None
                  ) -> dict[str, torch.Tensor]:
    torch.manual_seed(seed)
    s = build_model(arch).to(device); load_named(s, theta0)
    teacher = teacher.to(device).eval()
    if len(distill_ds) == 0 and not cfg.use_anchors:
        return deltas(theta0, state_named(s))

    if len(distill_ds) > 0:
        loader = DataLoader(distill_ds, batch_size=cfg.batch_size, shuffle=True, num_workers=0)
    else:
        loader = None
    opt = optim.SGD(s.parameters(), lr=cfg.lr, momentum=cfg.momentum)
    crit_anchor = nn.CrossEntropyLoss()

    # Reshape anchors for conv-style nets (which expect (N, 1, 28, 28))
    def _anchor_input(Z):
        if Z.dim() == 2 and arch == "lenet5":
            return Z.view(Z.size(0), 1, 28, 28)
        return Z

    s.train()
    for _ in range(cfg.K):
        if loader is not None:
            for xb, _ in loader:
                xb = xb.to(device)
                with torch.no_grad():
                    t_logits = teacher(xb)
                s_logits = s(xb)
                loss = kl(s_logits, t_logits, cfg.tau)
                if cfg.use_anchors and anchors is not None:
                    Z, yZ = anchors
                    loss = loss + cfg.anchor_lambda * crit_anchor(s(_anchor_input(Z)), yZ)
                opt.zero_grad()
                loss.backward()
                opt.step()
        else:
            # anchors-only step (no local data at all)
            Z, yZ = anchors
            loss = cfg.anchor_lambda * crit_anchor(s(_anchor_input(Z)), yZ)
            opt.zero_grad(); loss.backward(); opt.step()

    final = state_named(s)
    d = deltas(theta0, final)
    return d
