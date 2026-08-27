#!/usr/bin/env python3
"""build_manifest.py — WD-oa4i STEP 2 dataset manifest builder.

Emits datasets/manifest.json: one row per banked run record with
source run_id, intent, qc score, critic id, video path (repo-relative),
and curation status (kept/dropped/excluded + reason) from
datasets/wd-oa4i/curation.json plus in-record provenance markers.

No GEPA imports — plain json/pathlib only.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _curation_lookup(curation: dict):
    """run_id -> (status, reason) from the curation ledger."""
    table = {}
    legacy = curation.get("legacy_bank_disposition", {})
    for group in legacy.get("groups", []):
        for run in group.get("runs", []):
            disp = run["disposition"]
            reason = (run.get("reason")
                      or group.get("reason") or "").strip()
            table[run["run_id"]] = (disp, reason)
    return table


def build_manifest(runs_dir: Path, curation_path: Path,
                   out_path: Path) -> dict:
    curation = json.loads(Path(curation_path).read_text())
    table = _curation_lookup(curation)

    rows = []
    for p in sorted(Path(runs_dir).glob("*.json")):
        rec = json.loads(p.read_text())
        run_id = p.stem
        vids = rec.get("videos", [])
        marker = (rec.get("curation") or {}).get(
            "videos_provenance_lost", False)
        if marker:
            status, reason = "excluded", (
                (rec.get("curation") or {}).get("note", "")
                or "videos provenance-lost (in-record marker)")
            video = None
        else:
            status, reason = table.get(run_id, ("kept", ""))
            video = vids[0] if vids else None
        rows.append({
            "run_id": run_id,
            "intent": rec.get("intent", ""),
            "qc_score": rec.get("qc", {}).get("score"),
            "critic_id": rec.get("qc", {}).get("critic", ""),
            "video_path": video,
            "curation_status": status,
            "curation_reason": reason,
        })

    manifest = {
        "story": "WD-oa4i",
        "generated_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "n_records": len(rows),
        "n_kept": sum(1 for r in rows if r["curation_status"] == "kept"),
        "rows": rows,
    }
    Path(out_path).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs-dir", default=str(REPO / "datasets" / "runs"))
    ap.add_argument("--curation",
                    default=str(REPO / "datasets" / "wd-oa4i" / "curation.json"))
    ap.add_argument("--out", default=str(REPO / "datasets" / "manifest.json"))
    ap.add_argument("--dry-run", action="store_true",
                    help="build and print, do not write the output file")
    args = ap.parse_args(argv)

    out = Path("/dev/null") if args.dry_run else Path(args.out)
    m = build_manifest(Path(args.runs_dir), Path(args.curation), out)
    print(json.dumps(m, indent=2, ensure_ascii=False))
    if not args.dry_run:
        print(f"wrote {out}", file=__import__("sys").stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
