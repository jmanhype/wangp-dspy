#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from predict.content_brief import load_content_brief

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical_sha(plan: dict) -> str:
    roots = {str(ROOT)}
    recorded_root = plan.get("repository", {}).get("repo_root")
    if isinstance(recorded_root, str):
        roots.add(recorded_root)
    prefixes = tuple(f"{root.rstrip('/')}/" for root in sorted(roots, key=len, reverse=True))

    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if k not in {"input", "repository"}}
        if isinstance(value, list): return [clean(v) for v in value]
        if isinstance(value, str):
            for prefix in prefixes:
                if value.startswith(prefix):
                    return value[len(prefix):]
        return value
        return value
    data = json.dumps(clean(plan), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    base = ROOT / "datasets/content_briefs/lf004-operator-dogfood"
    ap.add_argument("--canonical-sha", required=True)
    args = ap.parse_args()
    brief = load_content_brief(base / "brief.json"); guides = json.loads((base / "run/audio-guides.json").read_text())
    plates = base / "plates"; assert sorted(p.name for p in plates.iterdir()) == ["Rho.png", "Tess.png", "anchor.png"]
    for name, item in guides["plates"].items():
        assert sha(plates / item["staged"]) == sha(ROOT / item["source"]) == item["sha256"]
    metadata = []
    for turn, path, line in zip(guides["turns"], brief.audio_paths, brief.dialogue):
        audio = (brief.source_path.parent / path).resolve(); assert audio.is_file() and ROOT in audio.parents and sha(audio) == turn["sha256"]
        provenance = json.loads((ROOT / turn["provenance"]).read_text()); assert provenance["text"] == turn["text"] == line.text
        report = json.loads((ROOT / turn["report"]).read_text()); entry = next(x for x in report["turns"] if x["text"] == turn["text"])
        assert entry["status"] == "complete" and entry["prepared_sha256"] == turn["sha256"] and entry["whisper_gate"]["passed"] is turn["whisper_passed"]
        assert entry["whisper_gate"]["transcript"] == turn["whisper_transcript"]; metadata.append((turn["speaker"], turn["text"]))
    plan = json.loads((base / "plan.json").read_text()); ledger = base / "run/run_ledger.json"; ledger_data = json.loads(ledger.read_text())
    assert canonical_sha(plan) == args.canonical_sha
    assert plan["brief_hash"] == brief.brief_hash and plan["summary"] == {"clip_count": 4, "speakers": [x[0] for x in metadata], "planned_duration_s": 17.832, "dry_run": True, "gpu_work": False, "queue_submitted": False}
    assert len(plan["clips"]) == 4 and all(clip["frames"] == clip["audio_length_frames"] == 107 for clip in plan["clips"])
    assert all(abs(clip["shot_duration_s"] - 107 / 24) < 0.001 for clip in plan["clips"])
    assert not (base / "run/jobs.db").exists() and sorted(p.name for p in (base / "run").iterdir()) == ["audio-guides.json", "run_ledger.json", "script.txt", "verify.py"]
    assert ledger_data["schema_version"] == 1 and ledger_data["status"] == "planned" and ledger_data["clip_count"] == 4 and ledger_data["dry_run"] is True
    with tempfile.TemporaryDirectory(prefix="lf004-replay-") as temp:
        identities = []
        for index in range(2):
            output = Path(temp) / f"plan-{index}.json"; run = Path(temp) / f"run-{index}"
            subprocess.run([sys.executable, str(ROOT / "scripts/run_content_brief.py"), "--brief", str(base / "brief.json"), "--plates", str(plates), "--output", str(output), "--run-dir", str(run)], check=True, stdout=subprocess.DEVNULL)
            identities.append(canonical_sha(json.loads(output.read_text()))); assert identities[-1] == args.canonical_sha
        assert identities[0] == identities[1]
    print(json.dumps({"brief_hash": brief.brief_hash, "plan_sha256": sha(base / "plan.json"), "canonical_plan_sha256": canonical_sha(plan), "run_ledger_sha256": sha(ledger), "replay": "identical", "status": "verified"}, sort_keys=True))
    return 0

if __name__ == "__main__": raise SystemExit(main())
