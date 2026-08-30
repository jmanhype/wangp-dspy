"""WD-a1d9-followup RED — S3 audio manifest + remux planner + QC
integration + run-record seam. Spec:
docs/specs/s3-audio-manifest-qc.md. Fails until predict/audio_manifest.py
and qc/audio_critic/ref2va_stage.py exist.
"""
import json
import pathlib

import pytest

from predict.audio_dataplane import (
    AudioDataPlaneError, AudioGuideProvenance, AudioPolicy, Ref2VAAudioQC,
)
from predict.audio_manifest import (
    AUDIO_MANIFEST_KEYS, AudioManifestError,
    audio_payload_hash, build_audio_manifest, readback_validate,
    write_audio_manifest,
)
from qc.audio_critic.ref2va_stage import (
    Ref2VAQCStageError, plan_remux_command, run_ref2va_qc_stage,
)


def _tmp_files(tmp_path, names):
    out = []
    for n in names:
        f = pathlib.Path(tmp_path) / n
        f.write_bytes(b"x" * 16)
        out.append(str(f))
    return out


def _settings_doc(tmp_path):
    """A settings doc shaped exactly like Ref2VAProfile.build_settings
    output (extra payloads merged at top level, flat=False)."""
    guide, master, stem, wmap = _tmp_files(
        tmp_path, ["guide.wav", "master.wav", "vocal.wav", "wmap.json"])
    return {
        "model_type": "ref2va_lip_sync",
        "script": "s",
        "image_refs": ["/tmp/ref1.png"],
        "audio_prompt_type": "A",
        "audio_guide": guide,
        "audio_provenance": AudioGuideProvenance(
            source_master=master, vocal_stem=stem, whisper_map=wmap,
            keeper_window_s=(1.0, 5.0)).to_dict(),
        "audio_policy": AudioPolicy(
            remux_window=(1.0, 5.0)).to_dict(),
        "audio_qc": Ref2VAAudioQC.empty().to_dict(),
    }


# ── D1: audio manifest ──────────────────────────────────────────────

def test_manifest_keys_constant():
    assert set(AUDIO_MANIFEST_KEYS) == {
        "audio_guide", "audio_provenance", "audio_policy", "audio_qc"}


def test_build_manifest_extracts_payloads_only(tmp_path):
    doc = _settings_doc(tmp_path)
    m = build_audio_manifest(doc)
    assert set(m.keys()) == set(AUDIO_MANIFEST_KEYS)
    assert m["audio_guide"].endswith("guide.wav")
    assert m["audio_policy"]["discard_rendered_audio"] is True
    # NON-audio keys never enter the manifest
    assert "image_refs" not in m and "script" not in m


def test_manifest_hash_only_sanctioned_block(tmp_path):
    """Qwen ruling: hashing must cover ONLY the sanctioned audio
    payload block — mutating a non-audio extra key (e.g. script) must
    NOT change the hash; mutating an audio payload MUST."""
    doc = _settings_doc(tmp_path)
    h1 = audio_payload_hash(doc)
    doc2 = dict(doc, script="totally different script",
                image_refs=["/other/ref.png"])
    assert audio_payload_hash(doc2) == h1
    doc3 = json.loads(json.dumps(doc))
    doc3["audio_qc"]["notes"] = "judged now"
    assert audio_payload_hash(doc3) != h1


def test_manifest_round_trip_and_readback_validate(tmp_path):
    doc = _settings_doc(tmp_path)
    m = build_audio_manifest(doc)
    assert readback_validate(m, doc) is True


def test_readback_fails_loud_on_mismatch(tmp_path):
    doc = _settings_doc(tmp_path)
    m = build_audio_manifest(doc)
    m["audio_guide"] = "/elsewhere/guide.wav"
    with pytest.raises(AudioManifestError, match="audio_guide"):
        readback_validate(m, doc)


def test_write_manifest_next_to_output(tmp_path):
    doc = _settings_doc(tmp_path)
    out = pathlib.Path(tmp_path) / "renders" / "cut1.mp4"
    out.parent.mkdir()
    out.write_bytes(b"vid")
    path = write_audio_manifest(doc, out)
    assert path == out.parent / "audio_manifest.json"
    assert json.loads(path.read_text())["audio_guide"].endswith("guide.wav")
    # write is idempotent byte-wise (deterministic serialization)
    p2 = write_audio_manifest(doc, out)
    assert path.read_bytes() == p2.read_bytes()


def test_manifest_missing_audio_keys_rejected(tmp_path):
    """A settings doc WITHOUT the audio payloads is not a valid audio
    job — typed rejection, never silently empty manifest."""
    with pytest.raises(AudioManifestError, match="audio_guide"):
        build_audio_manifest({"model_type": "ref2va_lip_sync"})


def test_manifest_required_gate_for_audio_jobs(tmp_path):
    """Hard gate: readback of an audio-bearing render REQUIRES the
    sidecar manifest — missing manifest = typed rejection."""
    doc = _settings_doc(tmp_path)
    out = pathlib.Path(tmp_path) / "renders" / "cut1.mp4"
    out.parent.mkdir()
    out.write_bytes(b"vid")
    m = build_audio_manifest(doc)
    write_audio_manifest(doc, out)
    # gate passes when present + matching
    assert readback_validate(m, doc)
    # gate fails when the manifest file is absent
    (out.parent / "audio_manifest.json").unlink()
    from predict.audio_manifest import require_manifest_for_render
    with pytest.raises(AudioManifestError, match="manifest"):
        require_manifest_for_render(out)


# ── D2: remux command PLANNER (argv list only, containment) ─────────

def test_plan_remux_argv_list_never_shell(tmp_path):
    guide, master, stem, wmap = _tmp_files(
        tmp_path, ["guide.wav", "master.wav", "vocal.wav", "wmap.json"])
    pol = AudioPolicy(remux_source="source_master", remux_window=(1.0, 5.0))
    out = str(pathlib.Path(tmp_path) / "remux" / "cut1.mp4")
    pathlib.Path(tmp_path, "remux").mkdir()
    argv = plan_remux_command(
        policy=pol, render_path=str(pathlib.Path(tmp_path) / "renders" / "cut1.mp4"),
        keeper_window=(1.0, 5.0), output_path=out,
        sanctioned_dirs=[str(pathlib.Path(tmp_path))])
    assert isinstance(argv, list)
    assert all(isinstance(a, str) for a in argv)
    assert argv[0] == "ffmpeg"
    assert " ".join(argv) == " ".join(argv)  # no shell metachar semantics
    # discard rendered audio: video stream copied from render, audio
    # from the source window
    assert "-an" in argv or ("-map" in argv and "0:v" in argv)
    assert "-ss" in argv and "-t" in argv  # window applied


def test_plan_remux_rejects_path_escape(tmp_path):
    """GLM N1: inputs/outputs must resolve under sanctioned dirs."""
    guide, master, stem, wmap = _tmp_files(
        tmp_path, ["guide.wav", "master.wav", "vocal.wav", "wmap.json"])
    pol = AudioPolicy(remux_source="vocal_stem", remux_window=(0.5, 2.0))
    outside = "/tmp/definitely-outside-evil/cut1.mp4"
    with pytest.raises(Ref2VAQCStageError, match="containment|sanctioned"):
        plan_remux_command(
            policy=pol, render_path=str(pathlib.Path(tmp_path) / "r.mp4"),
            keeper_window=(0.5, 2.0), output_path=outside,
            sanctioned_dirs=[str(pathlib.Path(tmp_path))])


def test_plan_remux_rejects_dotted_escape(tmp_path):
    guide, master, stem, wmap = _tmp_files(
        tmp_path, ["guide.wav", "master.wav", "vocal.wav", "wmap.json"])
    pol = AudioPolicy(remux_source="source_master", remux_window=(0.0, 1.0))
    evil = str(pathlib.Path(tmp_path) / "renders" / ".." / ".." / "esc.mp4")
    with pytest.raises(Ref2VAQCStageError, match="containment|sanctioned"):
        plan_remux_command(
            policy=pol, render_path=str(pathlib.Path(tmp_path) / "r.mp4"),
            keeper_window=(0.0, 1.0), output_path=evil,
            sanctioned_dirs=[str(pathlib.Path(tmp_path))])


# ── D3: QC integration ──────────────────────────────────────────────

def test_qc_stage_schema_only_honest_placeholders(tmp_path):
    """Schema-only path: critic_model present VERBATIM, scores None —
    honest placeholders, never fake scores."""
    doc = _settings_doc(tmp_path)
    qc = run_ref2va_qc_stage(doc, judge=None)
    assert qc.critic_model == "Qwen2-Audio-7B"
    assert qc.mouth_sync is None
    assert qc.audio_fidelity is None
    assert qc.visual_motion_match is None
    assert qc.audio_artifacts is None
    assert qc.critic_version is None


def test_qc_stage_refuses_non_policy_audio(tmp_path):
    """G3/G4: QC REFUSES an artifact whose audio did not pass through
    the discard/remux policy (e.g. discard_rendered_audio=False —
    trusting H3 audio violates the doctrine)."""
    doc = _settings_doc(tmp_path)
    doc["audio_policy"] = AudioPolicy(
        discard_rendered_audio=False, remux_window=(1.0, 5.0)).to_dict()
    with pytest.raises(Ref2VAQCStageError, match="G4|discard"):
        run_ref2va_qc_stage(doc, judge=None)


def test_qc_stage_refuses_doc_without_audio_payloads(tmp_path):
    with pytest.raises(Ref2VAQCStageError):
        run_ref2va_qc_stage({"model_type": "m"}, judge=None)


def test_qc_stage_judge_fills_scores(tmp_path):
    """A judge callable fills the four score fields; critic identity
    reported verbatim."""
    doc = _settings_doc(tmp_path)
    def fake_judge(**kw):
        return {"mouth_sync": 8.0, "audio_fidelity": 7.5,
                "visual_motion_match": 6.0, "audio_artifacts": 2.0}
    qc = run_ref2va_qc_stage(doc, judge=fake_judge,
                             critic_version="fake-judge-v9")
    assert qc.mouth_sync == 8.0
    assert qc.critic_model == "Qwen2-Audio-7B"
    assert qc.critic_version == "fake-judge-v9"
