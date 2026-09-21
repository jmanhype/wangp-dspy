#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path("/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-42no")
OUT = ROOT / "datasets/runs/provenance/lf004-operator-dogfood-20260920/cut2-deadletter-review"
WORKERS = {
    904: ROOT / "datasets/runs/pull/acceptance/worker-9f75aa6f6ecc/render-0000",
    905: ROOT / "datasets/runs/pull/acceptance/worker-7b851d1e3cf5/render-0001",
    906: ROOT / "datasets/runs/pull/acceptance/worker-d1c1953af087/render-0002",
}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def probe(path: Path) -> dict:
    raw = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], text=True))
    video = next(stream for stream in raw["streams"] if stream["codec_type"] == "video")
    return {"duration_s": float(raw["format"]["duration"]), "width": video["width"], "height": video["height"], "frame_count": video["nb_frames"]}

OUT.mkdir(parents=True, exist_ok=True)
review = {}
for seed, directory in WORKERS.items():
    raw = directory / "raw.mp4"
    sheet = OUT / f"seed-{seed}.contact_sheet.jpg"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-vf", "fps=1/1.115,scale=240:-1,tile=4x1", "-frames:v", "1", str(sheet)], check=True)
    qc_path = directory / "qc-evidence.json"
    review[str(seed)] = {
        "raw_path": str(raw), "raw_sha256": sha(raw), "remux_sha256": sha(directory / "remux.mp4"),
        "probe": probe(raw), "contact_sheet": str(sheet), "contact_sheet_sha256": sha(sheet),
        "qc_evidence": json.loads(qc_path.read_text()) if qc_path.exists() else None,
    }
(OUT / "evidence.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
(OUT / "README.md").write_text(
    "# LF004 cut 2 dead-letter evidence\n\n"
    "Seed 904 and 905 failed post-Whisper after duplicating/hallucinating dialogue. Seed 906 passed both Whisper gates but failed identity/action vision with ghosting and double-exposure artifacts. The durable queue therefore dead-lettered cut 2 after the policy's three QC failures; cuts 3 and 4 remain pending behind it.\n\n"
    "Review the three contact sheets beside this note before deciding whether to authorize a separately governed recovery story.\n"
)
print(json.dumps({seed: {"raw_sha256": item["raw_sha256"], "contact_sheet": item["contact_sheet"]} for seed, item in review.items()}, indent=2))
