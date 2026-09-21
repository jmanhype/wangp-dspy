"""WD-mhr2: first live Pipeline cycle on the 3090.

Render leg: GLM-5.3 creative stages -> H3 render via SshHost.
QC leg runs AFTER critic re-serve (separate step, GPU sequencing) —
this script stores everything QC needs (briefs, decisions, video
paths) into datasets/ as the first labeled example.

--lane {fl2va,ref2va} (PR feat/ref2va-jobs-routing): which render lane
the cycle drives. Default fl2va = byte-identical legacy behavior; the
ref2va lane drives the recipe-configured path end-to-end through the
adapter's per-job routing (adapter may be None for dry runs).
"""
import json
import os
import sys
import time
from pathlib import Path

# repo-root imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LANES = ("fl2va", "ref2va")


def parse_lane(argv):
    """--lane {fl2va,ref2va}; default fl2va (backward compat)."""
    lane = "fl2va"
    args = list(sys.argv[1:]) if argv is None else list(argv)
    if "--lane" in args:
        i = args.index("--lane")
        if i + 1 >= len(args):
            print("--lane requires a value "
                  f"({'|'.join(LANES)})", file=sys.stderr)
            raise SystemExit(2)
        lane = args[i + 1]
    if lane not in LANES:
        print(f"unknown lane {lane!r} — choose one of "
              f"{LANES}", file=sys.stderr)
        raise SystemExit(2)
    return lane


def main():
    lane = parse_lane(None)
    from predict.lm_wiring import creative_lm
    from predict.pipeline import Pipeline, PipelineStageError
    from host.render_host import SshHost
    from host.wangp_adapter import WanGPAdapter
    from wangp.config import HostConfigError, load_host_config, render_host

    GENRE = "surreal"
    INTENT = os.environ.get(
        "WD_MHR2_INTENT",
        "a lighthouse beacon sweeping a black ocean at night, "
        "storm building, waves exploding against the rocks")

    RUN_DIR = Path(os.environ.get(
        "WANGP_RUN_DIR",
        str(Path(__file__).resolve().parent.parent / "datasets" / "runs")))
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    run_id = time.strftime("%Y%m%d-%H%M%S")
    run_path = RUN_DIR / f"{run_id}.json"

    config = load_host_config(environ=os.environ)
    host = render_host(config)
    wgp_root = config.wgp_root
    assert wgp_root is not None
    adapter = WanGPAdapter(host=host,
                           output_dir=f"{wgp_root.value}/outputs")
    if lane == "ref2va":
        # ref2va lane: route through the adapter's per-job model
        # routing (recipe-configured path). Dry-run safe: adapter=None
        # skips the real render leg (planning/evidence only).
        # WITHOUT WANGP_DRY_RUN the Pipeline below would silently run
        # the plain fl2va render and label the record lane=ref2va —
        # fail closed instead until the production render seam lands.
        if not os.environ.get("WANGP_DRY_RUN"):
            print("ref2va lane is dry-run only until the production "
                  "render seam is wired — set WANGP_DRY_RUN=1",
                  file=sys.stderr)
            raise SystemExit(3)
        adapter = None
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
        "lane": lane,
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
    print("lane:", lane)
    print("videos:", record["videos"])
    print("record:", run_path)

    # ── stage 5: QC leg (scripted, reproducible) ─────────────────
    # Critic occupies the GPU; the render has finished and wgp exited,
    # so llama-server (kept warm between cycles) can critique now.
    if record["videos"]:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from run_qc import critique
        try:
            qc = critique(record["videos"][0], GENRE)
            record["qc"] = qc
            run_path.write_text(
                json.dumps(record, indent=2, default=str))
            print(f"QC {qc['score']}/10 — {qc['verdict']}")
        except Exception as exc:  # QC failure must not lose the render
            print(f"QC LEG FAILED (render + record preserved): {exc}",
                  file=sys.stderr)
            sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except HostConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2)
