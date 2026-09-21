#!/usr/bin/env python3
"""Bounded baseline-vs-GEPA render/QC experiment.

Runs on the 3090. Generates two brief variants for five fixed banked
intents, renders them with identical H3 settings/seeds, and critiques the
actual MP4s through the existing llama-server QC path.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

INTENTS = [
    ("lighthouse", "a lighthouse beacon sweeping a black ocean at night, storm building, waves exploding against the rocks"),
    ("ps2_neighborhood", "2004 PS2 real-time cutscene, low-poly West Coast crime game, urban neighborhood, orange smog sunset, boxy lowriders, fast-food drive-thru, liquor store parking lot, chain-link fences, stucco apartments, awkward NPC blocking, stiff poses, low-res compressed textures, vertex lighting, baked bloom, jaggies, no anti-aliasing"),
    ("svhs_aura", "late-1990s public-access analog chroma-key power-aura effect on S-VHS, bad yellow energy glow around a person, crude composite, flickering outline from imperfect key, chroma-key spill halo, color-under chroma bleed, tracking noise, misaligned composite layers, painted cosmic backdrop"),
    ("concert", "a 1970s live concert crowd shot from the stage, handheld 16mm, sweat and confetti in the air, stage wash magenta and amber, audience arms swaying, projector flicker, film scratches"),
    ("glacier", "a glacier calving into a fjord at midday, ice tower collapsing in slow chunks, white spray column rising, dark rock cliffs framing, cold blue palette, water churn settling"),
]

DECISION = {
    "model": "h3",
    "resolution": "768p",
    "shot_length_frames": 107,
    "seed_policy": "fixed_per_shot",
    "wangp_profile": "profile3",
}
FIXED_SEED = 424242


def run(cmd, *, timeout=1200, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode:
        raise RuntimeError(f"command failed ({r.returncode}): {' '.join(cmd)}\n{r.stderr[-1000:]}")
    return r


def load_lm():
    import yaml
    import dspy
    candidates = [
        Path.home() / ".hermes/profiles/qwen-escalator/config.yaml",
        Path.home() / ".hermes/config.yaml",
    ]
    cfg_path = next((p for p in candidates if p.exists()), None)
    if cfg_path is None:
        raise RuntimeError("no Hermes config found")
    cfg = yaml.safe_load(cfg_path.read_text()) or {}
    model = cfg.get("model", {})
    key = model.get("api_key") or os.environ.get("GLM_API_KEY")
    if not key:
        env_path = Path.home() / ".hermes/.env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("GLM_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"')
                    break
    base = "https://api.z.ai/api/coding/paas/v4"
    name = "openai/glm-5.3"
    if not key:
        raise RuntimeError("no GLM key available from qwen-escalator profile")
    lm = dspy.LM(name, api_base=base, api_key=key, max_tokens=8192)
    return dspy, lm, name, base


def brief_from_result(raw):
    from predict.prompt_director import _parse_brief
    if not isinstance(raw, str):
        raw = str(raw)
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("candidate did not contain a JSON brief")
    return _parse_brief(raw[start:end + 1])


def build_predictors(dspy):
    from predict.prompt_director import RenderBriefSignature
    saved = json.loads((REPO / "compiled/baseline_director.json").read_text())
    baseline = dspy.Predict(RenderBriefSignature)
    baseline.demos = saved["predict"].get("demos", [])
    candidates = json.loads((REPO / ".gepa_checkpoint_director/candidates.json").read_text())
    if len(candidates) < 2:
        raise RuntimeError("checkpoint has no non-baseline candidate")
    # The final GEPA run selected program 0 (baseline). Use the latest
    # non-baseline evolved instruction as the explicit challenger.
    candidate = candidates[-1]
    challenger = dspy.Predict(RenderBriefSignature.with_instructions(candidate["predict"]))
    return baseline, challenger, len(candidates) - 1, len(candidate["predict"])


def make_settings(brief, repo_output):
    from host.wangp_adapter import build_settings
    from predict.profile_selector import ProfileDecision
    import host.wangp_adapter as adapter_mod
    original = adapter_mod.derive_seed
    adapter_mod.derive_seed = lambda _policy, _briefs: FIXED_SEED
    try:
        settings = build_settings([brief], ProfileDecision(**DECISION))
    finally:
        adapter_mod.derive_seed = original
    settings["seed"] = FIXED_SEED
    settings["experiment_output"] = str(repo_output)
    return settings


def render_one(brief, variant, label, root):
    from host.wangp_adapter import WanGPAdapter
    from host.render_host import LocalHost
    out_root = root / "render_work" / variant / label
    out_root.mkdir(parents=True, exist_ok=True)
    from wangp.config import load_host_config, require_host_config

    wgp_root = require_host_config(load_host_config()).wgp_root
    assert wgp_root is not None
    adapter = WanGPAdapter(host=LocalHost(), output_dir=str(out_root),
                           wgp_outputs_dir=f"{wgp_root.value}/outputs",
                           timeout=1800)
    import host.wangp_adapter as adapter_mod
    original = adapter_mod.derive_seed
    adapter_mod.derive_seed = lambda _policy, _briefs: FIXED_SEED
    try:
        result = adapter.render([brief], __import__("predict.profile_selector", fromlist=["ProfileDecision"]).ProfileDecision(**DECISION))
    finally:
        adapter_mod.derive_seed = original
    src = Path(result.video_path)
    archive = root / "videos" / variant / f"{label}.mp4"
    archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, archive)
    sha = subprocess.check_output(["shasum", "-a", "256", str(archive)], text=True).split()[0]
    return {"video": str(archive), "sha256": sha, "settings_path": result.settings_path,
            "effective_frames": result.effective_frames}


def qc_one(video, label, root):
    # Existing run_qc handles faststart remux and the 3090 llama-server.
    record = root / "records" / f"{label}.json"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps({"video": video, "label": label}, indent=2))
    r = run([sys.executable, str(REPO / "scripts/run_qc.py"), video, str(record), "surreal"], timeout=900, check=False)
    try:
        data = json.loads(record.read_text())
    except Exception:
        data = {"qc_error": (r.stdout + r.stderr)[-2000:], "returncode": r.returncode}
    return data.get("qc", data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--root", default=str(REPO / "datasets/ab_render_qc"))
    ap.add_argument("--input-briefs", help="Use a pre-generated briefs.json and skip LM generation")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.input_briefs:
        manifest = json.loads(Path(args.input_briefs).read_text())
        dspy = None
    else:
        dspy, lm, model_name, base_url = load_lm()
        baseline, challenger, candidate_index, candidate_chars = build_predictors(dspy)
        manifest = {
            "experiment": "WD-y9ab baseline vs latest non-baseline GEPA candidate",
            "model": model_name,
            "base_url": base_url,
            "decision": DECISION,
            "fixed_seed": FIXED_SEED,
            "candidate_index": candidate_index,
            "candidate_instruction_chars": candidate_chars,
            "intents": [],
        }
        with dspy.settings.context(lm=lm):
            for label, intent in INTENTS:
                row = {"label": label, "intent": intent, "variants": {}}
                for variant, predictor in (("baseline", baseline), ("gepa_candidate", challenger)):
                    try:
                        brief = brief_from_result(predictor(intent=intent).brief)
                        row["variants"][variant] = {
                            "brief": {k: getattr(brief, k, "") for k in ("subject", "motion", "camera", "style", "audio_direction", "negatives", "identity_lock")},
                            "settings": make_settings(brief, root / "videos" / variant / f"{label}.mp4"),
                        }
                    except Exception as exc:
                        row["variants"][variant] = {"brief_error": repr(exc)}
                manifest["intents"].append(row)
    (root / "briefs.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    candidate_index = manifest.get("candidate_index")
    print(json.dumps({"dry_run": args.dry_run, "briefs": str(root / "briefs.json"), "candidate_index": candidate_index, "intents": len(manifest["intents"])}, indent=2))
    if args.dry_run:
        return 0

    run(["bash", str(REPO / "scripts/gpu_seq.sh"), "stop-critic"], timeout=300)
    try:
        for row in manifest["intents"]:
            for variant in ("baseline", "gepa_candidate"):
                spec = row["variants"].get(variant, {})
                if "brief" not in spec:
                    continue
                from predict.prompt_director import _parse_brief
                brief = _parse_brief(json.dumps(spec["brief"]))
                print(f"RENDER {variant}/{row['label']}", flush=True)
                spec["render"] = render_one(brief, variant, row["label"], root)
    finally:
        run(["bash", str(REPO / "scripts/gpu_seq.sh"), "start-critic"], timeout=360)
    for row in manifest["intents"]:
        for variant in ("baseline", "gepa_candidate"):
            spec = row["variants"].get(variant, {})
            if "render" in spec:
                print(f"QC {variant}/{row['label']}", flush=True)
                spec["qc"] = qc_one(spec["render"]["video"], f"{variant}-{row['label']}", root)
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(json.dumps({"manifest": str(root / "manifest.json"), "status": "complete"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
