#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


root = Path(__file__).resolve().parent
names = (
    "extend-probe",
    "blend-probe",
    "retake-probe",
    "edit-probe",
    "outpaint-probe",
    "repaint-probe",
    "recast-probe",
)
batch = [json.loads((root / f"native-settings/{name}.json").read_text()) for name in names]
(root / "native-settings/probe-batch.json").write_text(json.dumps(batch, indent=2) + "\n")
