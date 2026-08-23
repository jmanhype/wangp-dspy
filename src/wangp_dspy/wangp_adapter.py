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
import math
import os
import re
import subprocess
import time
from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Sequence

from wangp_dspy.profile_selector import (
    H3_FRAMES_MIN,
    H3_FRAMES_OFFSET,
    H3_FRAMES_STEP,
    ProfileDecision, SHOT_LENGTH_FLOOR_FRAMES,
)
from wangp_dspy.prompt_director import RenderBrief

H3_MODEL_TYPE = "minimax_h3_fl2va_pruned"
MULTISHOT_PROMPT_TAG = "multishot"
# WD-izly: wgp parse_script (models/minimax_h3/multishot.py:49)
# splits on (?m)^---\s*$ — the separator must be on its OWN LINE.
# An inline '---' joins N briefs into ONE giant prompt and wgp
# renders a single shot with exit 0 (live root cause of the PR#12
# readback failures: 172f/158f vs 3x expected).
SCRIPT_SEPARATOR = "\n---\n"
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
    r"(?<![\w/])(?:504|gateway[ _-]?timeout|decode[ _-]?error|decoding[ _-]?error)(?![\w/])",
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
    # Qwen PR#12: the snapped per-shot frame count actually rendered
    # (H3 grid is 107+17k; off-grid requests round UP). Consumers
    # budgeting by requested frames must read this, not the decision.
    effective_frames: int = 0

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


def normalize_frame_count(frame_count: int, minimum: int = H3_FRAMES_MIN,
                          step: int = H3_FRAMES_STEP,
                          offset: int = H3_FRAMES_OFFSET) -> int:
    """EXACT mirror of Wan2GP shared/utils/frame_scheduler.py
    normalize_frame_count (ceil to offset+k*step, clamp to minimum).

    MEASURED rule (WD-u4rv, do not guess):
    - Wan2GP/models/minimax_h3/minimax_h3_handler.py pins
      frames_minimum=107, frames_steps=17, frames_offset=5.
    - Real H3 outputs ffprobe'd at exactly 107/124/175f (=5+17k);
      96f requests render as 107f on H3 (the old 96f floor predates
      the H3 pin); cycle-3's 160f request rendered 175f.
    """
    frame_count = max(minimum, frame_count)
    step = max(1, step)
    offset = max(0, offset)
    if step <= 1:
        return frame_count
    return math.ceil(max(0, frame_count - offset) / step) * step + offset


def effective_frames_per_shot(frames: int) -> int:
    """The frames-per-shot H3 will actually render for a request."""
    return normalize_frame_count(frames)


# WD-tc04 -> WD-qn1a recalibration. Original WD-tc04 model was
# linear-2 per seam; the linear-2 guardrail then fired on a GOOD
# render (cycle-4): 4 shots, 420f actual vs 428f expected (diff 8)
# vs tolerance(4)=8 with a >= comparison. Measurements to date:
#   n=1: exact        (no seams)
#   n=3: diff 4       (2 seams, ~2.0/seam)   [WD-izly payoff, WD-tc04]
#   n=4: diff 8       (3 seams, ~2.67/seam)  [cycle-4]
# Seam loss is superlinear, not linear-2. MEASURED_SEAM_CEILING=3
# admits both data points with headroom (tol(3)=8 > 4, tol(4)=11 >
# 8) while real losses still trip (diff 15 vs tol(4)=11 raises).
# TODO(WD-qn1a): recalibrate at an n>=6 data point. The recalibration
# MUST capture PER-SEAM loss (total_diff / (n-1)) at each n so the
# loss curve can be fitted rather than endpoint-bounded.
MEASURED_SEAM_CEILING = 3


def frame_tolerance(n_briefs: int) -> int:
    """2 frames (fps rounding) + MEASURED_SEAM_CEILING per seam."""
    return 2 + MEASURED_SEAM_CEILING * max(0, n_briefs - 1)


# sentinel: frame count could not be verified (injected by tests);
# the readback check skips rather than fails on it
FRAME_COUNT_UNVERIFIED = -1


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
    # WD-u4rv: H3 quantizes to 5+17k with minimum 107 — snap the
    # request to the grid H3 will ACTUALLY render (ceil, like wgp's
    # normalize_frame_count at wgp.py:6953). 96 -> 107, 160 -> 175.
    if frames < H3_FRAMES_MIN:
        raise WanGPError(
            f"shot length {frames}f is below the H3 minimum of "
            f"{H3_FRAMES_MIN}f (5+17k grid; {SHOT_LENGTH_FLOOR_FRAMES}f "
            "floor predates the H3 pin — request 107f or more)")
    frames = effective_frames_per_shot(frames)
    if frames != decision.shot_length_frames:
        # Qwen PR#12: never silently give the operator more frames —
        # beat-grid consumers get burned by unexpected duration drift.
        print(f"[wangp-dspy] snapped frames_per_shot "
              f"{decision.shot_length_frames}f -> {frames}f (H3 5+17k grid)")
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
        "force_fps": str(FORCE_FPS),  # wgp's get_computed_fps len()s it — string per real settings files
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

    @staticmethod
    def _ffprobe_frames(host, path: str) -> int:
        """Count frames in a rendered video via the HOST seam (works
        locally and over SshHost: ffprobe runs wherever the file
        lives). Tests monkeypatch this; production shells out."""
        import subprocess as _sp
        argv = ["ffprobe", "-v", "error", "-count_frames",
                "-select_streams", "v:0",
                "-show_entries", "stream=nb_read_frames",
                "-of", "csv=p=0", path]
        proc = _sp.run(argv, stdout=_sp.PIPE, stderr=_sp.PIPE,
                       timeout=120)
        if proc.returncode != 0:
            raise WanGPError(
                "ffprobe failed during readback verification: "
                f"{proc.stderr.decode('utf-8', 'replace')[:200]}")
        out = proc.stdout.decode("utf-8", "replace").strip()
        try:
            return int(out.split(",")[-1])
        except ValueError:
            raise WanGPError(f"ffprobe returned no frame count: {out!r}")

    def __init__(self, *,
                 venv_python: str = DEFAULT_VENV_PYTHON,
                 wgp_script: str = DEFAULT_WGP_SCRIPT,
                 output_dir: str = "output",
                 wgp_outputs_dir: Optional[str] = None,
                 runner: Optional[Callable] = None,
                 host: Optional["RenderHostLike"] = None,
                 sleeper: Optional[Callable[[float], None]] = None,
                 max_attempts: int = DEFAULT_MAX_ATTEMPTS,
                 qc_factory=None,
                 assembler=None,
                 timeout: float = 3600.0):
        self.venv_python = venv_python
        self.wgp_script = wgp_script
        self.output_dir = output_dir
        # WD-5zti: wgp IGNORES --output-dir at this pin and always
        # writes to <wgp_root>/outputs/ — the readback must scan there.
        self.wgp_outputs_dir = (
            wgp_outputs_dir
            or os.path.join(
                os.path.dirname(os.path.abspath(wgp_script)), "outputs"))
        self.runner = runner or _default_runner
        # WD-h0vk: renderer-locality seam. The adapter makes NO direct
        # FS syscalls — every FS/exec operation goes through the host.
        # LocalHost preserves today's byte-identical behavior; SshHost
        # runs the renderer remotely (rsync push/pull, remote timeout).
        from wangp_dspy.render_host import LocalHost
        self.host = host or LocalHost(runner=self.runner)
        self.sleeper = sleeper or time.sleep
        self.max_attempts = max_attempts
        self.qc_factory = qc_factory
        self.assembler = assembler
        self.timeout = timeout

    # ── low-level: one wgp invocation, retry on transient failure ──

    def _check_venv(self):
        # delegated to the host (local FS or remote ssh test -x)
        self.host.check_executable(self.venv_python)

    def _run_wgp(self, settings_path: str, render_dir: str,
                 n_briefs: int = 1,
                 expected_frames: int | None = None) -> RenderResult:
        cwd, env = self.host.prepare_run(self.wgp_script)

        attempts = 0
        last_stderr = ""
        while attempts < self.max_attempts:
            attempts += 1
            attempt_started = time.time()
            # every attempt owns a private dir: a retry can never read
            # back a prior attempt's partial files
            attempt_dir = self.host.join(render_dir, f"attempt-{attempts}")
            self.host.makedirs(attempt_dir)
            cmd = [self.venv_python, self.wgp_script,
                   "--process", settings_path,
                   "--profile", DEFAULT_PROFILE_NUMBER,
                   "--output-dir", attempt_dir]
            res = self.host.run(cmd, cwd, env, self.timeout,
                                runner=self.runner)
            if res.returncode == 0:
                # WD-5zti: readback scans the attempt dir AND the wgp
                # outputs dir (wgp ignores --output-dir at this pin).
                # Only files NEWER than this attempt's start count, so
                # stale outputs never shadow or pollute the result.
                # WD-h0vk: the host returns LOCAL-namespace paths
                # (SshHost pulls first); the adapter never scans FS.
                videos = self.host.fetch_videos(
                    (attempt_dir, self.wgp_outputs_dir),
                    attempt_dir, newer_than=attempt_started)
                if not videos:
                    # WD-tc04 live wedge: remote wgp finished (fresh
                    # outputs on disk) but the ssh channel child hung /
                    # the first pull saw nothing. Retry the pull ONCE
                    # before failing — keepalives bound dead channels
                    # so this retry path is reachable within ~5min.
                    videos = self.host.fetch_videos(
                        (attempt_dir, self.wgp_outputs_dir),
                        attempt_dir, newer_than=attempt_started)
                if not videos:
                    # WD-d3b9: wgp exits 0 on skipped tasks (OOM etc.)
                    # with 'Queue completed: 0/1 tasks (1 skipped)' on
                    # stdout. Empty readback after rc 0 is a HARD typed
                    # failure carrying the stdout tail — never
                    # success-with-empty.
                    tail = "\n".join(
                        (res.stdout or "").strip().splitlines()[-5:])
                    raise WanGPError(
                        "wgp exited 0 but produced no video (task "
                        f"skipped?); stdout tail:\n{tail}")
                # WD-u4rv: verify the output actually contains the
                # expected frames (n_briefs * effective frames/shot).
                # The live cycle-3 bug (3 shots x ~175f = ~525f
                # expected, 172f actual) MUST be a typed error here.
                if expected_frames is not None:
                    want = n_briefs * expected_frames
                    tol = frame_tolerance(n_briefs)
                    for v in videos:
                        got = self._ffprobe_frames(self.host, v)
                        if got == FRAME_COUNT_UNVERIFIED:
                            continue
                        if abs(got - want) >= tol:
                            raise WanGPError(
                                f"rendered video frame count mismatch: "
                                f"expected ~{want}f "
                                f"({n_briefs} briefs x "
                                f"{expected_frames}f), ffprobe counted "
                                f"{got}f in {v!r}")
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
        render_dir = self.host.join(
            self.output_dir,
            f"render-{_RENDER_SEQ[0]:04d}")
        _RENDER_SEQ[0] += 1
        self.host.makedirs(render_dir)
        # WD-h0vk: settings are written THROUGH the host; the returned
        # (host-namespace) path is exactly what appears in the cmd —
        # the adapter never guesses a translated path.
        settings_path = self.host.write_text(
            self.host.join(render_dir, "settings.json"),
            json.dumps(settings, indent=2))
        eff = effective_frames_per_shot(decision.shot_length_frames)
        result = self._run_wgp(settings_path, render_dir,
                               n_briefs=len(briefs),
                               expected_frames=eff)
        # Qwen PR#12: surface the snapped count to consumers
        return RenderResult(attempts=result.attempts,
                            settings_path=result.settings_path,
                            output_dir=result.output_dir,
                            video_paths=result.video_paths,
                            effective_frames=eff)

    # ── pipeline: render -> RenderQC -> keepers -> Assembler ────────

    def run_pipeline(self, plans, genre: str):
        from wangp_dspy.render_qc import Verdict

        if self.qc_factory is None:
            raise WanGPError("qc_factory is required for run_pipeline")
        if self.assembler is None:
            raise WanGPError("assembler is required for run_pipeline")

        qc = self.qc_factory(genre)
        keepers = []

        def _checked_video(res: "RenderResult") -> str:
            path = res.video_path
            if not os.path.isfile(path):
                # Luna: never let the gate silently degrade to a
                # text-only critique on a missing file (guards both the
                # first QC call and the REVISE retry call)
                raise WanGPError(
                    f"rendered video {path!r} does not exist — refusing "
                    "to run QC on a missing file")
            return path

        for plan in plans:
            result = self.render([plan.brief], plan.decision)
            video = _checked_video(result)  # QC sees the RENDERED material
            verdict = qc.run(plan.brief, plan.decision, video=video)
            if verdict.verdict == Verdict.REVISE:
                # story-3 contract: exactly ONE anchored revision, then
                # typed human escalation — never silent
                result = self.render([plan.brief], plan.decision)
                verdict = qc.run(plan.brief, plan.decision,
                                 video=_checked_video(result))
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
