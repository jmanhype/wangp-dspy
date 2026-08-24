"""WD-mhr2 batch driver: N pipeline cycles, fully sequenced.

Per cycle: stop critic -> render (GLM-5.3 creative + H3) -> start
critic -> QC -> record. Stops at the first hard failure (record
preserved); progress logged per cycle.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
SKIP_DONE = "--skip-done" in sys.argv

INTENTS = [
    "a lighthouse beacon sweeping a black ocean at night, storm building, waves exploding against the rocks",
    "a kaiju silhouette rising through fog over a harbor city, dawn light, distant sirens",
    "rain on neon streets at midnight, reflections rippling as a lone figure walks past glowing signs",
    "a paper boat drifting down a flooded gutter city, macro lens, overcast melancholy",
    "an abandoned ferris wheel turning slowly in sea fog, gulls circling, desaturated dawn",
    "a chess match between two statues in a museum at night, dust motes in moonlight",
]

def sh(cmd, timeout=600, **kw):
    r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True,
                       text=True, timeout=timeout, **kw)
    return r

def gpu(seq):
    # start-critic sleeps 65s for model load + 2 ssh hops; give it room.
    # BatchMode in gpu_seq makes ssh fail fast instead of hanging on any
    # interactive prompt; retry once — transient Tailscale blips fail,
    # they don't block.
    tmo = 300 if seq == "start-critic" else 120
    r = None
    for attempt in (1, 2):
        r = sh(["bash", str(REPO / "scripts" / "gpu_seq.sh"), seq],
               timeout=tmo)
        if r.returncode == 0:
            break
        print(f"[gpu:{seq}] attempt {attempt} failed rc={r.returncode}; "
              f"retrying" if attempt == 1 else f"[gpu:{seq}] FAILED",
              flush=True)
        if attempt == 1:
            import time as _t; _t.sleep(5)
    print(f"[gpu:{seq}]", (r.stdout or "").strip().replace("\n", " | "))
    return r

results = []
failed_intents = []
done_intents = set()
for p in (REPO / "datasets" / "runs").glob("*.json"):
    try:
        rec = json.loads(p.read_text())
    except Exception:
        continue
    if rec.get("qc"):
        done_intents.add(rec.get("intent", "")[:60].lower())
print(f"banked: {len(done_intents)} example(s) with QC")

new_done = 0
for intent in INTENTS:
    if new_done >= N:
        break
    if intent[:60].lower() in done_intents:
        print(f"skip (already banked): {intent[:50]}")
        continue
    print(f"\n===== CYCLE +{new_done+1}/{N}: {intent[:50]}... =====", flush=True)
    t0 = time.time()

    gpu("stop-critic")
    # render leg (QC chained in-script will fail with critic down; run
    # render-only by temporarily monkeypatching? No — run_cycle tries QC
    # after render. We accept the exit-2 QC failure, then QC explicitly.)
    env_addon = f"WD_MHR2_INTENT={intent!r}"
    r = subprocess.run(
        f'cd {REPO} && GLM_API_KEY=$(grep GLM_API_KEY ~/.hermes/.env | cut -d= -f2) '
        f'GLM_BASE_URL=$(grep GLM_BASE_URL ~/.hermes/.env | cut -d= -f2) '
        f'WD_MHR2_INTENT=$(python3 -c "import json,sys;sys.stdout.write(json.loads(sys.argv[1]))" {json.dumps(intent)!r}) '
        f'uv run python scripts/run_cycle.py',
        shell=True, capture_output=True, text=True, timeout=2400)
    out = (r.stdout or "") + (r.stderr or "")
    print(out[-500:])
    # find the newest run record
    records = sorted((REPO / "datasets" / "runs").glob("*.json"))
    if not records:
        print("BATCH ABORT: no run record produced"); sys.exit(1)
    rec_path = records[-1]
    rec = json.loads(rec_path.read_text())
    if not rec.get("videos"):
        # a deterministic render failure (typed PipelineStageError) marks
        # THIS intent as failed and moves on — one bad brief must never
        # kill the batch. GPU is render-idle; next loop's stop-critic is
        # a no-op, start-critic comes after the next render.
        print(f"INTENT FAILED (render produced no video) — skipping to "
              f"next intent", flush=True)
        failed_intents.append(intent)
        continue

    # QC leg with critic up
    gpu("start-critic")
    q = subprocess.run(
        f'cd {REPO} && uv run python scripts/run_qc.py '
        f'"{rec["videos"][0]}" "{rec_path}" "{rec["genre"]}"',
        shell=True, capture_output=True, text=True, timeout=900)
    print("[qc]", (q.stdout or q.stderr).strip()[-200:])
    if q.returncode != 0:
        print("BATCH ABORT: QC failed"); sys.exit(1)

    rec = json.loads(rec_path.read_text())
    results.append((rec_path.name, rec["qc"]["score"], rec["qc"]["verdict"]))
    new_done += 1
    done_intents.add(intent[:60].lower())
    print(f"CYCLE DONE {time.time()-t0:.0f}s: "
          f"{rec['qc']['score']}/10 {rec['qc']['verdict']}", flush=True)

print("\n===== BATCH COMPLETE =====")
for f in failed_intents:
    print(f"  FAILED intent (render bug): {f[:60]}")
for name, score, verdict in results:
    print(f"  {name}: {score}/10 {verdict}")
