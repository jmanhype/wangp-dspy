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
    # PACK 07 — NIGHT-SHIFT CCTV UI
    "1998 public-access sea-town puppet horror on VHS, cheap aquatic puppet set, painted cardboard coral, blue fabric ocean backdrop, rubber sea-creature puppets, washed-out local cable lighting, children's-show blocking, tiny foam houses, visible puppet seams, long wrong pause, ominous silence. VHS color-under chroma bleed, tracking noise, head-switch band, luma noise, dub-soft. Analog tape only, no digital artifacts, no copyrighted cartoon characters, no clean modern puppet show.",
    # PACK 08 — CREATURE RESPONSE (DASHCAM)
    "2004 PS2 real-time cutscene, low-poly West Coast crime game, urban neighborhood, orange smog sunset, boxy lowriders, fast-food drive-thru, liquor store parking lot, chain-link fences, stucco apartments, awkward NPC blocking, stiff poses, low-res compressed textures, vertex lighting, baked bloom, jaggies, no anti-aliasing. Interlaced 480i combing, MPEG-2 DCT block artifacts, subtitle bar at bottom. PS2 framebuffer, no modern photorealism, no remake polish.",
    # PACK 09 — PRESTIGE PUPPET NOIR
    "2004 PS2 mission objective overlay, low-resolution game HUD, bold yellow objective text, black translucent subtitle box, minimap circle, health bar, wanted stars, mission marker arrow, compressed UI texture, blocky fonts. Interlaced 480i combing, low-res alpha, UI atlas fringe halos, CRT overscan crop. PS2 framebuffer, no modern UI design, no vector graphics, no remake polish.",
    # PACK 15 — EASTERN BLOC COSMONAUT
    "late-1990s public-access analog chroma-key power-aura effect on S-VHS, bad yellow energy glow around a person, crude composite, flickering outline from imperfect key, chroma-key spill halo, color-under chroma bleed, tracking noise, misaligned composite layers, painted cosmic backdrop. Analog tape compositing only, no modern VFX, no clean anime glow.",
    # PACK 14 — YOUTH MYSTERY GIALLO
    "1998 public-access anime power-up fitness VHS, community gym studio, folding mats, painted galaxy backdrop, paper lightning bolts, cheap yellow aura overlay, fluorescent lights, sweaty instructor in martial-arts workout clothes, plastic water bottles, hand-painted motivational signs. S-VHS tracking noise, head-switch noise, color-under chroma bleed on aura, chroma-key spill, luma noise. Analog tape only, no digital effects, no modern gym commercial.",
    # PACK 19 — SOVIET INDUSTRIAL
    "straight-man office receptionist, 2007 MiniDV workplace mockumentary, calm employee behind reception desk, tired half-smile, looking toward documentary camera, beige lobby, printer, phone, paperwork, fluorescent lighting, understated reaction comedy, cheap lower third. DV-compression DCT block artifacts, interlace combing, soft digital video. No real actor likeness, no glamour portrait.",
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
    # poll health: fire-and-forget launch + short polls (cannot hang)
    healthy = False
    for attempt in range(30):  # ~150s max for model load
        chk = sh(["bash", str(REPO / "scripts" / "gpu_seq.sh"), "status"],
                 timeout=60)
        if "critic: up" in (chk.stdout or ""):
            # process up; verify endpoint actually serves
            ep = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
                 "3090", "curl -s -m 5 http://127.0.0.1:8000/health"],
                capture_output=True, text=True, timeout=60)
            if '"ok"' in (ep.stdout or ""):
                healthy = True
                break
        time.sleep(5)
    if not healthy:
        print("BATCH ABORT: critic failed to come healthy")
        sys.exit(1)
    print("[critic] healthy", flush=True)
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
