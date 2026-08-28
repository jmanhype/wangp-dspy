"""WD-l5bx Tasks 4-9 RED — the six guaranteed-invocation gates.

RED-first: each pair (typed rejection + entry-point invocation) must
FAIL before implementation — proving the violation is currently
unguarded. Entry points are exercised DIRECTLY (never the gate
function in isolation).
"""
import pytest

from host.wangp_adapter import WanGPAdapter, WanGPError


def _adapter(tmp_path, **kw):
    return WanGPAdapter(output_dir=str(tmp_path / "out"), **kw)


def _brief(text="a detective walks"):
    from predict.prompt_director import RenderBrief
    return RenderBrief(subject=text, motion="walks forward",
                       camera="dolly in", style="16mm grain")


def _decision():
    from predict.profile_selector import ProfileDecision
    return ProfileDecision(model="h3", resolution="768p",
                           shot_length_frames=107,
                           seed_policy="fixed_per_story",
                           wangp_profile="profile3")


class _OkRunner:
    def __call__(self, cmd, cwd, env, timeout):
        class R:
            returncode = 0
            stdout = "ok"
            stderr = ""
        return R()


# ── G1: audio 'A' hard-reject at submit (generic path) ────────────────

def test_g1_typed_rejection():
    a = WanGPAdapter(output_dir="/tmp/x")
    with pytest.raises(WanGPError, match="G1"):
        a.submit(_brief(), _decision(), audio_prompt_type="A")


def test_g1_entry_point_fires():
    """Exercising the SUBMIT entry point directly — the gate is
    structural, not an optional pre-check."""
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    with pytest.raises(WanGPError, match="G1"):
        a.submit(_brief(), _decision(), audio_prompt_type="A")


# ── G2: guide==shot-duration exact match (Ref2VA) ─────────────────────

def test_g2_typed_rejection(tmp_path):
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    (tmp_path / "ref.png").write_bytes(b"x")
    with pytest.raises(WanGPError, match="G2"):
        a.submit(_brief(), _decision(), profile="ref2va",
                 image_refs=[str(tmp_path / "ref.png")],
                 audio_prompt_type="A",
                 guide_duration_s=7.33, shot_duration_s=8.0)


def test_g2_entry_point_fires(tmp_path):
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    (tmp_path / "ref.png").write_bytes(b"x")
    with pytest.raises(WanGPError, match="G2"):
        a.submit(_brief(), _decision(), profile="ref2va",
                 image_refs=[str(tmp_path / "ref.png")],
                 audio_prompt_type="A",
                 guide_duration_s=7.0, shot_duration_s=8.0)


# ── G3: QC consumes artifact, not spec ────────────────────────────────

def test_g3_stub_artifact_valid_spec_fails(tmp_path):
    """QC with a missing/unreadable ARTIFACT must fail even when the
    spec is perfectly valid."""
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner(),
                     qc_factory=lambda genre: _QC())
    with pytest.raises(WanGPError, match="G3"):
        a.run_pipeline([], "surreal")   # entry point


def test_g3_valid_artifact_mutated_spec_verdict_unchanged(tmp_path):
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner(),
                     qc_factory=lambda genre: _QC())
    # mutated spec must not change an artifact-based verdict
    out = a.qc_artifact("/tmp/fake.mp4", spec_text="MUTATED")
    assert out == "artifact-verdict"


class _QC:
    def run(self, brief, decision, video=""):
        if not video or "spec" in str(video):
            raise RuntimeError("no artifact")
        return "artifact-verdict"


# ── G4: H3-audio-never-trusted ────────────────────────────────────────

def test_g4_typed_rejection():
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    with pytest.raises(WanGPError, match="G4"):
        a.trust_h3_audio(_brief())


def test_g4_entry_point_fires(tmp_path):
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    with pytest.raises(WanGPError, match="G4"):
        a.submit(_brief(), _decision(), trust_h3_audio=True)


# ── G5: <d>-or-silence prompt contract ────────────────────────────────

def test_g5_typed_rejection():
    a = WanGPAdapter(output_dir="/tmp/x")
    with pytest.raises(WanGPError, match="G5"):
        a.submit(_brief("[John] looks up"), _decision())


def test_g5_entry_point_fires():
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    with pytest.raises(WanGPError, match="G5"):
        a.submit(_brief("(Mary) nods"), _decision())


# ── G6: master-lock precondition ──────────────────────────────────────

def test_g6_typed_rejection(tmp_path):
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    with pytest.raises(WanGPError, match="G6"):
        a.generate_brief("a kaiju video")   # no lock record anywhere


def test_g6_entry_point_fires(tmp_path):
    a = WanGPAdapter(output_dir="/tmp/x", runner=_OkRunner())
    with pytest.raises(WanGPError, match="G6"):
        a.generate_brief("a kaiju video")
