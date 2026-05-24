"""ViT-B/16 backbone, supporting two fine-tuning modes.

Backbone: timm vit_base_patch16_224.augreg_in21k_ft_in1k (pretrained on
ImageNet-21k, fine-tuned on ImageNet-1k). Loaded from local HF cache on VALAR.

Two modes selected by the `use_lora` flag:

(a) `use_lora=False` (default, "v1 method on ViT"):
    Every parameter of the ViT is trainable from the pretrained init.
    Each client's "delta" is the full 86M-parameter difference. Faithful
    translation of v1 — fine-tunes the entire model, KL-distills, ships
    the parameter delta, server linear-averages.

(b) `use_lora=True`:
    PEFT LoraConfig wraps q/k/v/proj attention projections with rank-r
    adapters (default rank=8, alpha=16). Backbone is frozen; only LoRA
    matrices + classification head are trainable. Delta per client is
    ~hundreds of K parameters instead of 86M.

`trainable_state()` etc. work uniformly: they return only the parameters
that have requires_grad=True. In full-FT mode that's everything; in LoRA
mode that's the adapter + head.
"""
from __future__ import annotations

import os
from typing import Dict, List

import timm
import torch
import torch.nn as nn
from peft import LoraConfig, get_peft_model, PeftModel


VIT_MODEL_NAME = "vit_base_patch16_224.augreg_in21k_ft_in1k"


def build_vit(num_classes: int, pretrained: bool = True) -> nn.Module:
    """Build a fresh ViT-B/16 with a new classification head sized for num_classes."""
    m = timm.create_model(VIT_MODEL_NAME, pretrained=pretrained,
                          num_classes=num_classes)
    return m


def _default_target_modules() -> List[str]:
    """Layer name patterns to LoRA-adapt.

    timm ViT-B/16 attention blocks have a single fused `qkv` linear plus a
    `proj` output linear. The FFN has `mlp.fc1` and `mlp.fc2`. We target
    qkv + proj only by default — this is the standard "attention-only LoRA"
    used by every recent LoRA-FL paper. Adding fc1/fc2 increases parameter
    count and helps utility but bloats the upload.
    """
    return ["qkv", "proj"]


def wrap_with_lora(model: nn.Module, *, rank: int = 8, alpha: int = 16,
                   dropout: float = 0.0,
                   target_modules: List[str] | None = None) -> PeftModel:
    """Wrap a timm ViT with LoRA adapters via PEFT. Returns a PeftModel.

    Only the LoRA A,B matrices are trainable. Everything else (backbone +
    classification head) is frozen at the pretrained init.
    """
    if target_modules is None:
        target_modules = _default_target_modules()
    cfg = LoraConfig(
        r=rank,
        lora_alpha=alpha,
        target_modules=target_modules,
        lora_dropout=dropout,
        bias="none",
        modules_to_save=["head"],  # leave the classification head trainable too
        task_type=None,
    )
    return get_peft_model(model, cfg)


def build_student(num_classes: int, *, use_lora: bool, rank: int = 8,
                  lora_alpha: int = 16, pretrained: bool = True) -> nn.Module:
    """Unified factory: returns either a plain ViT (all params trainable)
    or a LoRA-wrapped ViT (only LoRA + head trainable)."""
    base = build_vit(num_classes=num_classes, pretrained=pretrained)
    if not use_lora:
        for p in base.parameters():
            p.requires_grad = True
        return base
    return wrap_with_lora(base, rank=rank, alpha=lora_alpha)


def trainable_state(model: nn.Module) -> Dict[str, torch.Tensor]:
    """Return clones of all trainable parameters in the given model.

    For full-FT mode: returns the full state dict (everything is trainable).
    For LoRA mode: returns only the LoRA + head tensors. What gets shipped
    to the server in either case.
    """
    state = {}
    for name, p in model.named_parameters():
        if p.requires_grad:
            state[name] = p.detach().clone()
    return state


def trainable_load(model: nn.Module, state: Dict[str, torch.Tensor]) -> None:
    """Copy trainable-parameter values into the model."""
    own = dict(model.named_parameters())
    with torch.no_grad():
        for k, v in state.items():
            if k in own and own[k].requires_grad:
                own[k].copy_(v.to(own[k].device))


def model_deltas(initial: Dict[str, torch.Tensor],
                 final: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    """Per-tensor diff. Used by the server's linear aggregator."""
    return {k: (final[k] - initial[k]) for k in initial}


def trainable_param_count(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


# ---- backwards-compatible aliases (used by earlier code paths) ----
lora_trainable_state = trainable_state
lora_trainable_load = trainable_load
lora_deltas = model_deltas
