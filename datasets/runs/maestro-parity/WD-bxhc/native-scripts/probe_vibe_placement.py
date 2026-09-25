#!/usr/bin/env python3
"""Diagnostic: verify whether VibeVoice can load without meta parameters."""
from __future__ import annotations

import json
import os
from collections import Counter

import torch

from transformers import AutoModelForTextToWaveform


MODEL = "/mnt/bulk/straughter/models/VibeVoice-7B-hf"
mode = os.environ.get("WD_BXHC_VIBE_PLACEMENT", "cpu")
if mode == "cpu":
    model = AutoModelForTextToWaveform.from_pretrained(
        MODEL, device_map={"": "cpu"}, max_memory={"cpu": "26GiB"},
    )
else:
    model = AutoModelForTextToWaveform.from_pretrained(
        MODEL, device_map="auto", max_memory={0: "14GiB", "cpu": "26GiB"},
    )
placement = mode
if os.environ.get("WD_BXHC_VIBE_QUANTIZE") == "1":
    from quanto import freeze, qint8, quantize

    quantize(model, weights=qint8)
    freeze(model)
    model.to(torch.device("cuda"))
    placement = "cpu-load-quanto-int8-cuda"
devices = Counter(str(parameter.device) for parameter in model.parameters())
meta = [name for name, parameter in model.named_parameters() if parameter.device.type == "meta"]
print(json.dumps({
    "mode": placement,
    "device_counts": dict(devices),
    "meta_parameter_count": len(meta),
    "first_meta_parameters": meta[:20],
}, sort_keys=True))
