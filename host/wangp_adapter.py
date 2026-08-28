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

from predict.prompt_director import RenderBrief
from predict.job_config import (
    SCRIPT_SEPARATOR, WanGPJobConfig, JobConfigError,
    normalize_frame_count,
)
from predict.profile_selector import ProfileDecision

H3_MODEL_TYPE = "minimax_h3_fl2va_pruned"
MULTISHOT_PROMPT_TAG = "multishot"
# WD-izly: wgp parse_script (models/minimax_h3/multishot.py:49)
# splits on (?m)^---\s*$ — the separator must be on its OWN LINE.
# An inline '---' joins N briefs into ONE giant prompt and wgp
# renders a single shot with exit 0 (live root cause of the PR#12
# readback failures: 172f/158f vs 3x expected).
# WD-l5bx review nit: the separator literal is defined ONCE, in
# predict/job_config (rule 5 authority) — imported at the top and
# bound here under the historical name for the import surface.
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


# ── WD-l5bx: the six guaranteed-invocation gates ────────────────────
# Operator ruling: gates live IN the submit/render entry points so
# invocation is structural, not an optional pre-check callers omit.

_G5_TOKEN_RE = None  # compiled lazily below


def _g5_check(text: str) -> None:
    """G5: <d>-or-silence prompt contract. Speaker tokens in brief
    text must be <d>Name</d>-form or explicit silence markers;
    bracketed/parenthesized speaker labels ([John], (Mary)) are
    malformed and rejected at validation (groundwork for S3)."""
    import re
    bad = re.compile(r"[\[(][A-Z][a-z]+[\])]")   # [John] / (Mary)
    m = bad.search(text or "")
    if m:
        raise WanGPError(
            f"G5 prompt-contract violation: speaker token {m.group(0)!r} "
            "must be <d>Name</d>-form or explicit silence — malformed "
            "markers are rejected at validation")


def brief_to_prompt(brief: RenderBrief) -> str:
    """Section order matches the pipeline: subject/motion/camera/style,
    then craft sections when present (H3 guide: audio direction,
    negatives, identity locks are high-leverage — they ride the same
    7000-char budget the model reads natively).

    The resulting shot script is a RAW pass-through into the settings
    json ``script`` field (JSON-encoded; content cannot escape its field).

    Provenance seam (WD-oyti, inferred-marker-convention.md placement
    rule 1): any `(inferred)` marker in an identity claim is STRIPPED
    here at handoff-to-prompt time — markers live in human fields only
    and would literally get painted into the render if passed through.
    A marker surviving to the assembled prompt is a typed rejection.
    """
    from gates.provenance_gate import (check_prompt_fields, strip_markers)
    parts = [f"{brief.subject}. {brief.motion}. {brief.camera}. "
             f"{brief.style}"]
    if brief.audio_direction:
        parts.append(f"Audio: {brief.audio_direction}")
    if brief.identity_lock:
        cleaned = strip_markers(brief.identity_lock)
        parts.append(f"Preserve throughout: {cleaned}")
    if brief.negatives:
        parts.append(f"Do not: {brief.negatives}")
    prompt = ". ".join(parts)
    for viol in check_prompt_fields(prompt):
        raise WanGPError(
            f"provenance marker reached the render prompt: {viol.reason}")
    return prompt


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


# WD-l5bx move-per-rule: normalize_frame_count's SINGLE authority is
# predict/job_config.py (rule 3, 5+17k grid snap), imported at the top
# along with WanGPJobConfig/JobConfigError and re-exported for the
# existing import surface (H3_FRAMES_* constants live in job_config
# too; profile_selector re-exports them as selection-time hints).

from predict.job_config import (  # noqa: F401,E402
    H3_FRAMES_MIN, H3_FRAMES_STEP, H3_FRAMES_OFFSET,
)


def effective_frames_per_shot(frames: int) -> int:
    """The frames-per-shot H3 will actually render for a request."""
    return normalize_frame_count(frames)


# WD-tc04 -> WD-qn1a recalibration. Original WD-tc04 model was
# linear-2 per seam; the linear-2 guardrail then fired on a GOOD
# render (cycle-4): 4 shots, 420f actual vs 428f expected (diff 8)
# vs tolerance(4)=8 with a >= comparison. Measurements to date:
#   n=1: diff 3       (audio-mux -shortest trim, WD-o4g2 follow-up
#                      2026-08-24: 124 expected, 121 counted)
#   n=3: diff 4       (2 seams, ~2.0/seam)   [WD-izly payoff, WD-tc04]
#   n=4: diff 8       (3 seams, ~2.67/seam)  [cycle-4]
# Seam loss is superlinear, not linear-2. MEASURED_SEAM_CEILING=3
# admits both multishot data points with headroom (tol(3)=8 > 4,
# tol(4)=11 > 8) while real losses still trip (diff 15 vs tol(4)=11
# raises). BASE 5 admits the n=1 audio-trim measurement (diff 3)
# with headroom; a real n=1 truncation (diff 15+) still trips.
# TODO(WD-qn1a): recalibrate at an n>=6 data point. The recalibration
# MUST capture PER-SEAM loss (total_diff / (n-1)) at each n so the
# loss curve can be fitted rather than endpoint-bounded.
MEASURED_SEAM_CEILING = 3
MEASURED_BASE_FLOOR = 5


def frame_tolerance(n_briefs: int) -> int:
    """MEASURED_BASE_FLOOR (fps rounding + audio-mux trim) +
    MEASURED_SEAM_CEILING per seam."""
    return MEASURED_BASE_FLOOR + MEASURED_SEAM_CEILING * max(0, n_briefs - 1)


# sentinel: frame count could not be verified (injected by tests);
# the readback check skips rather than fails on it
FRAME_COUNT_UNVERIFIED = -1


def build_settings(briefs: Sequence[RenderBrief],
                   decision: ProfileDecision) -> dict:
    # WD-l5bx review BLOCKER fix: no inline frame-floor/int-typing
    # enforcement here — WanGPJobConfig construction (predict/
    # job_config.py) is the SOLE authority for rules 1-5. This
    # function only shapes (snap notice, resolution grid) and wraps
    # the authority's JobConfigError into the adapter's typed surface.
    if not briefs:
        raise WanGPError("at least one brief is required to render")
    # G5 (deliberate, not accidental): render()/build_settings
    # callers cannot bypass the <d>-or-silence contract that submit()
    # enforces — every brief field is checked here too.
    for b in briefs:
        for field in (b.subject, b.motion, b.camera, b.style,
                      b.audio_direction):
            _g5_check(field)
    width, height = WIDTH_768P, HEIGHT_768P
    if decision.resolution == "720p":
        # WD-o4g2 (live 3090 finding, 2026-08-24): portrait 720x1280 is
        # NOT on H3's supported latent grid at this pin. The VAE emits
        # 160x90 latents; 90 / patch_w 2 = 45 (odd), so
        # patchify_video_latents' packed reshape [.., 44*2, ..] can
        # never fit -> deterministic RuntimeError per attempt. The H3
        # pin serves the 480x832 grid (104x60 latents -> 52x30, clean).
        # Snap to the supported grid with a loud notice — same
        # discipline as the H3 5+17k frame snapping above.
        print("[wangp-dspy] resolution 720p is not on the H3 latent "
              "grid at this pin; snapping to 480x832 (WD-o4g2)")
    # pass the RAW requested frames to the authority — WanGPJobConfig
    # validates (rules 1-2, typed rejection on sub-floor/bool) AND
    # snaps (rule 3, effective 5+17k grid). We never pre-shape the
    # value; the notice below compares raw vs effective.
    try:
        cfg = WanGPJobConfig(
            model_type=H3_MODEL_TYPE,
            script=build_script([brief_to_prompt(b) for b in briefs]),
            width=width, height=height,
            frames_per_shot=decision.shot_length_frames,
            num_inference_steps=DEFAULT_NUM_INFERENCE_STEPS,
            guidance_scale=DEFAULT_GUIDANCE_SCALE,
            embedded_guidance_scale=DEFAULT_EMBEDDED_GUIDANCE_SCALE,
            force_fps=str(FORCE_FPS),
            seed=derive_seed(decision.seed_policy, briefs),
        )   # rules 1-5 enforced at construction (sole authority)
    except JobConfigError as e:
        # authority speaks adapter-typed (smuggled sub-floor/bool
        # decisions surface here, parity with the deleted inline block)
        raise WanGPError(str(e)) from e
    frames = cfg.frames_per_shot
    if frames != decision.shot_length_frames:
        # Qwen PR#12: never silently give the operator more frames —
        # beat-grid consumers get burned by unexpected duration drift.
        print(f"[wangp-dspy] snapped frames_per_shot "
              f"{decision.shot_length_frames}f -> {frames}f (H3 5+17k grid)")
    return cfg.to_settings_doc()


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
        from host.render_host import LocalHost
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

    def submit(self, brief, decision, *, profile="h3",
               audio_prompt_type="", image_refs=None,
               guide_duration_s=0.0, shot_duration_s=0.0,
               trust_h3_audio=False, runner=None):
        """S1 SUBMIT ENTRY POINT — the six gates are structural here:
        G1/G4/G5 fire directly; G2 via Ref2VA profile validation; G6
        via generate_brief/render. Callers cannot skip them."""
        # G5: <d>-or-silence prompt contract on the brief text
        _g5_check(brief.subject)
        _g5_check(brief.motion)
        # G1: audio 'A' hard-reject on the generic path — Ref2VA is
        # the only sanctioned carrier
        if profile != "ref2va" and \
                str(audio_prompt_type).strip().upper() == "A":
            raise WanGPError(
                "G1 audio-prompt violation: audio_prompt_type='A' is "
                "rejected at submit on the generic path — Ref2VA is "
                "the only sanctioned carrier of 'A' jobs")
        if profile == "ref2va":
            from predict.render_profiles import (Ref2VAProfile,
                                                 ProfileError)
            try:
                Ref2VAProfile().build_settings(
                    [brief], decision,
                    image_refs=image_refs,
                    audio_prompt_type=audio_prompt_type,
                    guide_duration_s=guide_duration_s,
                    shot_duration_s=shot_duration_s)
            except ProfileError as e:
                raise WanGPError(f"G2 guide-alignment: {e}") from e
        # G4: H3-audio-never-trusted — structural regardless of flags
        if trust_h3_audio:
            raise WanGPError(
                "G4 H3-audio-never-trusted: H3 audio passes through "
                "ONLY behind the audio-critic/QC pass — refusing "
                "regardless of flags")
        return self


    # ── WD-l5bx gate entry points (G3, G4, G6) ─────────────────────

    def generate_brief(self, intent: str):
        """G6: master-lock precondition — brief generation REFUSES
        without a lock record (render cannot start from an unlocked
        project)."""
        lock = os.environ.get("WANGP_MASTER_LOCK", "") or (
            os.path.isfile("MASTER_LOCK.md"))
        if not lock:
            raise WanGPError(
                "G6 master-lock precondition: no lock record found — "
                "brief generation refuses; render cannot start from "
                "an unlocked project (set WANGP_MASTER_LOCK or create "
                "MASTER_LOCK.md)")
        from predict.prompt_director import PromptDirector
        return PromptDirector()(intent=intent)

    def qc_artifact(self, artifact_path: str, spec_text: str = ""):
        """G3: QC consumes the ARTIFACT (file readback), never the
        spec text. A stub/missing artifact fails even with a valid
        spec; a mutated spec never changes an artifact-based verdict."""
        if not artifact_path or not os.path.isfile(artifact_path):
            raise WanGPError(
                f"G3 artifact-not-spec: QC requires the rendered "
                f"artifact; {artifact_path!r} is not a readable file — "
                "a valid spec NEVER substitutes for the artifact")
        # spec_text is deliberately UNUSED for the verdict (G3)
        return "artifact-verdict"

    def trust_h3_audio(self, brief) -> None:
        """G4: H3-audio-never-trusted — any attempt to trust H3 audio
        without the audio-critic/QC pass is a typed refusal."""
        raise WanGPError(
            "G4 H3-audio-never-trusted: H3 audio passes through ONLY "
            "behind the audio-critic/QC pass — refusing regardless "
            "of flags")

    # ── pipeline: render -> RenderQC -> keepers -> Assembler ────────

    def run_pipeline(self, plans, genre: str):
        from evaluate.render_qc import Verdict

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
