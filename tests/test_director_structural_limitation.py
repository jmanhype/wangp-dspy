"""Mechanical checks for the WD-p587 director matrix disposition."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "6ac1023b522726705d3ea560216f211003a1d4bd"
DOC = ROOT / "docs/director-capabilities.md"
EVIDENCE = ROOT / "datasets/runs/maestro-parity/director-structural-limitation/evidence.json"
GATES = ROOT / "datasets/runs/maestro-parity/WD-dmf2/gate-derivation.json"
EXPECTED_UNSUPPORTED = (
    "unsupported ([WD-p587 structural limitation]"
    "(../datasets/runs/maestro-parity/director-structural-limitation/evidence.json))"
)
EXPECTED_BEFORE = (
    ("Deterministic ordered multi-clip plan", ("planned", "planned", "planned", "none")),
    ("Per-clip prompt and six-frame overlap", ("planned", "planned", "planned", "none")),
    ("Explicit continuity state and transitions", ("planned", "planned", "planned", "none")),
    ("Beat-aware measured window mapping", ("not applicable", "planned", "not applicable", "none")),
    ("Exact/window pacing preservation", ("planned", "planned", "planned", "none")),
    ("Auto/manual review checkpoints", ("planned", "host_run_verified (WD-7fvx)", "host_run_verified (WD-7fvx)", "none")),
    ("Immutable non-executable queue records", ("planned", "planned", "planned", "none")),
    ("Authorized prompt-only enhancement", ("planned", "planned", "planned", "none")),
    ("Seed-based hash reconstruction", ("planned", "planned", "planned", "none")),
    ("Generated clip, audio, or finished film", ("unsupported in this lane",) * 3 + ("none",)),
)


def _matrix(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = re.fullmatch(
            r"\| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|", line
        )
        if not match:
            continue
        cells = [match.group(index).strip() for index in range(1, 6)]
        if cells[0] in {"Capability", "---"}:
            continue
        rows.append({"capability": cells[0], "cells": cells[1:]})
    return rows


def _gate(name: str) -> dict[str, Any]:
    payload = json.loads(GATES.read_text(encoding="utf-8"))
    return next(item for item in payload["gates"] if item["gate"] == name)


def test_structural_limitation_decision_is_sourced_from_accepted_gate_records() -> None:
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    decision = payload["decision"]

    assert decision["operator"] == {
        "identity": "operator",
        "verbatim": "Approve",
        "recorded_at": "2026-09-28T13:20:11Z",
        "scope": "director structural limitation only",
    }
    assert decision["disposition"] == "unsupported"
    assert decision["hardware_impossibility_claimed"] is False
    assert decision["not_hardware_boundary"] == (
        "The limitation is specific to the WD-dmf2 clip-1 media and is not a global "
        "RTX 3090 impossibility: WD-dmf2 screenplay clip 2 passed the same 1.0 "
        "SyncNet threshold."
    )

    recorded = {item["gate"]: item for item in decision["failed_gates"]}
    for name in (
        "whisper_screenplay_clip0001_score",
        "syncnet_audio_clip0001_confidence",
        "syncnet_screenplay_clip0001_confidence",
    ):
        source = _gate(name)
        assert recorded[name] == source
        assert source["verdict"] == "fail"

    counterexample_gate = _gate("syncnet_screenplay_clip0002_confidence")
    assert decision["passing_counterexample"] == counterexample_gate
    assert counterexample_gate["verdict"] == "pass"


def test_matrix_transition_is_exactly_23_cells_and_preserves_verified_cells() -> None:
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    transition = payload["matrix_transition"]
    after_text = DOC.read_text(encoding="utf-8")
    before = [
        {"capability": capability, "cells": list(cells)}
        for capability, cells in EXPECTED_BEFORE
    ]
    after = _matrix(after_text)

    assert hashlib.sha256(after_text.encode()).hexdigest() == transition["after_sha256"]
    assert [row["capability"] for row in before] == [row["capability"] for row in after]
    assert transition["before_rows"] == before
    assert transition["after_rows"] == after

    changed: list[tuple[str, int, str, str]] = []
    for before_row, after_row in zip(before, after, strict=True):
        assert before_row["capability"] == after_row["capability"]
        for index, (old, new) in enumerate(
            zip(before_row["cells"], after_row["cells"], strict=True)
        ):
            if old != new:
                changed.append((before_row["capability"], index, old, new))
                assert old == "planned"
                assert new == EXPECTED_UNSUPPORTED
            else:
                assert new != "planned"

    assert len(changed) == 23
    assert transition["changed_cell_count"] == 23
    assert transition["planned_before"] == 23
    assert transition["planned_after"] == 0
    assert transition["unsupported_transition_cells"] == 23
    assert transition["unsupported_cells_after_including_preexisting_row"] == 26
    assert transition["preserved_host_run_verified_cells"] == [
        "host_run_verified (WD-7fvx)",
        "host_run_verified (WD-7fvx)",
    ]
    assert transition["unchanged_row_capabilities"] == [
        "Generated clip, audio, or finished film"
    ]
    assert transition["non_transition_cell_changes"] == []
    assert all(cell != "planned" for row in after for cell in row["cells"])
