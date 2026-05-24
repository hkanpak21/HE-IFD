"""ViT-B/16 backbone + LoRA adapters via PEFT.

Backbone: timm vit_base_patch16_224.augreg_in21k_ft_in1k (pretrained on
ImageNet-21k, fine-tuned on ImageNet-1k). Loaded from local HF cache on VALAR.

LoRA: PEFT LoraConfig targeting the attention projection layers (q, k, v) and
optionally the FFN. Default rank=8, alpha=16. Only LoRA matrices are trainable.

Per-client "delta" is the set of LoRA A and B matrices. Since A is init Kaiming
and B is init zero, the initial LoRA output is identically zero — so each
client's "delta from shared init" can be expressed as the final LoRA state.
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


def lora_trainable_state(pmodel: PeftModel) -> Dict[str, torch.Tensor]:
    """Return clones of all trainable parameters in a LoRA-wrapped model.

    These are the LoRA A/B tensors and the classification head (if
    modules_to_save lists it). What gets shipped to the server.
    """
    state = {}
    for name, p in pmodel.named_parameters():
        if p.requires_grad:
            state[name] = p.detach().clone()
    return state


def lora_trainable_load(pmodel: PeftModel, state: Dict[str, torch.Tensor]) -> None:
    """Load trainable-parameter values into a fresh LoRA model with the same arch."""
    own = dict(pmodel.named_parameters())
    with torch.no_grad():
        for k, v in state.items():
            if k in own and own[k].requires_grad:
                own[k].copy_(v.to(own[k].device))


def lora_deltas(initial: Dict[str, torch.Tensor],
                final: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    """Per-tensor diff. Used by the server's linear aggregator."""
    return {k: (final[k] - initial[k]) for k in initial}


def trainable_param_count(pmodel: PeftModel) -> int:
    return sum(p.numel() for p in pmodel.parameters() if p.requires_grad)
