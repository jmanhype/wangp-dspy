#!/usr/bin/env python3
"""Mechanically validate the current WD-fay0 consolidated evidence index."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


BUNDLE = Path(__file__).resolve().parent
REPO = BUNDLE.parents[3]
BASE_COMMIT = "5a94eb491c524816334e23e1b2894acc3b772819"
MATRIX_IDENTITY_SHA256 = "5def89a93c01db3b79250e7aced865ea1e4493090537d3c0c4eb04d5725ec2c6"
EXPECTED_DOCS = {
    "image-capabilities.md": 5,
    "music-capabilities.md": 2,
    "sfx-capabilities.md": 3,
    "video-capabilities.md": 9,
    "finishing-capabilities.md": 4,
    "voice-capabilities.md": 3,
    "character-capabilities.md": 2,
    "director-capabilities.md": 3,
}
EXPECTED_TOTALS = {
    "dependency_blocked": 1,
    "host_run_verified": 95,
    "not_applicable": 2,
    "terminal_unsupported_or_fail_closed": 110,
}
EXPECTED_DOCUMENTED_STATES = {
    "dependency_blocked": 1,
    "fail-closed": 1,
    "host_run_verified": 95,
    "not applicable": 2,
    "unsupported": 97,
    "unsupported for planning": 1,
    "unsupported in this lane": 5,
    "unsupported_host_implementation": 2,
    "unsupported_missing_required_input": 2,
    "unsupported_on_this_hardware": 2,
}
EXPECTED_LTX_CELLS = {
    ("docs/video-capabilities.md", "ltx/2.3", "Upscale"),
}
EDITOR_EVIDENCE = Path(
    "datasets/runs/maestro-parity/editor-host-export/host-run/evidence.json"
)
CHECKER_RECEIPT = Path(
    "datasets/runs/maestro-parity/checker-lane-receipts/evidence.json"
)
FIRST_RUN_BOUNDARY = {
    "source_ref": "story/WD-bw0h@2dfe36863e29eef02af0ea330d13d331bafdc00e",
    "path": "datasets/runs/maestro-parity/clean-generated/failed-retry/boundary.md",
    "sha256": "b78f5936a227782e4c3b7866e041cd9bbcc3d60d7ed4b9ebe5418e14e3d78d5f",
    "state": "incomplete_storage_boundary",
    "generated_artifact": False,
    "retry_or_second_generation": False,
    "queue_jobs_admitted": 0,
}
LTX_BOUNDARY = {
    "source_ref": "story/WD-28ac@fced67e1293dc2dbbdf3f29c8b615f6357012ab6",
    "path": "datasets/runs/maestro-parity/ltx-dependency-terminalization/preflight-boundary.json",
    "sha256": "6c881c9df3cd2a5d4ce85ee8fe5327e6631ac77cf2a2ca88c3b4579be4f05d53",
    "state": "dependency_blocked_before_download_or_admission",
    "cells": [list(cell) for cell in sorted(EXPECTED_LTX_CELLS)],
    "model_download_bytes_actual": 0,
    "inference_attempted": False,
    "not_a_hardware_verdict": True,
}
NON_MATRIX_ROWS = [
    {
        "cell": "generation",
        "canonical_state": "host_run_verified",
        "doc": "docs/editor.md",
        "documented_state": "verified - evidence-backed host run",
        "evidence_or_boundary": "datasets/runs/maestro-parity/editor-host-export/host-run/evidence.json",
        "row": "Authorized host export/media",
        "source_line": 19,
    },
    {
        "cell": "surface",
        "canonical_state": "terminal_unsupported_or_fail_closed",
        "doc": "docs/editor.md",
        "documented_state": "unsupported",
        "evidence_or_boundary": "explicitly deferred; no GUI in this lane",
        "row": "Graphical/browser UI",
        "source_line": 32,
    },
    {
        "cell": "generation",
        "canonical_state": "incomplete_storage_boundary",
        "doc": "docs/first-run.md",
        "documented_state": "not a verified generation claim",
        "evidence_or_boundary": "story/WD-bw0h@2dfe36863e29eef02af0ea330d13d331bafdc00e:datasets/runs/maestro-parity/clean-generated/failed-retry/boundary.md",
        "row": "Generated artifact from first-run",
        "source_line": 97,
    },
]


def canonical_state(state: str) -> str:
    if state == "host_run_verified":
        return "host_run_verified"
    if state == "dependency_blocked":
        return "dependency_blocked"
    if state == "not applicable":
        return "not_applicable"
    if state.startswith("unsupported") or state == "fail-closed":
        return "terminal_unsupported_or_fail_closed"
    raise AssertionError(f"unknown capability state: {state}")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_document_rows(repo_root: Path = REPO) -> list[dict[str, str]]:
    parsed: list[dict[str, str]] = []
    for filename, state_columns in EXPECTED_DOCS.items():
        lines = (repo_root / "docs" / filename).read_text(encoding="utf-8").splitlines()
        table: list[tuple[int, list[str]]] = []
        for line_number, line in enumerate(lines, 1):
            if line.startswith("|"):
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                table.append((line_number, cells))
        if len(table) < 3:
            raise AssertionError(f"{filename}: capability table is missing")
        headers = table[0][1]
        for line_number, row in table[2:]:
            identity = row[0].strip("`")
            for column in headers[1 : 1 + state_columns]:
                raw = row[headers.index(column)]
                state = raw.split("(", 1)[0].split("[", 1)[0].strip()
                link_match = re.search(r"\]\((.*?)\)", raw)
                parsed.append(
                    {
                        "doc": f"docs/{filename}",
                        "source_line": str(line_number),
                        "row": identity,
                        "cell": column,
                        "documented_state": state,
                        "evidence_or_boundary": link_match.group(1)
                        if link_match
                        else "",
                    }
                )
    return parsed


def matrix_identity(rows: list[dict[str, str]]) -> str:
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalized_evidence_path(link: str, repo_root: Path = REPO) -> Path:
    path = (repo_root / "docs" / link).resolve()
    repo_root = repo_root.resolve()
    if repo_root not in path.parents:
        raise AssertionError(f"evidence link escapes repository: {link}")
    return path


def evidence_manifest(rows: list[dict[str, str]], repo_root: Path = REPO) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for row in rows:
        if not row["evidence_or_boundary"]:
            continue
        path = normalized_evidence_path(row["evidence_or_boundary"], repo_root)
        manifest[path.relative_to(repo_root.resolve()).as_posix()] = digest(path)
    return dict(sorted(manifest.items()))


def validate_non_matrix_sources(repo_root: Path) -> None:
    editor = (repo_root / "docs/editor.md").read_text(encoding="utf-8").splitlines()
    first_run = (repo_root / "docs/first-run.md").read_text(encoding="utf-8").splitlines()
    assert "WD-qthq authorized host export is **verified - evidence-backed host run**" in editor[18]
    assert EDITOR_EVIDENCE.as_posix() in editor[18]
    assert "No graphical or browser UI is implemented" in editor[31]
    assert "No command in this surface is a verified generation claim." in first_run[96]


def validate_index(
    index_path: Path = BUNDLE / "evidence-index.json",
    repo_root: Path = REPO,
) -> dict[str, object]:
    index: dict[str, Any] = json.loads(
        index_path.read_text(encoding="utf-8")
    )
    assert index["base_commit"] == BASE_COMMIT
    assert index["matrix_identity_sha256"] == MATRIX_IDENTITY_SHA256
    rows = index["row_inventory"]["rows"]
    observed = parse_document_rows()
    expected_rows = [
        {**row, "canonical_state": canonical_state(row["documented_state"])}
        for row in observed
    ]
    assert len(rows) == len(observed) == 208, (len(rows), len(observed))
    assert rows == expected_rows, "index rows diverge from source capability matrices"
    assert matrix_identity(expected_rows) == MATRIX_IDENTITY_SHA256, (
        "authoritative matrix identity drifted"
    )
    identities = [(row["doc"], row["row"], row["cell"]) for row in rows]
    assert len(identities) == len(set(identities)), "duplicate matrix identity"
    for row in rows:
        assert set(row) == {
            "doc",
            "source_line",
            "row",
            "cell",
            "documented_state",
            "evidence_or_boundary",
            "canonical_state",
        }

    totals = Counter(row["canonical_state"] for row in rows)
    assert dict(sorted(totals.items())) == EXPECTED_TOTALS
    assert index["row_inventory"]["totals"] == EXPECTED_TOTALS
    documented_totals = Counter(row["documented_state"] for row in rows)
    assert dict(sorted(documented_totals.items())) == EXPECTED_DOCUMENTED_STATES
    assert index["row_inventory"]["documented_state_totals"] == EXPECTED_DOCUMENTED_STATES
    assert sum(
        count
        for state, count in documented_totals.items()
        if state != "host_run_verified"
        and state != "dependency_blocked"
        and state != "not applicable"
    ) == 110
    ltx_rows = {
        (row["doc"], row["row"], row["cell"])
        for row in rows
        if row["canonical_state"] == "dependency_blocked"
    }
    assert ltx_rows == EXPECTED_LTX_CELLS, "wrong remaining LTX dependency scope"

    validate_non_matrix_sources(repo_root)
    assert index["non_matrix_inventory"]["rows"] == NON_MATRIX_ROWS, (
        "non_matrix_inventory is stale"
    )
    assert index["non_matrix_inventory"]["total"] == len(NON_MATRIX_ROWS)
    assert index["remaining_boundaries"]["ltx_dependency_batch"] == LTX_BOUNDARY, (
        "wrong remaining LTX dependency boundary"
    )
    assert index["remaining_boundaries"]["first_run_generated_artifact"] == FIRST_RUN_BOUNDARY
    editor_path = repo_root / EDITOR_EVIDENCE
    editor = json.loads(editor_path.read_text(encoding="utf-8"))
    assert digest(editor_path) == index["editor_host_run_evidence_sha256"]
    assert editor["operator_authorization"]["status"] == "approved"
    assert editor["queue_attempt"]["final_state"] == "done"
    assert editor["reviewer_verdict"]["decision"] == "approved"
    assert all(gate["verdict"] == "pass" for gate in editor["objective_gate_results"])
    assert editor["runtime_notes"]["model_downloads"] == 0

    manifest = evidence_manifest(observed, repo_root)
    assert index["evidence_manifest"] == manifest, "matrix evidence hash manifest drifted"
    for relative_path, expected_hash in manifest.items():
        assert digest(repo_root / relative_path) == expected_hash, relative_path

    receipt_path = repo_root / CHECKER_RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert digest(receipt_path) == index["lane_bundles"]["receipt_sha256"]
    assert digest(repo_root / "scripts/verify_maestro_parity.py") == receipt["checker_sha256"]
    assert receipt["checker_sha256"] == index["lane_bundles"]["checker_sha256"]
    expected_receipt_results = {
        "WD-2gyw": 0,
        "WD-bxhc": 0,
        "WD-cpow": 0,
        "WD-m0r5": 0,
        "WD-r81u": 0,
        "WD-rous": 0,
        "consent-closeout": 0,
        "WD-dmf2": 1,
    }
    observed_receipt_results = {lane["lane"]: lane["exit_code"] for lane in receipt["lanes"]}
    assert observed_receipt_results == expected_receipt_results
    assert index["lane_bundles"]["lane_exit_codes"] == expected_receipt_results

    rendered = render_markdown(index)
    assert (index_path.with_name("evidence-index.md").read_text(encoding="utf-8")) == rendered

    bundle_root = index_path.parent
    bundle_files = [path for path in bundle_root.rglob("*") if path.is_file()]
    assert sum(path.stat().st_size for path in bundle_files) < 16 * 1024 * 1024
    assert not [
        path
        for path in bundle_root.rglob("*")
        if path.suffix.lower() in {".bin", ".ckpt", ".safetensors", ".env"}
    ]
    return {
        "matrix_rows": len(rows),
        "matrix_totals": dict(sorted(totals.items())),
        "non_matrix_rows": len(NON_MATRIX_ROWS),
        "ltx_dependency_cells": len(ltx_rows),
        "hashed_matrix_evidence_files": len(manifest),
    }


def _markdown_cell(value: object) -> str:
    return f"`{value}`" if value else ""


def render_markdown(index: dict[str, Any]) -> str:
    lines = [
        "# Current consolidated Maestro-parity evidence index",
        "",
        f"Reconciled by: `{index['reconciliation_story_id']}`; capstone base: `{index['base_commit']}`.",
        "",
        f"**VERDICT: {index['verdict']}**",
        "",
        "This is local evidence navigation only. It authorizes no host, model, storage, queue, render, or new capability work.",
        "",
        "## Current matrix census",
        "",
    ]
    for state, count in index["row_inventory"]["totals"].items():
        lines.append(f"- `{state}`: {count}")
    lines.extend(["", "## Remaining boundaries", ""])
    boundaries = index["remaining_boundaries"]
    ltx = boundaries["ltx_dependency_batch"]
    first = boundaries["first_run_generated_artifact"]
    lines.extend(
        [
            f"- Exactly {len(ltx['cells'])} LTX cells remain `dependency_blocked` at `{ltx['source_ref']}` (`{ltx['path']}`, SHA-256 `{ltx['sha256']}`); no download, inference, or admission is claimed.",
            f"- First-run generated media remains incomplete at `{first['source_ref']}` (`{first['path']}`, SHA-256 `{first['sha256']}`); the failed retry generated no artifact and admitted no queue job.",
            "",
            "## Non-matrix dispositions",
            "",
            "| Source | Line | Row | Cell | Documented state | Canonical state | Evidence/boundary |",
            "| --- | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for row in index["non_matrix_inventory"]["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["doc"],
                    str(row["source_line"]),
                    row["row"],
                    row["cell"],
                    _markdown_cell(row["documented_state"]),
                    _markdown_cell(row["canonical_state"]),
                    _markdown_cell(row["evidence_or_boundary"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Complete matrix-row/cell disposition table",
            "",
            "| Source | Line | Row | Cell | Documented state | Canonical state | Evidence/boundary |",
            "| --- | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for row in index["row_inventory"]["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["doc"],
                    str(row["source_line"]),
                    row["row"],
                    row["cell"],
                    _markdown_cell(row["documented_state"]),
                    _markdown_cell(row["canonical_state"]),
                    _markdown_cell(row["evidence_or_boundary"]),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Matrix evidence byte manifest", ""])
    lines.extend(
        f"- `{path}`: `{digest}`"
        for path, digest in index["evidence_manifest"].items()
    )
    lines.extend(
        [
            "",
            f"Checker receipt: `{CHECKER_RECEIPT}` SHA-256 `{index['lane_bundles']['receipt_sha256']}`.",
            f"Editor host-run evidence: `{EDITOR_EVIDENCE}` SHA-256 `{index['editor_host_run_evidence_sha256']}`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    summary = validate_index()
    print(
        json.dumps(
            {
                "result": "PASS",
                **summary,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, KeyError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
