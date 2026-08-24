"""WD-mhr2: first live Pipeline cycle on the 3090.

Render leg: GLM-5.3 creative stages -> H3 render via SshHost.
QC leg runs AFTER critic re-serve (separate step, GPU sequencing) —
this script stores everything QC needs (briefs, decisions, video
paths) into datasets/ as the first labeled example.
"""
import json
import os
import sys
import time
from pathlib import Path

# repo-root imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from predict.lm_wiring import creative_lm
from predict.pipeline import Pipeline, PipelineStageError
from host.render_host import SshHost
from host.wangp_adapter import WanGPAdapter

GENRE = "surreal"
INTENT = ("a lighthouse beacon sweeping a black ocean at night, "
          "storm building, waves exploding against the rocks")

RUN_DIR = Path(__file__).resolve().parent.parent / "datasets" / "runs"
RUN_DIR.mkdir(parents=True, exist_ok=True)
run_id = time.strftime("%Y%m%d-%H%M%S")
run_path = RUN_DIR / f"{run_id}.json"

host = SshHost(target="3090", wgp_root="/home/straughter/Wan2GP",
               pull_root=str(RUN_DIR / "pull"))
# output_dir is REMOTE-namespace (the adapter builds remote attempt
# dirs from it; WD-h0vk namespace contract) — the host maps it back
# to the local pull mirror for readback.
adapter = WanGPAdapter(host=host,
                       output_dir="/home/straughter/Wan2GP/outputs")
lm = creative_lm()

p = Pipeline(genre=GENRE, creative_lm=lm, adapter=adapter)
t0 = time.time()
try:
    r = p.forward(INTENT)
except PipelineStageError as e:
    print(f"STAGE FAILURE [{e.stage}]: {e}", file=sys.stderr)
    sys.exit(1)

record = {
    "run_id": run_id,
    "genre": GENRE,
    "intent": INTENT,
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "duration_secs": round(time.time() - t0, 1),
    "briefs": [b.__dict__ if hasattr(b, "__dict__") else str(b)
               for b in r.briefs],
    "decisions": [d.__dict__ if hasattr(d, "__dict__") else str(d)
                  for d in r.decisions],
    "videos": list(r.render.video_paths) if r.render else [],
    "evidence": r.evidence,
    "qc": None,  # filled by the QC step after critic re-serve
}
run_path.write_text(json.dumps(record, indent=2, default=str))
print("RUN OK:", run_id, f"{record['duration_secs']}s")
print("videos:", record["videos"])
print("record:", run_path)
