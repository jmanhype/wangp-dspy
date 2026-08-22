"""WanGPAdapter — render pipeline adapter vs the local 3090 (WD story 5).

Ground truth (probed on the 3090 box):
- wgp is NOT on PATH. Headless render is
  ``<venv>/bin/python wgp.py --process <settings.json> --profile 3
  --output-dir <dir>`` run from the Wan2GP checkout, with
  ``$HOME/.local/bin`` prepended to PATH (nd/pvg live there).
- settings json (real saved file): model_type, prompt="multishot",
  script (the joined shot text), width, height, frames_per_shot,
  num_inference_steps, guidance_scale, embedded_guidance_scale,
  force_fps=24, seed.
- H3 multishot scripts join per-shot prompts with '---'.
- HARD floor frames_per_shot >= 96 (4s @ 24fps).
- 504s / decode-choke stderr markers are transient: retry with 60s+
  backoff; other failures are hard (no retry).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Sequence

from wangp_dspy.profile_selector import (
    ProfileDecision, SHOT_LENGTH_FLOOR_FRAMES,
)
from wangp_dspy.prompt_director import RenderBrief

H3_MODEL_TYPE = "minimax_h3_fl2va_pruned"
MULTISHOT_PROMPT_TAG = "multishot"
SCRIPT_SEPARATOR = "---"
FORCE_FPS = 24

# real probed 768p vertical
WIDTH_768P, HEIGHT_768P = 480, 832

DEFAULT_NUM_INFERENCE_STEPS = 20
DEFAULT_GUIDANCE_SCALE = 1.0
DEFAULT_EMBEDDED_GUIDANCE_SCALE = 6.0

# Wan2GP checkout on the 3090
DEFAULT_WANGP_DIR = "/home/straughter/Wan2GP"
DEFAULT_VENV_PYTHON = "/home/straughter/Wan2GP/venv/bin/python"
DEFAULT_WGP_SCRIPT = "/home/straughter/Wan2GP/wgp.py"

# profile "3" is the H3 keep (memory); --profile takes the bare number
DEFAULT_PROFILE_NUMBER = "3"

RETRY_BACKOFF_SECS = 60.0
DEFAULT_MAX_ATTEMPTS = 3

# per-instance-agnostic render sequence: each render() call gets its own
# numbered subdirectory under output_dir (F2 isolation)
_RENDER_SEQ = [0]

# transient stderr markers: gateway timeouts and decode chokes.
# Word-boundary regex — a literal "504" inside frame numbers, ms counts
# or file paths (frame 1504, step 504/1000, out504.mp4) must NOT
# classify as transient.
_TRANSIENT_RE = re.compile(
    r"(?<![\w/])(?:504|gateway[ _-]?timeout|decode[ _-]?error)(?![\w/])",
    re.I)


class WanGPError(Exception):
    """Typed adapter failure (bad settings, wgp exit, no keepers)."""


class QCEscalationError(WanGPError):
    """Typed escalation: a REVISE verdict persisted after its single
    anchored retry — a human must decide (story-3 contract)."""


@dataclass(frozen=True)
class RenderResult:
    attempts: int
    settings_path: str
    output_dir: str
    video_paths: tuple = ()

    @property
    def video_path(self) -> str:
        if not self.video_paths:
            raise WanGPError("no video files were produced")
        return self.video_paths[0]


@dataclass(frozen=True)
class RenderedShot:
    brief: RenderBrief
    decision: ProfileDecision
    path: str
    verdict: object = None


def brief_to_prompt(brief: RenderBrief) -> str:
    """Section order matches the pipeline: subject/motion/camera/style.

    The resulting shot script is a RAW pass-through into the settings
    json ``script`` field (JSON-encoded; content cannot escape its field).
    """
    return f"{brief.subject}. {brief.motion}. {brief.camera}. {brief.style}"


def build_script(prompts: Sequence[str]) -> str:
    return SCRIPT_SEPARATOR.join(prompts)


def derive_seed(seed_policy: str, briefs: Sequence[RenderBrief]) -> int:
    """Deterministic seed from the Selector's seed_policy — never a
    hardcoded constant.

    - fixed_per_story: one seed for the whole brief set (identical
      briefs -> identical seed).
    - derived_from_brief: same digest scheme (per-story granularity is
      the pipeline's job: it renders one brief per render() call).
    Unknown policies are a typed rejection.
    """
    if seed_policy not in ("fixed_per_story", "fixed_per_shot",
                           "derived_from_brief"):
        raise WanGPError(
            f"unknown seed_policy {seed_policy!r} — cannot derive a seed")
    payload = "|".join(
        f"{b.subject}.{b.motion}.{b.camera}.{b.style}" for b in briefs)
    digest = hashlib.sha256(f"{seed_policy}:{payload}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def build_settings(briefs: Sequence[RenderBrief],
                   decision: ProfileDecision) -> dict:
    frames = decision.shot_length_frames
    if isinstance(frames, bool) or not isinstance(frames, int):
        raise WanGPError(
            f"shot length must be an int (below the HARD floor of "
            f"{SHOT_LENGTH_FLOOR_FRAMES}f it is a typed rejection)")
    if frames < SHOT_LENGTH_FLOOR_FRAMES:
        raise WanGPError(
            f"shot length {frames}f is below the HARD floor of "
            f"{SHOT_LENGTH_FLOOR_FRAMES}f (4s @ {FORCE_FPS}fps)")
    if not briefs:
        raise WanGPError("at least one brief is required to render")
    width, height = WIDTH_768P, HEIGHT_768P
    if decision.resolution == "720p":
        width, height = 720, 1280
    return {
        "model_type": H3_MODEL_TYPE,
        "prompt": MULTISHOT_PROMPT_TAG,
        "script": build_script([brief_to_prompt(b) for b in briefs]),
        "width": width,
        "height": height,
        "frames_per_shot": frames,
        "num_inference_steps": DEFAULT_NUM_INFERENCE_STEPS,
        "guidance_scale": DEFAULT_GUIDANCE_SCALE,
        "embedded_guidance_scale": DEFAULT_EMBEDDED_GUIDANCE_SCALE,
        "force_fps": FORCE_FPS,
        "seed": derive_seed(decision.seed_policy, briefs),
    }


def _default_runner(cmd, cwd, env, timeout):
    proc = subprocess.Popen(cmd, cwd=cwd, env=env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # hung wgp leaks the GPU — kill and reap, then fail typed
        proc.kill()
        proc.wait()
        raise WanGPError(
            f"wgp timed out after {timeout}s and was killed")
    returncode = proc.returncode
    stdout = out.decode("utf-8", "replace") if isinstance(out, bytes) else (out or "")
    stderr = err.decode("utf-8", "replace") if isinstance(err, bytes) else (err or "")

    class _R:
        pass

    r = _R()
    r.returncode = returncode
    r.stdout = stdout
    r.stderr = stderr
    return r


def _is_transient(stderr: str) -> bool:
    return bool(_TRANSIENT_RE.search(stderr or ""))


class WanGPAdapter:
    """Render briefs as H3 shots via headless wgp, gate with RenderQC,
    hand keepers to MultiShotAssembler.

    Timeout policy: a wgp timeout is a HARD failure — the child is
    killed and reaped, and NO retry is attempted (a hang indicates a
    systemic problem, not a transient choke; retrying would just pin
    the GPU twice).

    Transient detection is a word-boundary regex exposed as TRANSIENT_RE
    so renderer subclasses can tighten/extend it.
    """

    TRANSIENT_RE = _TRANSIENT_RE

    def __init__(self, *,
                 venv_python: str = DEFAULT_VENV_PYTHON,
                 wgp_script: str = DEFAULT_WGP_SCRIPT,
                 output_dir: str = "output",
                 runner: Optional[Callable] = None,
                 sleeper: Optional[Callable[[float], None]] = None,
                 max_attempts: int = DEFAULT_MAX_ATTEMPTS,
                 qc_factory=None,
                 assembler=None,
                 timeout: float = 3600.0):
        self.venv_python = venv_python
        self.wgp_script = wgp_script
        self.output_dir = output_dir
        self.runner = runner or _default_runner
        self.sleeper = sleeper or time.sleep
        self.max_attempts = max_attempts
        self.qc_factory = qc_factory
        self.assembler = assembler
        self.timeout = timeout

    # ── low-level: one wgp invocation, retry on transient failure ──

    def _check_venv(self):
        if not (os.path.isfile(self.venv_python)
                and os.access(self.venv_python, os.X_OK)):
            raise WanGPError(
                f"venv python not found or not executable: "
                f"{self.venv_python!r} — is the Wan2GP venv present?")

    def _run_wgp(self, settings_path: str, render_dir: str) -> RenderResult:
        env = dict(os.environ)
        local_bin = os.path.join(os.path.expanduser("~"), ".local", "bin")
        env["PATH"] = local_bin + os.pathsep + env.get("PATH", "")
        cwd = os.path.dirname(os.path.abspath(self.wgp_script)) or "."

        attempts = 0
        last_stderr = ""
        while attempts < self.max_attempts:
            attempts += 1
            # every attempt owns a private dir: a retry can never read
            # back a prior attempt's partial files
            attempt_dir = os.path.join(render_dir, f"attempt-{attempts}")
            os.makedirs(attempt_dir, exist_ok=True)
            cmd = [self.venv_python, self.wgp_script,
                   "--process", settings_path,
                   "--profile", DEFAULT_PROFILE_NUMBER,
                   "--output-dir", attempt_dir]
            res = self.runner(cmd, cwd, env, self.timeout)
            if res.returncode == 0:
                # readback scoped to THIS attempt dir only
                videos = tuple(sorted(
                    os.path.join(attempt_dir, n)
                    for n in os.listdir(attempt_dir)
                    if n.lower().endswith((".mp4", ".mov", ".webm"))))
                return RenderResult(attempts=attempts,
                                    settings_path=settings_path,
                                    output_dir=attempt_dir,
                                    video_paths=videos)
            last_stderr = res.stderr or ""
            if not _is_transient(last_stderr):
                raise WanGPError(
                    f"wgp failed (exit {res.returncode}): "
                    f"{last_stderr[:500]}")
            if attempts < self.max_attempts:
                self.sleeper(RETRY_BACKOFF_SECS)
        raise WanGPError(
            f"wgp failed after {attempts} attempts: {last_stderr[:500]}")

    # ── render: briefs -> settings json -> wgp ──────────────────────

    def render(self, briefs: Sequence[RenderBrief],
               decision: ProfileDecision) -> RenderResult:
        self._check_venv()
        settings = build_settings(briefs, decision)
        # F2: every render (and each of its retries) owns a private
        # subdirectory — renders never share output files
        render_dir = os.path.join(
            self.output_dir,
            f"render-{_RENDER_SEQ[0]:04d}")
        _RENDER_SEQ[0] += 1
        os.makedirs(render_dir, exist_ok=True)
        settings_path = os.path.join(render_dir, "settings.json")
        with open(settings_path, "w", encoding="utf-8") as fh:
            json.dump(settings, fh, indent=2)
        return self._run_wgp(settings_path, render_dir)

    # ── pipeline: render -> RenderQC -> keepers -> Assembler ────────

    def run_pipeline(self, plans, genre: str):
        from wangp_dspy.render_qc import Verdict

        if self.qc_factory is None:
            raise WanGPError("qc_factory is required for run_pipeline")
        if self.assembler is None:
            raise WanGPError("assembler is required for run_pipeline")

        qc = self.qc_factory(genre)
        keepers = []
        for plan in plans:
            result = self.render([plan.brief], plan.decision)
            video = result.video_path  # QC sees the RENDERED material
            if not os.path.isfile(video):
                # Luna: never let the gate silently degrade to a
                # text-only critique on a missing file
                raise WanGPError(
                    f"rendered video {video!r} does not exist — refusing "
                    "to run QC on a missing file")
            verdict = qc.run(plan.brief, plan.decision, video=video)
            if verdict.verdict == Verdict.REVISE:
                # story-3 contract: exactly ONE anchored revision, then
                # typed human escalation — never silent
                result = self.render([plan.brief], plan.decision)
                verdict = qc.run(plan.brief, plan.decision,
                                 video=result.video_path)
                if verdict.verdict == Verdict.REVISE:
                    raise QCEscalationError(
                        f"REVISE persisted after its single anchored "
                        f"retry (anchor={verdict.anchor_field!r}) for "
                        f"brief {plan.brief.subject!r} — escalation to "
                        "human review")
            if verdict.verdict == Verdict.PASS:
                keepers.append(plan)

        # Bounds (MIN_SHOTS etc.) are the assembler's typed domain.
        return self.assembler.assemble(keepers)
