"""Fail-closed, injectable VibeVoice turn supplier."""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from predict.audio_prep import AudioPreparationError, prepare_turn_audio
from qc.audio_critic.whisper_gate import run_whisper_gate


class VibeVoiceError(ValueError):
    """Typed rejection of an invalid or unsafe VibeVoice supply run."""


MANIFEST_SCHEMA = "wangp-dspy.vibevoice-turns/v1"
PROVENANCE_SCHEMA = "wangp-dspy.vibevoice-provenance/v1"
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class VibeVoiceTurn:
    turn_index: int
    speaker: str
    text: str
    voice_reference: Path
    output: Path
    target_duration_s: float

    def __post_init__(self) -> None:
        if self.turn_index < 1:
            raise VibeVoiceError("turn_index: must start at 1")
        if not isinstance(self.speaker, str) or not self.speaker.strip():
            raise VibeVoiceError("speaker: required")
        if not isinstance(self.text, str) or not self.text.strip():
            raise VibeVoiceError("text: required")
        if not isinstance(self.voice_reference, Path):
            raise VibeVoiceError("voice_reference: path is required")
        if not isinstance(self.output, Path):
            raise VibeVoiceError("output: path is required")
        if not isinstance(self.target_duration_s, (int, float)):
            raise VibeVoiceError("target_duration_s: numeric value required")
        if not 0 < float(self.target_duration_s) <= 30:
            raise VibeVoiceError("target_duration_s: must be in (0, 30] seconds")

    def to_dict(self) -> dict:
        return {
            "turn_index": self.turn_index,
            "speaker": self.speaker,
            "text": self.text,
            "voice_reference": str(self.voice_reference),
            "output": str(self.output),
            "target_duration_s": float(self.target_duration_s),
        }


@dataclass(frozen=True)
class VibeVoiceManifest:
    schema: str
    model: Path
    model_sha256: str
    seed: int
    turns: tuple[VibeVoiceTurn, ...]
    source_path: Path

    def __post_init__(self) -> None:
        if self.schema != MANIFEST_SCHEMA:
            raise VibeVoiceError(
                f"schema: expected {MANIFEST_SCHEMA!r}, got {self.schema!r}")
        if not isinstance(self.model, Path):
            raise VibeVoiceError("model: path is required")
        if not isinstance(self.model_sha256, str) or not _SHA256_RE.fullmatch(
                self.model_sha256):
            raise VibeVoiceError("model_sha256: expected 64 lowercase hex chars")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise VibeVoiceError("seed: integer required")
        if self.seed < 0:
            raise VibeVoiceError("seed: must be non-negative")
        if not self.turns:
            raise VibeVoiceError("turns: at least one turn is required")
        indexes = [turn.turn_index for turn in self.turns]
        if indexes != list(range(1, len(indexes) + 1)):
            raise VibeVoiceError(
                f"turns: indexes must be contiguous from 1, got {indexes}")
        if len({turn.output for turn in self.turns}) != len(self.turns):
            raise VibeVoiceError("turns: output paths must be unique")

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "model": str(self.model),
            "model_sha256": self.model_sha256,
            "seed": self.seed,
            "turns": [turn.to_dict() for turn in self.turns],
        }


class VibeVoiceBackend:
    """Transformers backend using the validated VibeVoice-7B API.

    Construction intentionally loads the processor and model exactly once.
    Generation then performs one isolated model call per turn.  Keeping the
    transformers imports inside this constructor prevents merely importing the
    supplier (or parsing its CLI) from loading a GPU model.
    """

    backend_kind = "transformers.vibevoice-7b"

    def __init__(self, model: str | Path):
        model_path = Path(model)
        if not model_path.is_dir():
            raise VibeVoiceError(f"model: not readable: {model_path}")
        try:
            from transformers import (
                AutoModelForTextToWaveform,
                AutoProcessor,
                set_seed,
            )
        except Exception as exc:
            raise VibeVoiceError(
                "transformers VibeVoice backend unavailable: "
                "install the source-transformers environment"
            ) from exc
        try:
            self.processor = AutoProcessor.from_pretrained(model_path)
            self.model = AutoModelForTextToWaveform.from_pretrained(
                model_path, device_map="auto")
            self.set_seed = set_seed
        except Exception as exc:
            raise VibeVoiceError(f"VibeVoice model load failed: {exc}") from exc

    def generate(
        self,
        turn: VibeVoiceTurn,
        destination: str | Path,
        seed: int,
    ) -> Path:
        """Generate one isolated turn with the documented chat template."""
        if not isinstance(turn, VibeVoiceTurn):
            raise VibeVoiceError("turn: VibeVoiceTurn is required")
        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        conversation = [{
            "role": "0",
            "content": [
                # The validated resolver requires a plain path, not file://.
                {"type": "audio", "url": str(turn.voice_reference)},
                {"type": "text", "text": turn.text},
            ],
        }]
        try:
            self.set_seed(seed)
            inputs = self.processor.apply_chat_template(
                conversation,
                return_dict=True,
                tokenize=True,
                add_generation_prompt=True,
            ).to(self.model.device, self.model.dtype)
            audio = self.model.generate(**inputs)
            self.processor.save_audio(audio, str(destination_path))
        except Exception as exc:
            raise VibeVoiceError(
                f"VibeVoice generation failed for {destination_path}: {exc}"
            ) from exc
        if not destination_path.is_file():
            raise VibeVoiceError(
                f"VibeVoice backend did not create output: {destination_path}")
        return destination_path


def _read_json_object(path: Path, label: str) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VibeVoiceError(f"{label}: unreadable JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise VibeVoiceError(f"{label}: expected a JSON object")
    return payload


def _manifest_output_path(manifest_dir: Path, raw: object) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise VibeVoiceError("output: non-empty relative path required")
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts:
        raise VibeVoiceError(f"output: must remain under manifest root: {raw!r}")
    base = manifest_dir.resolve()
    resolved = (base / relative).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise VibeVoiceError(f"output: escapes manifest root: {raw!r}") from exc
    return resolved


def _manifest_input_path(manifest_dir: Path, raw: object, field: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise VibeVoiceError(f"{field}: non-empty path required")
    path = Path(raw)
    return path if path.is_absolute() else manifest_dir / path


def load_vibevoice_manifest(path: str | Path) -> VibeVoiceManifest:
    manifest_path = Path(path).resolve()
    payload = _read_json_object(manifest_path, "manifest")
    required = {"schema", "model", "model_sha256", "seed", "turns"}
    missing = sorted(required - payload.keys())
    if missing:
        raise VibeVoiceError(f"manifest missing key: {missing[0]}")
    manifest_dir = manifest_path.parent
    raw_turns = payload["turns"]
    if not isinstance(raw_turns, list):
        raise VibeVoiceError("turns: expected an array")
    turns = []
    required_turn = {
        "speaker", "text", "voice_reference", "output", "target_duration_s"}
    for index, raw_turn in enumerate(raw_turns, start=1):
        if not isinstance(raw_turn, Mapping):
            raise VibeVoiceError(f"turns[{index - 1}]: expected an object")
        missing_turn = sorted(required_turn - raw_turn.keys())
        if missing_turn:
            raise VibeVoiceError(
                f"turns[{index - 1}] missing key: {missing_turn[0]}")
        try:
            duration = float(raw_turn["target_duration_s"])
        except (TypeError, ValueError) as exc:
            raise VibeVoiceError(
                f"turns[{index - 1}].target_duration_s: numeric value required"
            ) from exc
        turns.append(VibeVoiceTurn(
            turn_index=index,
            speaker=raw_turn["speaker"],
            text=raw_turn["text"],
            voice_reference=_manifest_input_path(
                manifest_dir, raw_turn["voice_reference"], "voice_reference"),
            output=_manifest_output_path(manifest_dir, raw_turn["output"]),
            target_duration_s=duration,
        ))
    return VibeVoiceManifest(
        schema=payload["schema"],
        model=_manifest_input_path(manifest_dir, payload["model"], "model"),
        model_sha256=payload["model_sha256"],
        seed=payload["seed"],
        turns=tuple(turns),
        source_path=manifest_path,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _provenance_path(output: Path) -> Path:
    return output.with_name(output.name + ".vibevoice.json")


def _prepared_path(output: Path) -> Path:
    return output.with_suffix(".prepared.wav")


def _base_provenance(
    manifest: VibeVoiceManifest, turn: VibeVoiceTurn, backend_kind: str
) -> dict:
    return {
        "schema": PROVENANCE_SCHEMA,
        "turn_index": turn.turn_index,
        "speaker": turn.speaker,
        "text": turn.text,
        "model": str(manifest.model),
        "model_sha256": manifest.model_sha256,
        "seed": manifest.seed,
        "backend_kind": backend_kind,
        "voice_reference": str(turn.voice_reference),
        "output": str(turn.output),
        "prepared_path": str(_prepared_path(turn.output)),
    }


def _validate_provenance(
    manifest: VibeVoiceManifest,
    turn: VibeVoiceTurn,
    backend_kind: str,
    provenance: Mapping,
    *,
    require_prepared: bool,
) -> None:
    expected = _base_provenance(manifest, turn, backend_kind)
    for field, wanted in expected.items():
        if provenance.get(field) != wanted:
            raise VibeVoiceError(f"provenance {field} mismatch for {turn.output}")
    reference_hash = provenance.get("voice_reference_sha256")
    if not isinstance(reference_hash, str) or not _SHA256_RE.fullmatch(reference_hash):
        raise VibeVoiceError("provenance voice_reference_sha256 is invalid")
    if reference_hash != _sha256(turn.voice_reference):
        raise VibeVoiceError("voice_reference SHA-256 mismatch")
    if provenance.get("output_sha256") != _sha256(turn.output):
        raise VibeVoiceError("output SHA-256 mismatch")
    if require_prepared:
        prepared = _prepared_path(turn.output)
        if provenance.get("prepared_sha256") != _sha256(prepared):
            raise VibeVoiceError("prepared SHA-256 mismatch")


def _preflight(manifest, backend, transcriber, preparation_runner) -> str:
    if not manifest.model.is_dir():
        raise VibeVoiceError(f"model: not readable: {manifest.model}")
    for turn in manifest.turns:
        if not turn.voice_reference.is_file():
            raise VibeVoiceError(
                f"voice_reference: not readable: {turn.voice_reference}")
    if not callable(getattr(backend, "generate", None)):
        raise VibeVoiceError("backend: inject a callable generate() backend")
    backend_kind = getattr(backend, "backend_kind", None)
    if not isinstance(backend_kind, str) or not backend_kind.strip():
        raise VibeVoiceError("backend: non-empty backend_kind is required")
    if not callable(transcriber):
        raise VibeVoiceError("transcriber: callable is required")
    if not callable(preparation_runner):
        raise VibeVoiceError("preparation_runner: callable is required")
    return backend_kind


def _report(
    manifest: VibeVoiceManifest,
    records: Sequence[dict],
    *,
    status: str,
    resumed_turn_count: int = 0,
    error: str | None = None,
) -> dict:
    payload = {
        "schema": "wangp-dspy.vibevoice-report/v1",
        "manifest": str(manifest.source_path),
        "model_sha256": manifest.model_sha256,
        "seed": manifest.seed,
        "status": status,
        "turns": list(records),
        "completed_turn_count": sum(
            item.get("status") == "complete" for item in records),
        "resumed_turn_count": resumed_turn_count,
    }
    if error is not None:
        payload["error"] = error
    return payload


def _pending_record(turn: VibeVoiceTurn) -> dict:
    return {
        "turn_index": turn.turn_index,
        "speaker": turn.speaker,
        "text": turn.text,
        "status": "pending",
        "output_path": str(turn.output),
    }


def supply_vibevoice_turns(
    manifest: VibeVoiceManifest,
    *,
    backend,
    transcriber: Callable[[str], object],
    preparation_runner: Callable[[Sequence[str]], object],
    report_path: str | Path,
    resume: bool = False,
    pass_bar: float = 0.5,
) -> dict:
    """Generate, prepare, and pre-gate each turn through injected seams."""
    backend_kind = _preflight(manifest, backend, transcriber, preparation_runner)
    report_destination = Path(report_path)
    records = [_pending_record(turn) for turn in manifest.turns]
    resumed_count = 0

    for index, turn in enumerate(manifest.turns):
        record = records[index]
        provenance_path = _provenance_path(turn.output)
        prepared = _prepared_path(turn.output)
        try:
            if turn.output.exists():
                if not resume:
                    raise VibeVoiceError(
                        "existing output requires resume and matching provenance: "
                        f"{turn.output}")
                provenance = _read_json_object(provenance_path, "provenance")
                _validate_provenance(
                    manifest, turn, backend_kind, provenance,
                    require_prepared=prepared.is_file())
                resumed_count += 1
            else:
                if provenance_path.exists():
                    raise VibeVoiceError(
                        f"orphan provenance exists without output: {provenance_path}")
                turn.output.parent.mkdir(parents=True, exist_ok=True)
                try:
                    backend.generate(turn, turn.output, manifest.seed)
                except Exception as exc:
                    raise VibeVoiceError(
                        f"generation failed for {turn.output}: {exc}") from exc
                if not turn.output.is_file():
                    raise VibeVoiceError(
                        f"backend did not create output: {turn.output}")
                provenance = _base_provenance(manifest, turn, backend_kind)
                provenance.update({
                    "voice_reference_sha256": _sha256(turn.voice_reference),
                    "output_sha256": _sha256(turn.output),
                })
                _write_json(provenance_path, provenance)

            if prepared.is_file():
                provenance = _read_json_object(provenance_path, "provenance")
                preparation = provenance.get("preparation")
                if not isinstance(preparation, dict):
                    raise VibeVoiceError(
                        f"prepared output lacks preparation provenance: {prepared}")
                _validate_provenance(
                    manifest, turn, backend_kind, provenance, require_prepared=True)
            else:
                try:
                    prepared_audio = prepare_turn_audio(
                        str(turn.output),
                        str(prepared),
                        speaker_id=turn.speaker,
                        target_duration_s=turn.target_duration_s,
                        runner=preparation_runner,
                    )
                except AudioPreparationError as exc:
                    raise VibeVoiceError(f"audio preparation failed: {exc}") from exc
                preparation = prepared_audio.to_dict()
                provenance.update({
                    "preparation": preparation,
                    "prepared_sha256": _sha256(prepared),
                })
                _write_json(provenance_path, provenance)

            try:
                gate = run_whisper_gate(
                    str(prepared),
                    turn.text,
                    transcriber=transcriber,
                    phase="pre",
                    pass_bar=pass_bar,
                )
            except Exception as exc:
                record.update({
                    "status": "pre_gate_failed",
                    "prepared_path": str(prepared),
                    "whisper_gate": {
                        "phase": "pre",
                        "audio_path": str(prepared),
                        "intended_text": turn.text,
                        "passed": False,
                        "error": str(exc),
                    },
                })
                failed = _report(
                    manifest, records, status="failed", error=str(exc))
                _write_json(report_destination, failed)
                raise VibeVoiceError(str(exc)) from exc

            record.update({
                "status": "complete",
                "provenance_path": str(provenance_path),
                "prepared_path": preparation["output_path"],
                "prepared_sha256": provenance["prepared_sha256"],
                "preparation": preparation,
                "whisper_gate": gate.to_dict(),
            })
            _write_json(report_destination, _report(
                manifest, records, status="in_progress",
                resumed_turn_count=resumed_count))
        except Exception as exc:
            if record.get("status") == "pre_gate_failed":
                raise
            error = str(exc) or exc.__class__.__name__
            if record.get("status") == "pending":
                record["status"] = "generation_failed"
            _write_json(report_destination, _report(
                manifest, records, status="failed", error=error,
                resumed_turn_count=resumed_count))
            if isinstance(exc, VibeVoiceError):
                raise
            raise VibeVoiceError(error) from exc

    completed = _report(
        manifest, records, status="complete", resumed_turn_count=resumed_count)
    _write_json(report_destination, completed)
    return completed


def publish_vibevoice_turns(report: Mapping, *, host) -> list[dict]:
    """Publish complete prepared WAVs through RenderHost's asset seam."""
    required_methods = ("map_asset", "makedirs", "push_asset")
    if not all(callable(getattr(host, name, None)) for name in required_methods):
        raise VibeVoiceError(
            "host: RenderHost map_asset/makedirs/push_asset are required")
    if not isinstance(report, Mapping):
        raise VibeVoiceError("report: expected an object")
    if report.get("status") != "complete":
        raise VibeVoiceError(
            "cannot publish incomplete VibeVoice report: "
            f"{report.get('status')!r}")
    turns = report.get("turns")
    if not isinstance(turns, list) or not turns:
        raise VibeVoiceError("report.turns: non-empty array required")
    if report.get("completed_turn_count") != len(turns):
        raise VibeVoiceError("report: completed_turn_count does not match turns")

    candidates = []
    for turn in turns:
        if not isinstance(turn, Mapping) or turn.get("status") != "complete":
            raise VibeVoiceError("cannot publish incomplete VibeVoice turn")
        local = turn.get("prepared_path")
        if not isinstance(local, str) or not local:
            raise VibeVoiceError("prepared_path: required")
        local_path = Path(local)
        if not local_path.is_file():
            raise VibeVoiceError(f"prepared output is not readable: {local}")
        expected_hash = turn.get("prepared_sha256")
        if (not isinstance(expected_hash, str)
                or not _SHA256_RE.fullmatch(expected_hash)):
            raise VibeVoiceError(
                f"prepared output SHA-256 provenance is required: {local}")
        if expected_hash != _sha256(local_path):
            raise VibeVoiceError(f"prepared output SHA-256 mismatch: {local}")
        candidates.append(local_path)

    published = []
    for local in candidates:
        remote = host.map_asset(str(local))
        if not isinstance(remote, str) or not remote:
            raise VibeVoiceError(
                f"host.map_asset returned invalid path: {local!r}")
        host.makedirs(str(Path(remote).parent))
        host.push_asset(str(local))
        published.append({"local_path": str(local), "remote_path": remote})
    return published


def main(
    argv=None,
    *,
    backend_factory=None,
    transcriber=None,
    preparation_runner=None,
) -> int:
    """Run the reusable supplier entrypoint.

    Production execution uses ``VibeVoiceBackend``, the local Whisper CLI
    adapter, and ffmpeg through argv lists.  Every one of those seams can be
    injected by callers and tests; no dependency is loaded before it is
    actually selected.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m predict.vibevoice",
        description="Generate, prepare, and pre-gate isolated VibeVoice turns",
    )
    parser.add_argument("manifest", help="VibeVoice turn manifest JSON")
    parser.add_argument(
        "--report",
        help="supply report JSON (default: beside the manifest)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="resume only outputs with matching SHA provenance",
    )
    parser.add_argument(
        "--pass-bar",
        type=float,
        default=0.5,
        help="Whisper pre-gate minimum score (default: 0.5)",
    )
    parser.add_argument(
        "--whisper-model",
        default="small",
        help="local Whisper model for the required pre-gate (default: small)",
    )
    parser.add_argument(
        "--whisper-output-dir",
        default="/tmp/wangp-vibevoice-whisper",
        help="isolated local Whisper transcript directory",
    )
    args = parser.parse_args(argv)
    manifest = load_vibevoice_manifest(args.manifest)
    report_path = (
        Path(args.report)
        if args.report
        else manifest.source_path.parent / "vibevoice-report.json"
    )

    backend = (backend_factory or VibeVoiceBackend)(manifest.model)
    if transcriber is None:
        import subprocess
        from qc.audio_critic.whisper_cli import whisper_transcriber
        def whisper_runner(argv):
            return subprocess.run(
                list(argv), capture_output=True, text=True, check=False)
        transcriber = lambda audio_path: whisper_transcriber(
            audio_path, runner=whisper_runner, model=args.whisper_model,
            output_dir=args.whisper_output_dir)
    if preparation_runner is None:
        import subprocess

        def preparation_runner(argv):
            return subprocess.run(
                list(argv), capture_output=True, text=True, check=False)

    report = supply_vibevoice_turns(
        manifest,
        backend=backend,
        transcriber=transcriber,
        preparation_runner=preparation_runner,
        report_path=report_path,
        resume=args.resume,
        pass_bar=args.pass_bar,
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "MANIFEST_SCHEMA",
    "PROVENANCE_SCHEMA",
    "VibeVoiceError",
    "VibeVoiceBackend",
    "VibeVoiceManifest",
    "VibeVoiceTurn",
    "main",
    "load_vibevoice_manifest",
    "publish_vibevoice_turns",
    "supply_vibevoice_turns",
]
