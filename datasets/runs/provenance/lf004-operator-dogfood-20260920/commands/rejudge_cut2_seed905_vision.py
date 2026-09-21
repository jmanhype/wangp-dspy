#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from qc.audio_critic.vision_judge import run_vision_judge, VisionJudgeError
from qc.audio_critic.local_qwen_vision_judge import build_local_qwen_vision_judge
from scripts.run_jobs import _default_host

ROOT = Path("/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-42no")
video = ROOT / "datasets/runs/pull/acceptance/worker-7b851d1e3cf5/render-0001/remux.mp4"
reference = ROOT / "datasets/runs/pull/acceptance/worker-8a16858d5ace/render-0000/chain/clip0001/chain_last_frame.png"
if not reference.is_file():
    reference = ROOT / "datasets/content_briefs/lf004-operator-dogfood/plates/anchor.png"
out = ROOT / "datasets/runs/provenance/lf004-operator-dogfood-20260920/cut2-deadletter-review/seed-905-independent-vision.json"
try:
    evidence = run_vision_judge(str(video), expected_speaker="Rho (S2), the man on the RIGHT; not Tess (S1) on the LEFT", expected_action="subtle natural listening and speaking motion", judge=build_local_qwen_vision_judge(host=_default_host()), reference_image_path=str(reference))
    payload = {"passed": True, "evidence": evidence.to_dict()}
except VisionJudgeError as error:
    payload = {"passed": False, "failure": str(error), "scores": error.scores, "raw_response": error.raw_response, "mouth_bbox_raw_response": error.mouth_bbox_raw_response}
payload["video_path"] = str(video)
payload["reference_image_path"] = str(reference)
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps(payload, indent=2))
