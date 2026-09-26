#!/usr/bin/env python3
"""Mechanically validate the WD-fay0 consolidated evidence index."""
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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_document_rows() -> list[dict[str, str]]:
    parsed: list[dict[str, str]] = []
    for filename, state_columns in EXPECTED_DOCS.items():
        lines = (REPO / "docs" / filename).read_text(encoding="utf-8").splitlines()
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


def main() -> int:
    index: dict[str, Any] = json.loads(
        (BUNDLE / "evidence-index.json").read_text(encoding="utf-8")
    )
    rows = index["row_inventory"]["rows"]
    observed = parse_document_rows()
    assert len(rows) == len(observed) == 208, (len(rows), len(observed))
    assert [
        (row["doc"], row["source_line"], row["row"], row["cell"], row["documented_state"])
        for row in rows
    ] == [
        (
            row["doc"],
            int(row["source_line"]),
            row["row"],
            row["cell"],
            row["documented_state"],
        )
        for row in observed
    ], "index rows diverge from source capability matrices"
    identities = [(row["doc"], row["row"], row["cell"]) for row in rows]
    assert len(identities) == len(set(identities)), "duplicate matrix identity"
    for row in rows:
        if row["canonical_state"] == "planned":
            assert row["blocker"].strip(), f"planned row lacks blocker: {row}"
        if row["documented_state"] == "host_run_verified":
            assert row["evidence_or_boundary"], f"verified row lacks evidence: {row}"

    lanes = index["lane_bundles"]
    assert len(lanes) == 8 and len({lane["story_id"] for lane in lanes}) == 8
    for lane in lanes:
        if lane["available_on_capstone_base"] and lane["manifest_sha256"]:
            manifest = REPO / lane["manifest_path"]
            assert digest(manifest) == lane["manifest_sha256"], lane["story_id"]

    transcript = (BUNDLE / "checker-transcripts/results.tsv").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(transcript) == 9, "checker result table must cover eight lanes"
    checker_rows = [line.split("\t") for line in transcript]
    assert checker_rows[0] == ["lane", "retrieval", "exit", "result"]
    assert [row[0] for row in checker_rows[1:]] == [lane["story_id"] for lane in lanes]
    assert [int(row[2]) for row in checker_rows[1:]] == [
        lane["checker"]["exit"] for lane in lanes
    ]

    totals = Counter(row["canonical_state"] for row in rows)
    assert dict(totals) == index["row_inventory"]["totals"]
    bundle_files = [path for path in BUNDLE.rglob("*") if path.is_file()]
    assert sum(path.stat().st_size for path in bundle_files) < 16 * 1024 * 1024
    assert not [
        path
        for path in BUNDLE.rglob("*")
        if path.suffix.lower() in {".bin", ".ckpt", ".safetensors", ".env"}
    ]
    print(
        json.dumps(
            {
                "result": "PASS",
                "matrix_rows": len(rows),
                "matrix_totals": dict(totals),
                "lanes": len(lanes),
                "passing_bundles": sum(lane["checker"]["exit"] == 0 for lane in lanes),
                "failing_bundles": sum(lane["checker"]["exit"] != 0 for lane in lanes),
                "bundle_files": len(bundle_files),
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
