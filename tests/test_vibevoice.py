import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from predict.vibevoice import (
    _attempt_paths,
    VibeVoiceError,
    VibeVoiceBackend,
    load_vibevoice_manifest,
    main,
    publish_vibevoice_turns,
    supply_vibevoice_turns,
    supply_vibevoice_turns_remote,
)


MODEL_SHA = "a" * 64


class FakeBackend:
    backend_kind = "fake"

    def __init__(self):
        self.generate_calls = []

    def generate(self, turn, destination, seed):
        self.generate_calls.append((turn, Path(destination), seed))
        Path(destination).write_bytes(f"raw-{turn.speaker}".encode())


def _audio_runner(argv):
    if argv[0] == "ffprobe":
        return SimpleNamespace(returncode=0, stdout="2.333333\n", stderr="")
    if argv[0] == "ffmpeg" and "volumedetect" not in argv:
        Path(argv[-1]).write_bytes(b"prepared-audio")
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    return SimpleNamespace(
        returncode=0, stdout="", stderr="mean_volume: -20.0 dB\n")


def _manifest(tmp_path):
    model = tmp_path / "model"
    model.mkdir()
    refs = []
    for name in ("nell", "orin"):
        ref = tmp_path / f"{name}-reference.wav"
        ref.write_bytes(f"voice-{name}".encode())
        refs.append(ref)
    payload = {
        "schema": "wangp-dspy.vibevoice-turns/v1",
        "model": str(model),
        "model_sha256": MODEL_SHA,
        "seed": 42,
        "turns": [
            {
                "speaker": "Nell",
                "text": "This is the last rain we have.",
                "voice_reference": str(refs[0]),
                "output": "generated/nell.wav",
                "target_duration_s": 2.333333,
            },
            {
                "speaker": "Orin",
                "text": "Then don't spill a single drop.",
                "voice_reference": str(refs[1]),
                "output": "generated/orin.wav",
                "target_duration_s": 2.333333,
            },
        ],
    }
    path = tmp_path / "vibevoice.json"
    path.write_text(json.dumps(payload))
    return path


def _transcriber(audio_path):
    name = Path(audio_path).name
    if name.startswith("nell"):
        return "This is the last rain we have."
    if name.startswith("orin"):
        return "Then don't spill a single drop."
    raise AssertionError(f"unexpected audio path: {audio_path}")


def test_vibevoice_supplies_isolated_turns_with_provenance_and_pre_gate(
        tmp_path):
    manifest_path = _manifest(tmp_path)
    manifest = load_vibevoice_manifest(manifest_path)
    backend = FakeBackend()
    report_path = tmp_path / "supply-report.json"

    report = supply_vibevoice_turns(
        manifest,
        backend=backend,
        transcriber=_transcriber,
        preparation_runner=_audio_runner,
        report_path=report_path)

    assert report["status"] == "complete"
    assert [call[0].speaker for call in backend.generate_calls] == [
        "Nell", "Orin"]
    assert [call[1] for call in backend.generate_calls] == [
        tmp_path / "generated" / "nell.wav",
        tmp_path / "generated" / "orin.wav"]
    assert len({call[1] for call in backend.generate_calls}) == 2
    assert report["turns"][0]["prepared_path"] == str(
        tmp_path / "generated" / "nell.prepared.wav")
    assert report["turns"][1]["prepared_path"] == str(
        tmp_path / "generated" / "orin.prepared.wav")
    assert report["turns"][0]["whisper_gate"]["passed"] is True
    assert report["turns"][1]["whisper_gate"]["passed"] is True
    assert report_path.is_file()

    provenance = json.loads(
        (tmp_path / "generated" / "nell.wav.vibevoice.json").read_text())
    assert provenance["model_sha256"] == MODEL_SHA
    assert provenance["voice_reference_sha256"] == hashlib_sha256(
        tmp_path / "nell-reference.wav")
    assert provenance["output_sha256"] == hashlib_sha256(
        tmp_path / "generated" / "nell.wav")
    assert provenance["prepared_sha256"] == hashlib_sha256(
        tmp_path / "generated" / "nell.prepared.wav")


def test_scored_rejection_retries_with_bumped_seed_and_preserves_evidence(
        tmp_path):
    manifest = load_vibevoice_manifest(_manifest(tmp_path))
    backend = FakeBackend()
    orin_calls = {"count": 0}

    def flaky_transcriber(audio_path):
        if Path(audio_path).name == "orin.prepared.wav":
            orin_calls["count"] += 1
            if orin_calls["count"] == 1:
                return "When you ring, what shall come?"
        return _transcriber(audio_path)

    report = supply_vibevoice_turns(
        manifest, backend=backend, transcriber=flaky_transcriber,
        preparation_runner=_audio_runner,
        report_path=tmp_path / "report.json")

    assert report["status"] == "complete"
    assert [call[2] for call in backend.generate_calls] == [42, 42, 43]
    orin = report["turns"][1]
    assert orin["status"] == "complete"
    assert orin["generation_seed"] == 43
    assert orin["attempt_index"] == 2
    assert len(orin["seed_rejections"]) == 1
    assert orin["seed_rejections"][0]["generation_seed"] == 42
    assert Path(orin["seed_rejections"][0]["output_path"]).is_file()
    assert Path(orin["seed_rejections"][0]["prepared_path"]).is_file()
    assert Path(orin["seed_rejections"][0]["provenance_path"]).is_file()
    assert orin["whisper_gate"]["score"] == 1.0

    provenance = json.loads(Path(orin["provenance_path"]).read_text())
    assert provenance["generation_seed"] == 43
    assert provenance["attempt_count"] == 2
    assert provenance["seed_rejections"][0]["generation_seed"] == 42
    assert provenance["seed_rejections"][0]["output_path"] == str(
        tmp_path / "generated" / "orin.attempt-1.wav")
    assert provenance["seed_rejections"][0]["whisper_gate"][
        "transcript"] == "When you ring, what shall come?"
    assert (tmp_path / "generated" / "orin.attempt-1.wav").is_file()
    assert (tmp_path / "generated" / "orin.attempt-1.prepared.wav").is_file()


def test_resume_preserves_retry_audit_fields(tmp_path):
    manifest = load_vibevoice_manifest(_manifest(tmp_path))
    orin_calls = {"count": 0}

    def flaky_transcriber(audio_path):
        if Path(audio_path).name == "orin.prepared.wav":
            orin_calls["count"] += 1
            if orin_calls["count"] == 1:
                return "unrelated words"
        return _transcriber(audio_path)

    supply_vibevoice_turns(
        manifest, backend=FakeBackend(), transcriber=flaky_transcriber,
        preparation_runner=_audio_runner,
        report_path=tmp_path / "fresh-report.json")
    resumed = supply_vibevoice_turns(
        manifest, backend=FakeBackend(), transcriber=_transcriber,
        preparation_runner=_audio_runner,
        report_path=tmp_path / "resume-report.json", resume=True)
    orin = resumed["turns"][1]
    assert orin["generation_seed"] == 43
    assert orin["attempt_index"] == 2
    assert orin["attempt_count"] == 2
    assert [item["generation_seed"] for item in orin["seed_rejections"]] == [42]


def test_exhausted_scored_retries_fail_closed_and_retain_all_attempts(
        tmp_path):
    manifest = load_vibevoice_manifest(_manifest(tmp_path))
    backend = FakeBackend()

    def wrong_orin(audio_path):
        if Path(audio_path).name.startswith("orin"):
            return "When you ring, what shall come?"
        return _transcriber(audio_path)

    with pytest.raises(VibeVoiceError, match="below pass bar"):
        supply_vibevoice_turns(
            manifest, backend=backend, transcriber=wrong_orin,
            preparation_runner=_audio_runner,
            report_path=tmp_path / "report.json", seed_retries=2)

    assert [call[2] for call in backend.generate_calls] == [42, 42, 43, 44]
    report = json.loads((tmp_path / "report.json").read_text())
    orin = report["turns"][1]
    assert report["status"] == "failed"
    assert orin["generation_seed"] == 44
    assert orin["attempt_index"] == 3
    assert [item["generation_seed"] for item in orin["seed_rejections"]] == [
        42, 43, 44]
    terminal_provenance = json.loads(Path(orin["provenance_path"]).read_text())
    assert terminal_provenance["attempt_count"] == 3
    assert [item["generation_seed"] for item in
            terminal_provenance["seed_rejections"]] == [42, 43, 44]
    assert Path(orin["output_path"]).is_file()
    assert (tmp_path / "generated" / "orin.attempt-1.wav").is_file()
    assert (tmp_path / "generated" / "orin.attempt-2.wav").is_file()
    assert not (tmp_path / "generated" / "orin.attempt-3.wav").exists()


def test_unscored_transcription_error_is_never_seed_retried(tmp_path):
    manifest = load_vibevoice_manifest(_manifest(tmp_path))
    backend = FakeBackend()

    def broken_orin(audio_path):
        if Path(audio_path).name.startswith("orin"):
            raise RuntimeError("whisper transport failed")
        return _transcriber(audio_path)

    with pytest.raises(VibeVoiceError, match="whisper transport failed"):
        supply_vibevoice_turns(
            manifest, backend=backend, transcriber=broken_orin,
            preparation_runner=_audio_runner,
            report_path=tmp_path / "report.json")
    assert [call[2] for call in backend.generate_calls] == [42, 42]
    assert not (tmp_path / "generated" / "orin.attempt-1.wav").exists()


def test_retry_generation_failure_preserves_prior_rejection_evidence(tmp_path):
    manifest = load_vibevoice_manifest(_manifest(tmp_path))

    class SecondOrinGenerationFails(FakeBackend):
        def __init__(self):
            super().__init__()
            self.received_seeds = []

        def generate(self, turn, destination, seed):
            self.received_seeds.append(seed)
            if turn.speaker == "Orin" and len(
                    [c for c in self.generate_calls if c[0].speaker == "Orin"]) == 1:
                raise RuntimeError("model generation failed")
            return super().generate(turn, destination, seed)

    backend = SecondOrinGenerationFails()

    def wrong_first_orin(audio_path):
        if Path(audio_path).name == "orin.prepared.wav":
            return "When you ring, what shall come?"
        return _transcriber(audio_path)

    with pytest.raises(VibeVoiceError, match="generation failed"):
        supply_vibevoice_turns(
            manifest, backend=backend, transcriber=wrong_first_orin,
            preparation_runner=_audio_runner,
            report_path=tmp_path / "report.json")
    assert backend.received_seeds == [42, 42, 43]
    report = json.loads((tmp_path / "report.json").read_text())
    orin = report["turns"][1]
    assert orin["status"] == "generation_failed"
    assert len(orin["seed_rejections"]) == 1
    assert Path(orin["seed_rejections"][0]["output_path"]).is_file()


def test_missing_second_attempt_output_preserves_prior_rejection_evidence(tmp_path):
    manifest = load_vibevoice_manifest(_manifest(tmp_path))

    class SecondOrinOutputMissing(FakeBackend):
        def generate(self, turn, destination, seed):
            if turn.speaker == "Orin" and len(
                    [c for c in self.generate_calls if c[0].speaker == "Orin"]) == 1:
                return
            return super().generate(turn, destination, seed)

    def wrong_first_orin(audio_path):
        if Path(audio_path).name == "orin.prepared.wav":
            return "When you ring, what shall come?"
        return _transcriber(audio_path)

    with pytest.raises(VibeVoiceError, match="backend did not create output"):
        supply_vibevoice_turns(
            manifest, backend=SecondOrinOutputMissing(),
            transcriber=wrong_first_orin, preparation_runner=_audio_runner,
            report_path=tmp_path / "report.json")
    report = json.loads((tmp_path / "report.json").read_text())
    orin = report["turns"][1]
    assert orin["status"] == "generation_failed"
    assert [item["generation_seed"] for item in orin["seed_rejections"]] == [42]
    assert Path(orin["seed_rejections"][0]["output_path"]).is_file()


def test_resume_gate_failure_retains_scored_evidence(tmp_path):
    manifest = load_vibevoice_manifest(_manifest(tmp_path))
    supply_vibevoice_turns(
        manifest, backend=FakeBackend(), transcriber=_transcriber,
        preparation_runner=_audio_runner,
        report_path=tmp_path / "initial-report.json")

    def changed_orin(audio_path):
        if Path(audio_path).name.startswith("orin"):
            return "different words entirely"
        return _transcriber(audio_path)

    with pytest.raises(VibeVoiceError, match="below pass bar"):
        supply_vibevoice_turns(
            manifest, backend=FakeBackend(), transcriber=changed_orin,
            preparation_runner=_audio_runner,
            report_path=tmp_path / "resume-report.json", resume=True)
    report = json.loads((tmp_path / "resume-report.json").read_text())
    orin = report["turns"][1]
    assert report["status"] == "failed"
    assert orin["status"] == "pre_gate_failed"
    assert orin["whisper_gate"]["passed"] is False
    assert orin["whisper_gate"]["transcript"] == "different words entirely"


@pytest.mark.parametrize("seed_retries", [-1, 11, 1.5, True])
def test_invalid_seed_retry_budget_fails_before_generation(
        tmp_path, seed_retries):
    manifest = load_vibevoice_manifest(_manifest(tmp_path))
    backend = FakeBackend()
    with pytest.raises(VibeVoiceError, match="seed_retries"):
        supply_vibevoice_turns(
            manifest, backend=backend, transcriber=_transcriber,
            preparation_runner=_audio_runner,
            report_path=tmp_path / "report.json",
            seed_retries=seed_retries)
    assert backend.generate_calls == []


def test_cli_invalid_seed_retry_budget_fails_before_backend(tmp_path):
    def forbidden(_model):
        pytest.fail("invalid retry budget must reject before backend construction")

    with pytest.raises(VibeVoiceError, match="seed_retries"):
        main([str(_manifest(tmp_path)), "--seed-retries", "-1"],
             backend_factory=forbidden, transcriber=_transcriber,
             preparation_runner=_audio_runner)


def test_retry_artifact_names_cannot_collide_with_turn_outputs(tmp_path):
    manifest_path = _manifest(tmp_path)
    payload = json.loads(manifest_path.read_text())
    payload["turns"][0]["output"] = "generated/a.wav"
    payload["turns"][1]["output"] = "generated/a.attempt-1.wav"
    manifest_path.write_text(json.dumps(payload))
    manifest = load_vibevoice_manifest(manifest_path)
    backend = FakeBackend()
    with pytest.raises(VibeVoiceError, match="paths must be unique"):
        supply_vibevoice_turns(
            manifest, backend=backend, transcriber=_transcriber,
            preparation_runner=_audio_runner,
            report_path=tmp_path / "report.json")
    assert backend.generate_calls == []


def test_missing_reference_fails_before_generation(tmp_path):
    manifest_path = _manifest(tmp_path)
    payload = json.loads(manifest_path.read_text())
    payload["turns"][1]["voice_reference"] = str(
        tmp_path / "missing-reference.wav")
    manifest_path.write_text(json.dumps(payload))
    manifest = load_vibevoice_manifest(manifest_path)
    backend = FakeBackend()

    with pytest.raises(VibeVoiceError, match="voice_reference.*not readable"):
        supply_vibevoice_turns(
            manifest, backend=backend, transcriber=_transcriber,
            preparation_runner=_audio_runner,
            report_path=tmp_path / "report.json")
    assert backend.generate_calls == []


def test_module_import_does_not_load_transformers():
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-c",
         "import sys; import predict.vibevoice; "
         "print('transformers' in sys.modules)"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "False"


def test_backend_construction_is_first_transformers_import(
        tmp_path, monkeypatch):
    import builtins

    model = tmp_path / "model"
    model.mkdir()
    real_import = builtins.__import__

    def refuse_transformers(name, *args, **kwargs):
        if name == "transformers":
            raise RuntimeError("blocked before model load")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", refuse_transformers)
    with pytest.raises(VibeVoiceError, match="backend unavailable"):
        VibeVoiceBackend(model)


def _fake_transformers_backend(device_map, parameter_devices):
    calls = []

    class Inputs(dict):
        def to(self, device, dtype):
            calls.append(("to", device, dtype))
            return self

    def template(conversation, **kwargs):
        calls.append(("template", conversation, kwargs))
        return Inputs(input_ids="fake-tokens")

    def generate(**kwargs):
        calls.append(("generate", kwargs))
        return b"fake-audio"

    def save_audio(audio, destination):
        calls.append(("save", destination))
        Path(destination).write_bytes(audio)

    backend = VibeVoiceBackend.__new__(VibeVoiceBackend)
    backend.model = SimpleNamespace(
        device="meta", dtype="float16", hf_device_map=device_map,
        parameters=lambda: iter(SimpleNamespace(device=d) for d in parameter_devices),
        generate=generate,
    )
    backend.processor = SimpleNamespace(
        apply_chat_template=template, save_audio=save_audio)
    backend.set_seed = lambda seed: calls.append(("seed", seed))
    return backend, calls


@pytest.mark.parametrize("placement", ["cuda:1", 1])
def test_backend_meta_first_map_uses_concrete_cuda_per_turn(tmp_path, placement):
    manifest = load_vibevoice_manifest(_manifest(tmp_path))
    backend, calls = _fake_transformers_backend(
        {"offloaded": "meta", "cpu": "cpu", "disk": "disk", "decoder": placement},
        ["meta"],
    )
    for turn in manifest.turns:
        assert backend.generate(turn, turn.output, 42) == turn.output
        assert turn.output.read_bytes() == b"fake-audio"
    assert [c for c in calls if c[0] == "to"] == [("to", "cuda:1", "float16")] * 2
    assert [c for c in calls if c[0] == "generate"] == [
        ("generate", {"input_ids": "fake-tokens"})] * 2
    assert [c for c in calls if c[0] == "seed"] == [("seed", 42)] * 2
    assert [c for c in calls if c[0] == "template"] == [
        ("template", [{"role": "0", "content": [
            {"type": "audio", "url": str(turn.voice_reference)},
            {"type": "text", "text": turn.text},
        ]}], {"return_dict": True, "tokenize": True, "add_generation_prompt": True})
        for turn in manifest.turns
    ]


def test_backend_skips_meta_parameters_to_find_concrete_device(tmp_path):
    turn = load_vibevoice_manifest(_manifest(tmp_path)).turns[0]
    backend, calls = _fake_transformers_backend(None, ["meta", "cpu", "cuda:2"])
    backend.generate(turn, turn.output, 42)
    assert ("to", "cuda:2", "float16") in calls
    assert len([c for c in calls if c[0] == "generate"]) == 1


@pytest.mark.parametrize("placements", [
    ["meta", "meta"], ["cpu", "disk"], [], ["cuda", -1, True, "bogus:0"],
])
def test_backend_without_concrete_accelerator_rejects_before_generation(
        tmp_path, placements):
    turn = load_vibevoice_manifest(_manifest(tmp_path)).turns[0]
    backend, calls = _fake_transformers_backend(
        dict(enumerate(placements)), placements)
    with pytest.raises(VibeVoiceError, match="no concrete accelerator"):
        backend.generate(turn, turn.output, 42)
    assert calls == []
    assert not turn.output.exists()


def test_cli_runs_with_injected_backend_without_gpu(tmp_path, capsys):
    manifest_path = _manifest(tmp_path)
    created = []

    def factory(model):
        created.append(model)
        return FakeBackend()

    report_path = tmp_path / "cli-report.json"
    exit_code = main(
        [str(manifest_path), "--report", str(report_path)],
        backend_factory=factory,
        transcriber=_transcriber,
        preparation_runner=_audio_runner,
    )
    assert exit_code == 0
    assert created == [tmp_path / "model"]
    assert report_path.is_file()
    assert json.loads(report_path.read_text())["status"] == "complete"
    assert json.loads(capsys.readouterr().out)["status"] == "complete"


def test_existing_output_requires_resume_and_matching_provenance(tmp_path):
    manifest_path = _manifest(tmp_path)
    manifest = load_vibevoice_manifest(manifest_path)
    backend = FakeBackend()
    report_path = tmp_path / "report.json"
    supply_vibevoice_turns(
        manifest, backend=backend, transcriber=_transcriber,
        preparation_runner=_audio_runner, report_path=report_path)
    assert len(backend.generate_calls) == 2

    with pytest.raises(VibeVoiceError, match="existing output"):
        supply_vibevoice_turns(
            manifest, backend=FakeBackend(), transcriber=_transcriber,
            preparation_runner=_audio_runner, report_path=report_path)

    report = supply_vibevoice_turns(
        manifest, backend=backend, transcriber=_transcriber,
        preparation_runner=_audio_runner, report_path=report_path,
        resume=True)
    assert report["resumed_turn_count"] == 2
    assert len(backend.generate_calls) == 2

    output = tmp_path / "generated" / "nell.wav"
    output.write_bytes(b"tampered")
    with pytest.raises(VibeVoiceError, match="output SHA-256 mismatch"):
        supply_vibevoice_turns(
            manifest, backend=backend, transcriber=_transcriber,
            preparation_runner=_audio_runner, report_path=report_path,
            resume=True)


def test_generation_or_pre_gate_failure_never_publishes_or_queues_render(
        tmp_path):
    manifest_path = _manifest(tmp_path)
    manifest = load_vibevoice_manifest(manifest_path)
    report_path = tmp_path / "failed-report.json"

    def bad_transcriber(audio_path):
        if Path(audio_path).name.startswith("orin"):
            return "completely unrelated words"
        return _transcriber(audio_path)

    with pytest.raises(VibeVoiceError, match="below pass bar"):
        supply_vibevoice_turns(
            manifest, backend=FakeBackend(), transcriber=bad_transcriber,
            preparation_runner=_audio_runner, report_path=report_path)
    failed_report = json.loads(report_path.read_text())
    assert failed_report["status"] == "failed"
    assert failed_report["completed_turn_count"] == 1
    assert failed_report["turns"][1]["status"] == "pre_gate_failed"

    class Host:
        def __init__(self):
            self.calls = []

        def map_asset(self, path):
            self.calls.append(("map", path))
            return "/remote/" + Path(path).name

        def makedirs(self, path):
            self.calls.append(("mkdir", path))

        def push_asset(self, path):
            self.calls.append(("push", path))

    host = Host()
    with pytest.raises(VibeVoiceError, match="cannot publish incomplete"):
        publish_vibevoice_turns(failed_report, host=host)
    assert host.calls == []


def test_publish_uses_render_host_asset_seam(tmp_path):
    manifest_path = _manifest(tmp_path)
    manifest = load_vibevoice_manifest(manifest_path)
    report = supply_vibevoice_turns(
        manifest, backend=FakeBackend(), transcriber=_transcriber,
        preparation_runner=_audio_runner,
        report_path=tmp_path / "report.json")
    calls = []

    class Host:
        def map_asset(self, path):
            calls.append(("map", path))
            return "/remote/audio/" + Path(path).name

        def makedirs(self, path):
            calls.append(("mkdir", path))

        def push_asset(self, path):
            calls.append(("push", path))

    published = publish_vibevoice_turns(report, host=Host())
    assert [item["local_path"] for item in published] == [
        str(tmp_path / "generated" / "nell.prepared.wav"),
        str(tmp_path / "generated" / "orin.prepared.wav")]
    assert [item["remote_path"] for item in published] == [
        "/remote/audio/nell.prepared.wav",
        "/remote/audio/orin.prepared.wav"]
    assert ("push", str(tmp_path / "generated" / "nell.prepared.wav")) in calls
    assert all(kind != "render" for kind, _value in calls)


def test_publish_rejects_tampered_prepared_audio_before_host_calls(tmp_path):
    manifest = load_vibevoice_manifest(_manifest(tmp_path))
    report = supply_vibevoice_turns(
        manifest, backend=FakeBackend(), transcriber=_transcriber,
        preparation_runner=_audio_runner, report_path=tmp_path / "report.json")
    Path(report["turns"][0]["prepared_path"]).write_bytes(b"tampered")

    class Host:
        def map_asset(self, _path):
            raise AssertionError("host must not be called")

        def makedirs(self, _path):
            raise AssertionError("host must not be called")

        def push_asset(self, _path):
            raise AssertionError("host must not be called")

    with pytest.raises(VibeVoiceError, match="prepared output SHA-256 mismatch"):
        publish_vibevoice_turns(report, host=Host())


def hashlib_sha256(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.mark.parametrize("duration", ["1.99", "nan", "inf", "N/A", ""])
def test_short_or_invalid_reference_never_loads_backend(tmp_path, duration):
    manifest_path = _manifest(tmp_path)
    def runner(argv):
        return SimpleNamespace(returncode=0, stdout=duration, stderr="")
    def forbidden(_):
        pytest.fail("backend factory must not execute")
    with pytest.raises(VibeVoiceError, match=">=2s"):
        main([str(manifest_path)], backend_factory=forbidden,
             preparation_runner=runner, transcriber=_transcriber)
    backend = FakeBackend()
    with pytest.raises(VibeVoiceError, match=">=2s"):
        supply_vibevoice_turns(load_vibevoice_manifest(manifest_path), backend=backend,
            preparation_runner=runner, transcriber=_transcriber,
            report_path=tmp_path / "report.json")
    assert backend.generate_calls == []


class SupplyHost:
    """Host filesystem sandbox with a model-free repo module execution seam."""
    def __init__(self, root, local_root, defect=None):
        self.root, self.local_root, self.defect = root, local_root, defect
        self.calls = []
        (root / "model").mkdir(parents=True)

    def map_asset(self, path):
        self.calls.append(("map_asset", path))
        return str(self.root / Path(path).relative_to(self.local_root))

    def makedirs(self, path):
        self.calls.append(("makedirs", path))
        Path(path).mkdir(parents=True, exist_ok=True)

    def push_asset(self, path):
        self.calls.append(("push_asset", path))
        mapped = self.map_asset(path)
        Path(mapped).write_bytes(Path(path).read_bytes())
        return mapped

    def write_text(self, path, text):
        self.calls.append(("write_text", path))
        Path(path).write_text(text)
        return path

    def run_argv(self, argv, *, cwd, timeout):
        self.calls.append(("run_argv", argv))
        if self.defect == "raised_run":
            raise RuntimeError("transport failed")
        assert argv[:3] == ["/host/python", "-m", "predict.vibevoice"]
        assert cwd == "/host/repo with spaces"
        manifest = load_vibevoice_manifest(argv[3])
        backend = FakeBackend()
        backend.backend_kind = VibeVoiceBackend.backend_kind
        texts = {str(t.output.with_suffix(".prepared.wav")): t.text for t in manifest.turns}
        report_path = Path(argv[argv.index("--report") + 1])
        if self.defect and self.defect.startswith("rejected"):
            failed_index = 0 if self.defect == "rejected_first" else 1
            texts[str(manifest.turns[failed_index].output.with_suffix(".prepared.wav"))] = "unrelated words"
            if self.defect == "rejected_then_generation_fails":
                class SecondOrinGenerationFails(FakeBackend):
                    def generate(self, turn, destination, seed):
                        if (turn.speaker == "Orin" and len(
                                [c for c in self.generate_calls
                                 if c[0].speaker == "Orin"]) == 1):
                            raise RuntimeError("model generation failed")
                        return super().generate(turn, destination, seed)

                with pytest.raises(VibeVoiceError, match="generation failed"):
                    failing_backend = SecondOrinGenerationFails()
                    failing_backend.backend_kind = VibeVoiceBackend.backend_kind
                    supply_vibevoice_turns(
                        manifest, backend=failing_backend,
                        transcriber=texts.__getitem__,
                        preparation_runner=_audio_runner, report_path=report_path)
                return SimpleNamespace(returncode=1, stderr="generation failed")
            if self.defect == "rejected_then_pass":
                gate_calls = {"count": 0}
                failed_path = str(
                    manifest.turns[failed_index].output.with_suffix(".prepared.wav"))

                def flaky_transcriber(audio_path):
                    if audio_path == failed_path:
                        gate_calls["count"] += 1
                        if gate_calls["count"] == 1:
                            return "unrelated words"
                        return manifest.turns[failed_index].text
                    return texts[audio_path]

                supply_vibevoice_turns(manifest, backend=backend,
                    transcriber=flaky_transcriber, preparation_runner=_audio_runner,
                    report_path=report_path)
            else:
                with pytest.raises(VibeVoiceError, match="below pass bar"):
                    supply_vibevoice_turns(manifest, backend=backend, transcriber=texts.__getitem__,
                        preparation_runner=_audio_runner, report_path=report_path)
            if self.defect == "rejected_gate":
                payload = json.loads(report_path.read_text())
                payload["turns"][1]["whisper_gate"]["score"] = 0.4
                report_path.write_text(json.dumps(payload))
            if self.defect != "rejected_then_pass":
                return SimpleNamespace(returncode=1, stderr="pre-gate failed")
            return SimpleNamespace(returncode=0, stderr="")
        supply_vibevoice_turns(manifest, backend=backend, transcriber=texts.__getitem__,
            preparation_runner=_audio_runner, report_path=report_path)
        if self.defect == "failed_run":
            return SimpleNamespace(returncode=1, stderr="generation failed")
        if self.defect == "bad_report":
            report_path.write_text("{}")
        if self.defect == "bad_gate":
            payload = json.loads(report_path.read_text())
            payload["turns"][0]["whisper_gate"]["transcript"] = "wrong"
            report_path.write_text(json.dumps(payload))
        return SimpleNamespace(returncode=0, stderr="")

    def run_probe(self, argv, *, timeout):
        self.calls.append(("run_probe", argv))
        return 0, "", ""

    def fetch_file(self, remote, local):
        self.calls.append(("fetch_file", remote))
        if self.defect == "rejected_report_missing" and remote.endswith("report.json"):
            return local
        if self.defect == "rejected_raw_missing" and remote.endswith("turn-2.wav"):
            return local
        if self.defect in {"missing", "rejected_missing"} and remote.endswith("prepared.wav"):
            return local
        data = Path(remote).read_bytes()
        if self.defect == "rejected_raw_hash" and remote.endswith("turn-2.wav"):
            data = b"tampered"
        if self.defect in {"bad_hash", "rejected_hash"} and remote.endswith("prepared.wav"):
            data = b"tampered"
        if self.defect in {"bad_provenance", "rejected_provenance"} and remote.endswith("vibevoice.json"):
            data = b"{}"
        Path(local).write_bytes(data)
        return local


def _remote_supply(tmp_path, defect=None):
    local = tmp_path / "local"
    local.mkdir()
    manifest = load_vibevoice_manifest(_manifest(local))
    host = SupplyHost(tmp_path / "host", local, defect)
    kwargs = dict(host=host, host_python="/host/python", host_repo="/host/repo with spaces",
                  host_model=str(host.root / "model"), report_path=local / "report.json",
                  preparation_runner=_audio_runner)
    return manifest, host, kwargs


def test_remote_supply_stages_executes_and_fetches_only_through_host(tmp_path):
    manifest, host, kwargs = _remote_supply(tmp_path)
    # A host-only model path does not require local model files.
    manifest.model.rmdir()
    report = supply_vibevoice_turns_remote(manifest, **kwargs)
    assert report["status"] == "complete"
    assert Path(report["remote_report_path"]).is_file()
    assert len([c for c in host.calls if c[0] == "push_asset"]) == 2
    assert len([c for c in host.calls if c[0] == "run_argv"]) == 1
    remote_argv = next(c[1] for c in host.calls if c[0] == "run_argv")
    assert remote_argv[remote_argv.index("--seed-retries") + 1] == "2"
    assert len([c for c in host.calls if c[0] == "fetch_file"]) == 7
    lifecycle = [c for c in host.calls if c[0] in {"run_probe", "run_argv"}]
    assert [c[1][-1] for c in lifecycle[:2]] == ["stop", "3"]
    assert lifecycle[2][0] == "run_argv"
    assert lifecycle[3][1][-1] == "start"
    for turn, record in zip(manifest.turns, report["turns"]):
        assert Path(record["prepared_path"]).is_file()
        assert record["prepared_sha256"] == hashlib_sha256(record["prepared_path"])
        evidence = json.loads(Path(record["provenance_path"]).read_text())
        assert evidence["voice_reference"] == str(turn.voice_reference)
        assert evidence["prepared_sha256"] == record["prepared_sha256"]


@pytest.mark.parametrize("defect", ["missing", "bad_hash", "bad_provenance", "bad_report", "bad_gate", "failed_run"])
def test_remote_artifact_failure_never_publishes_complete_report(tmp_path, defect):
    manifest, host, kwargs = _remote_supply(tmp_path, defect)
    with pytest.raises(VibeVoiceError):
        supply_vibevoice_turns_remote(manifest, **kwargs)
    assert not Path(kwargs["report_path"]).exists()
    assert not any(t.output.exists() for t in manifest.turns)


def test_short_remote_reference_does_not_call_host(tmp_path):
    manifest, host, kwargs = _remote_supply(tmp_path)
    kwargs["preparation_runner"] = lambda _: SimpleNamespace(returncode=0, stdout="1.8")
    with pytest.raises(VibeVoiceError, match=">=2s"):
        supply_vibevoice_turns_remote(manifest, **kwargs)
    assert host.calls == []


def test_existing_local_attempt_evidence_blocks_remote_run(tmp_path):
    manifest, host, kwargs = _remote_supply(tmp_path)
    stale_attempt = _attempt_paths(manifest.turns[1].output, 1)[0]
    stale_attempt.parent.mkdir(parents=True, exist_ok=True)
    stale_attempt.write_bytes(b"stale evidence")
    with pytest.raises(VibeVoiceError, match="remote supply requires new local"):
        supply_vibevoice_turns_remote(manifest, **kwargs)
    assert host.calls == []


def test_later_short_reference_rejects_all_turns_before_backend(tmp_path):
    manifest = load_vibevoice_manifest(_manifest(tmp_path))
    backend = FakeBackend()
    def runner(argv):
        if argv[0] == "ffprobe" and "orin-reference" in argv[-1]:
            return SimpleNamespace(returncode=0, stdout="1.9", stderr="")
        return _audio_runner(argv)
    with pytest.raises(VibeVoiceError, match=">=2s"):
        supply_vibevoice_turns(manifest, backend=backend, transcriber=_transcriber,
            preparation_runner=runner, report_path=tmp_path / "report.json")
    assert backend.generate_calls == []


def test_remote_cli_never_constructs_local_backend(tmp_path, capsys):
    manifest, host, kwargs = _remote_supply(tmp_path)
    manifest.model.rmdir()
    def forbidden(_):
        pytest.fail("remote CLI must not construct a local backend")
    assert main([str(manifest.source_path), "--host-python", kwargs["host_python"],
                 "--host-repo", kwargs["host_repo"], "--host-model", kwargs["host_model"],
                 "--report", str(kwargs["report_path"])], host=host,
                backend_factory=forbidden, preparation_runner=_audio_runner) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "complete"


@pytest.mark.parametrize("failure", [None, "acquire", "release", "failed_run", "raised_run"])
def test_remote_gpu_lease_order_and_fail_closed(tmp_path, failure):
    manifest, host, kwargs = _remote_supply(tmp_path, failure)
    class Lease:
        def acquire(self, leased_host):
            assert leased_host is host
            host.calls.append(("acquire", None))
            if failure == "acquire":
                raise RuntimeError("stop failed")

        def release(self, leased_host):
            assert leased_host is host
            host.calls.append(("release", None))
            if failure == "release":
                raise RuntimeError("start failed")

    kwargs["gpu_lease"] = Lease()
    if failure is None:
        assert supply_vibevoice_turns_remote(manifest, **kwargs)["status"] == "complete"
    else:
        expected_error = RuntimeError if failure == "raised_run" else VibeVoiceError
        with pytest.raises(expected_error):
            supply_vibevoice_turns_remote(manifest, **kwargs)
        assert not Path(kwargs["report_path"]).exists()
        assert not any(t.output.exists() for t in manifest.turns)
        assert any(c[0] == "fetch_file" for c in host.calls) == (failure == "failed_run")
    order = [c[0] for c in host.calls if c[0] in {"acquire", "run_argv", "release"}]
    assert order == (["acquire", "release"] if failure == "acquire"
                     else ["acquire", "run_argv", "release"])


def test_local_cli_never_uses_gpu_lease(tmp_path):
    class ForbiddenLease:
        def acquire(self, host):
            pytest.fail("local supply must not acquire a remote lease")
        def release(self, host):
            pytest.fail("local supply must not release a remote lease")
    assert main([str(_manifest(tmp_path))], backend_factory=lambda _: FakeBackend(),
                transcriber=_transcriber, preparation_runner=_audio_runner,
                gpu_lease=ForbiddenLease()) == 0


def test_remote_cli_explicit_external_gpu_policy(tmp_path):
    manifest, host, kwargs = _remote_supply(tmp_path)
    assert main([str(manifest.source_path), "--host-python", kwargs["host_python"],
                 "--host-repo", kwargs["host_repo"], "--host-model", kwargs["host_model"],
                 "--report", str(kwargs["report_path"]), "--remote-gpu-lease", "none"],
                host=host, preparation_runner=_audio_runner) == 0
    assert not any(c[0] == "run_probe" for c in host.calls)


@pytest.mark.parametrize("failed_action", ["stop", "start"])
def test_default_remote_lease_rejects_judge_control_failure(tmp_path, failed_action):
    manifest, host, kwargs = _remote_supply(tmp_path)
    def probe(argv, *, timeout):
        host.calls.append(("run_probe", argv))
        return (1, "", "control failed") if argv[-1] == failed_action else (0, "", "")
    host.run_probe = probe
    with pytest.raises(VibeVoiceError, match="GPU lease .* failed"):
        supply_vibevoice_turns_remote(manifest, **kwargs)
    assert host.calls[-1][1][-1] == "start"
    assert any(c[0] == "run_argv" for c in host.calls) == (failed_action == "start")
    assert not Path(kwargs["report_path"]).exists()
    assert not any(t.output.exists() for t in manifest.turns)


def test_remote_rejection_preserves_verified_listening_bundle_without_publication(tmp_path):
    manifest, host, kwargs = _remote_supply(tmp_path, "rejected")
    with pytest.raises(VibeVoiceError, match="rejected evidence"):
        supply_vibevoice_turns_remote(manifest, **kwargs)
    assert not Path(kwargs["report_path"]).exists()
    assert not any(t.output.exists() for t in manifest.turns)
    bundles = list((Path(kwargs["report_path"]).parent / "rejected").iterdir())
    assert len(bundles) == 1
    report = json.loads((bundles[0] / "report.json").read_text())
    assert report["status"] == "failed"
    assert report["turns"][1]["whisper_gate"]["transcript"] == "unrelated words"
    assert report["turns"][1]["whisper_gate"]["score"] == 0.0
    assert report["turns"][1]["whisper_gate"]["pass_bar"] == 0.6
    assert report["turns"][1]["whisper_gate"]["passed"] is False
    for record in report["turns"]:
        assert Path(record["output_path"]).is_file()
        assert Path(record["prepared_path"]).is_file()
        assert Path(record["provenance_path"]).is_file()
    failed_rejections = report["turns"][1]["seed_rejections"]
    assert [item["generation_seed"] for item in failed_rejections] == [42, 43, 44]
    assert all(Path(item["output_path"]).is_file() for item in failed_rejections)
    assert all(Path(item["prepared_path"]).is_file() for item in failed_rejections)
    assert all(Path(item["provenance_path"]).is_file() for item in failed_rejections)
    assert (bundles[0] / "report.remote.json").is_file()
    assert len(list(bundles[0].glob("*.provenance.remote.json"))) == 4
    original_attempt = json.loads((
        bundles[0] / "turn-2.attempt-1.wav.provenance.remote.json").read_text())
    assert original_attempt["output"].startswith(str(host.root))
    assert ".attempt-1.wav" in original_attempt["output"]
    calls = list(host.calls)
    with pytest.raises(VibeVoiceError, match="incomplete"):
        publish_vibevoice_turns(report, host=host)
    assert host.calls == calls


def test_remote_retry_success_localizes_every_attempt_artifact(tmp_path):
    manifest, host, kwargs = _remote_supply(tmp_path, "rejected_then_pass")
    report = supply_vibevoice_turns_remote(manifest, **kwargs)
    assert report["status"] == "complete"
    orin = report["turns"][1]
    assert orin["generation_seed"] == 43
    assert [item["generation_seed"] for item in orin["seed_rejections"]] == [42]
    assert all(Path(item["output_path"]).is_file() for item in orin["seed_rejections"])
    assert all(Path(item["prepared_path"]).is_file() for item in orin["seed_rejections"])
    assert all(Path(item["provenance_path"]).is_file() for item in orin["seed_rejections"])
    provenance = json.loads(Path(orin["provenance_path"]).read_text())
    assert provenance["seed_rejections"][0][
        "provenance_path"] == orin["seed_rejections"][0]["provenance_path"]
    assert Path(provenance["seed_rejections"][0]["output_path"]).is_file()


def test_remote_retry_generation_failure_preserves_prior_attempts(tmp_path):
    manifest, host, kwargs = _remote_supply(
        tmp_path, "rejected_then_generation_fails")
    with pytest.raises(VibeVoiceError, match="rejected evidence"):
        supply_vibevoice_turns_remote(manifest, **kwargs)
    bundle = next((Path(kwargs["report_path"]).parent / "rejected").iterdir())
    report = json.loads((bundle / "report.json").read_text())
    orin = report["turns"][1]
    assert report["status"] == "failed"
    assert orin["status"] == "generation_failed"
    assert [item["generation_seed"] for item in orin["seed_rejections"]] == [42]
    assert Path(orin["seed_rejections"][0]["output_path"]).is_file()
    assert Path(orin["seed_rejections"][0]["prepared_path"]).is_file()
    assert Path(orin["seed_rejections"][0]["provenance_path"]).is_file()
    assert not Path(orin["output_path"]).exists()


@pytest.mark.parametrize("defect", ["rejected_missing", "rejected_hash", "rejected_provenance", "rejected_gate",
                                  "rejected_raw_missing", "rejected_raw_hash", "rejected_report_missing"])
def test_remote_rejected_missing_or_tampered_evidence_fails_closed(tmp_path, defect):
    manifest, host, kwargs = _remote_supply(tmp_path, defect)
    with pytest.raises(VibeVoiceError):
        supply_vibevoice_turns_remote(manifest, **kwargs)
    assert not Path(kwargs["report_path"]).exists()
    assert not any(t.output.exists() for t in manifest.turns)
    assert not (Path(kwargs["report_path"]).parent / "rejected").exists()


def test_remote_first_turn_rejected_leaves_remaining_turn_pending(tmp_path):
    manifest, host, kwargs = _remote_supply(tmp_path, "rejected_first")
    with pytest.raises(VibeVoiceError, match="rejected evidence"):
        supply_vibevoice_turns_remote(manifest, **kwargs)
    bundle = next((Path(kwargs["report_path"]).parent / "rejected").iterdir())
    report = json.loads((bundle / "report.json").read_text())
    assert report["completed_turn_count"] == 0
    assert report["turns"][1]["status"] == "pending"
    assert not Path(report["turns"][1]["output_path"]).exists()
    assert [item["generation_seed"] for item in
            report["turns"][0]["seed_rejections"]] == [42, 43, 44]
    assert all(Path(item["provenance_path"]).is_file() for item in
               report["turns"][0]["seed_rejections"])
    assert len([c for c in host.calls if c[0] == "fetch_file"]) == 10
