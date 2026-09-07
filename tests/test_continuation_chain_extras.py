"""Finding 5: chain manifests carry typed Ref2Va continuation extras."""
from __future__ import annotations


def _script():
    return [
        {"speaker": "Ada", "text": "The reactor is waking up."},
        {"speaker": "Bo", "text": "Then we leave now."},
    ]


def _characters():
    return [
        {"name": "Ada", "sn_tag": "S1", "description": "engineer, red jacket"},
        {"name": "Bo", "sn_tag": "S2", "description": "pilot, gray coat"},
    ]


def test_exact_two_second_chain_plan_uses_48_frames():
    from services.chain.controller import build_chain_plan

    plan = build_chain_plan(
        _script(), _characters(), [2.0, 2.0],
        audio_paths=["a0.wav", "a1.wav"],
        continuation_mode=True,
    )
    assert plan.continuation_mode is True
    assert plan.overlap_frames == 0
    assert [clip.frames for clip in plan.clips] == [48, 48]
    assert [clip.duration_s for clip in plan.clips] == [2.0, 2.0]


def test_continuation_manifest_has_ref2va_extras_and_chain_refs():
    from services.chain.controller import build_chain_plan, emit_render_manifest

    plan = build_chain_plan(
        _script(), _characters(), [2.0, 2.0],
        audio_paths=["a0.wav", "a1.wav"],
        continuation_mode=True,
    )
    manifest = emit_render_manifest(
        plan, plate_paths=["anchor.png", "ada.png", "bo.png"])
    assert len(manifest) == 2
    first, second = manifest
    assert first["kind"] == second["kind"] == "ref2va_render"
    assert first["continuation_extras"]["image_start"] == "anchor.png"
    assert first["continuation_extras"]["image_refs"] == [
        "anchor.png", "bo.png"]
    assert second["continuation_extras"]["image_start"].startswith("chain://")
    assert second["continuation_extras"]["image_refs"][0].startswith("chain://")
    assert second["continuation_extras"]["image_refs"][1] == "ada.png"
    assert second["continuation_extras"]["audio_guide"] == "a1.wav"
    assert second["continuation_extras"]["video_length"] == 48


def test_adapter_runtime_input_consumes_continuation_extras(tmp_path):
    from host.wangp_adapter import WanGPAdapter, _build_ref2va_runtime_input

    image = tmp_path / "frame.png"
    wav = tmp_path / "turn.wav"
    for path in (image, wav):
        path.write_bytes(b"fixture")
    adapter = WanGPAdapter(output_dir=str(tmp_path))
    job = {
        "kind": "ref2va_render",
        "prompt": "speaker says line",
        "image_refs": [str(image), str(image)],
        "audio_guide": str(wav),
        "shot_duration_s": 2.0,
        "guide_duration_s": 2.0,
        "audio_length_frames": 48,
        "audio_provenance": {
            "source_master": str(wav),
            "vocal_stem": str(wav),
            "whisper_map": str(wav),
            "keeper_window_s": [0.0, 2.0],
        },
        "continuation_extras": {
            "image_prompt_type": "S",
            "video_prompt_type": "I",
            "audio_prompt_type": "A",
            "image_start": str(image),
            "image_refs": [str(image), str(image)],
            "audio_guide": str(wav),
            "video_length": 48,
            "requested_frames": 48,
        },
    }
    inp = _build_ref2va_runtime_input(
        adapter, job, render=lambda _inp: "", runner=lambda _argv: 0,
        raw_render_path=tmp_path / "raw.mp4",
        audio_source_path=wav,
        remux_output_path=tmp_path / "remux.mp4",
        settings_path=tmp_path / "settings.json",
        sanctioned_dirs=[str(tmp_path)],
    )
    assert inp.profile_build_kwargs["continuation"] is True
    assert inp.profile_build_kwargs["image_start"] == str(image)
    assert inp.profile_build_kwargs["image_refs"] == [str(image), str(image)]
