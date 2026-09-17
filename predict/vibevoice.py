"""Fail-closed, injectable VibeVoice turn supplier."""
from __future__ import annotations

import hashlib
import json
import os
import re
import math
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from predict.audio_prep import (
    AudioPreparationError, PreparedTurnAudio, prepare_turn_audio, _rms_from_probe,
)
from qc.audio_critic.whisper_gate import WhisperGateError, run_whisper_gate


class VibeVoiceError(ValueError):
    """Typed rejection of an invalid or unsafe VibeVoice supply run."""


class VibeVoiceJudgeLease:
    """Timeshare the repo-managed judge; this is not a cross-process lock."""

    def acquire(self, host) -> None:
        from scripts.run_jobs import free_vram_for_render
        free_vram_for_render(host)

    def release(self, host) -> None:
        from scripts.run_jobs import start_local_vision_judge
        start_local_vision_judge(host)


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


def _vibevoice_execution_device(model: object) -> str:
    """Resolve an accelerator placement, never the first (possibly meta) tensor.

    Accelerate may offload parameters to meta/CPU/disk while dispatching work
    to an accelerator. Prefer its device map, then concrete parameter devices.
    Do not guess a CUDA index or fall back to model.device / CPU.
    """
    def concrete_device(value: object) -> str | None:
        # Accelerate device maps also encode CUDA ordinals as integers.
        if isinstance(value, int) and not isinstance(value, bool):
            return f"cuda:{value}" if value >= 0 else None
        device = str(value)
        if re.fullmatch(r"(?:cuda|xpu|npu|hpu):[0-9]+", device):
            return device
        if device in {"mps", "mps:0"}:
            return device
        return None

    device_map = getattr(model, "hf_device_map", None)
    if isinstance(device_map, Mapping):
        for value in device_map.values():
            device = concrete_device(value)
            if device is not None:
                return device
    parameters = getattr(model, "parameters", None)
    if callable(parameters):
        for parameter in parameters():
            device = concrete_device(getattr(parameter, "device", None))
            if device is not None:
                return device
    raise VibeVoiceError(
        "VibeVoice execution device: no concrete accelerator in "
        "hf_device_map or model parameters (meta/cpu/disk are not executable)")


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
            execution_device = _vibevoice_execution_device(self.model)
            self.set_seed(seed)
            inputs = self.processor.apply_chat_template(
                conversation,
                return_dict=True,
                tokenize=True,
                add_generation_prompt=True,
            ).to(execution_device, self.model.dtype)
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


def _attempt_paths(output: Path, attempt_index: int) -> tuple[Path, Path, Path]:
    raw = output.with_name(f"{output.stem}.attempt-{attempt_index}.wav")
    prepared = raw.with_suffix(".prepared.wav")
    provenance = raw.with_name(raw.name + ".vibevoice.json")
    return raw, prepared, provenance


def _generation_seed(manifest: VibeVoiceManifest, attempt_index: int) -> int:
    return manifest.seed + attempt_index - 1


def _validate_seed_retries(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10:
        raise VibeVoiceError("seed_retries: integer from 0 through 10 required")


def _validate_attempt_namespaces(
        manifest: VibeVoiceManifest, seed_retries: int) -> None:
    paths = []
    for turn in manifest.turns:
        paths.extend((turn.output, _prepared_path(turn.output),
                      _provenance_path(turn.output)))
        for attempt_index in range(1, seed_retries + 2):
            paths.extend(_attempt_paths(turn.output, attempt_index))
    seen = {}
    for path in paths:
        normalized = str(path)
        if normalized in seen:
            raise VibeVoiceError(
                "turn outputs and seed-retry evidence paths must be unique: "
                f"{normalized}")
        seen[normalized] = True


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
    validate_voice_references(manifest, runner=preparation_runner)
    return backend_kind


def validate_voice_references(manifest, *, runner) -> None:
    """Reject short/unreadable references without padding or model loading.

    References must already be clean, isolated speaker recordings selected
    by the operator. Duration probing is not a speaker-isolation classifier.
    """
    for reference in dict.fromkeys(t.voice_reference for t in manifest.turns):
        if not reference.is_file():
            raise VibeVoiceError(f"voice_reference: not readable: {reference}")
        try:
            result = runner(["ffprobe", "-v", "error", "-select_streams", "a:0",
                             "-show_entries", "stream=duration", "-of",
                             "default=nw=1:nk=1", str(reference)])
            duration = float(result.stdout.strip())
            if result.returncode != 0 or not math.isfinite(duration) or duration < 2:
                raise ValueError("short or invalid duration")
            rms = _rms_from_probe(runner([
                "ffmpeg", "-v", "info", "-i", str(reference),
                "-af", "volumedetect", "-f", "null", "-"]))
            if not math.isfinite(rms) or rms < -60:
                raise ValueError("silent reference")
        except Exception as exc:
            raise VibeVoiceError(
                f"voice_reference must contain >=2s of clean audio: {reference}") from exc


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


def _load_or_prepare_turn(
    *,
    manifest: VibeVoiceManifest,
    turn: VibeVoiceTurn,
    backend_kind: str,
    provenance: dict,
    prepared: Path,
    preparation_runner: Callable[[Sequence[str]], object],
) -> tuple[dict, dict]:
    if prepared.is_file():
        provenance = _read_json_object(
            _provenance_path(turn.output), "provenance")
        preparation = provenance.get("preparation")
        if not isinstance(preparation, dict):
            raise VibeVoiceError(
                f"prepared output lacks preparation provenance: {prepared}")
        _validate_provenance(
            manifest, turn, backend_kind, provenance, require_prepared=True)
        return provenance, preparation
    try:
        prepared_audio = prepare_turn_audio(
            str(turn.output), str(prepared), speaker_id=turn.speaker,
            target_duration_s=turn.target_duration_s,
            runner=preparation_runner)
    except AudioPreparationError as exc:
        raise VibeVoiceError(f"audio preparation failed: {exc}") from exc
    preparation = prepared_audio.to_dict()
    provenance.update({
        "preparation": preparation,
        "prepared_sha256": _sha256(prepared),
    })
    _write_json(_provenance_path(turn.output), provenance)
    return provenance, preparation


def _gate_payload(exc: Exception, prepared: Path, turn: VibeVoiceTurn) -> dict:
    evidence = exc.evidence if isinstance(exc, WhisperGateError) else None
    if evidence is None:
        return {
            "phase": "pre",
            "audio_path": str(prepared),
            "intended_text": turn.text,
            "passed": False,
            "error": str(exc),
        }
    return evidence.to_dict()


def _retry_audit_from_provenance(
        provenance: Mapping, manifest: VibeVoiceManifest) -> dict:
    generation_seed = provenance.get("generation_seed", manifest.seed)
    attempt_index = provenance.get("attempt_index", 1)
    attempt_count = provenance.get("attempt_count", attempt_index)
    seed_rejections = provenance.get("seed_rejections", [])
    if (isinstance(generation_seed, bool) or not isinstance(generation_seed, int)
            or isinstance(attempt_index, bool) or not isinstance(attempt_index, int)
            or isinstance(attempt_count, bool) or not isinstance(attempt_count, int)
            or not isinstance(seed_rejections, list)):
        raise VibeVoiceError("provenance retry audit is invalid")
    return {
        "generation_seed": generation_seed,
        "attempt_index": attempt_index,
        "attempt_count": attempt_count,
        "seed_rejections": seed_rejections,
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
    seed_retries: int = 2,
) -> dict:
    """Generate, prepare, and pre-gate each turn through injected seams."""
    _validate_seed_retries(seed_retries)
    backend_kind = _preflight(manifest, backend, transcriber, preparation_runner)
    _validate_attempt_namespaces(manifest, seed_retries)
    report_destination = Path(report_path)
    records = [_pending_record(turn) for turn in manifest.turns]
    resumed_count = 0

    for index, turn in enumerate(manifest.turns):
        record = records[index]
        seed_rejections = []
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

            if turn.output.exists() and resume:
                provenance, preparation = _load_or_prepare_turn(
                    manifest=manifest, turn=turn, backend_kind=backend_kind,
                    provenance=provenance, prepared=prepared,
                    preparation_runner=preparation_runner)
                try:
                    gate = run_whisper_gate(
                        str(prepared), turn.text, transcriber=transcriber,
                        phase="pre", pass_bar=pass_bar)
                except Exception as exc:
                    gate_payload = _gate_payload(exc, prepared, turn)
                    record.update({
                        "status": "pre_gate_failed",
                        "prepared_path": str(prepared),
                        "provenance_path": str(provenance_path),
                        "prepared_sha256": provenance["prepared_sha256"],
                        "preparation": preparation,
                        "whisper_gate": gate_payload,
                    })
                    _write_json(report_destination, _report(
                        manifest, records, status="failed", error=str(exc)))
                    raise VibeVoiceError(str(exc)) from exc
                record.update({
                    "status": "complete",
                    "provenance_path": str(provenance_path),
                    "prepared_path": preparation["output_path"],
                    "prepared_sha256": provenance["prepared_sha256"],
                    "preparation": preparation,
                    "whisper_gate": gate.to_dict(),
                    **_retry_audit_from_provenance(provenance, manifest),
                })
                _write_json(report_destination, _report(
                    manifest, records, status="in_progress",
                    resumed_turn_count=resumed_count))
                continue

            if provenance_path.exists():
                raise VibeVoiceError(
                    f"orphan provenance exists without output: {provenance_path}")
            for attempt_index in range(1, seed_retries + 2):
                preserved_raw, preserved_prepared, preserved_provenance = (
                    _attempt_paths(turn.output, attempt_index))
                if any(path.exists() for path in (
                        preserved_raw, preserved_prepared, preserved_provenance)):
                    raise VibeVoiceError(
                        "existing seed-retry evidence requires a fresh run: "
                        f"{preserved_raw}")
                generation_seed = _generation_seed(manifest, attempt_index)
                turn.output.parent.mkdir(parents=True, exist_ok=True)
                try:
                    backend.generate(turn, turn.output, generation_seed)
                except Exception as exc:
                    record.update({
                        "status": "generation_failed",
                        "generation_seed": generation_seed,
                        "attempt_index": attempt_index,
                        "seed_rejections": seed_rejections,
                    })
                    raise VibeVoiceError(
                        f"generation failed for {turn.output}: {exc}") from exc
                if not turn.output.is_file():
                    raise VibeVoiceError(
                        f"backend did not create output: {turn.output}")
                provenance = _base_provenance(manifest, turn, backend_kind)
                provenance.update({
                    "voice_reference_sha256": _sha256(turn.voice_reference),
                    "output_sha256": _sha256(turn.output),
                    "generation_seed": generation_seed,
                    "attempt_index": attempt_index,
                })
                _write_json(provenance_path, provenance)
                provenance, preparation = _load_or_prepare_turn(
                    manifest=manifest, turn=turn, backend_kind=backend_kind,
                    provenance=provenance, prepared=prepared,
                    preparation_runner=preparation_runner)

                try:
                    gate = run_whisper_gate(
                        str(prepared), turn.text, transcriber=transcriber,
                        phase="pre", pass_bar=pass_bar)
                except Exception as exc:
                    gate_payload = _gate_payload(exc, prepared, turn)
                    rejection = {
                        "attempt_index": attempt_index,
                        "generation_seed": generation_seed,
                        "output_path": str(turn.output),
                        "prepared_path": str(prepared),
                        "provenance_path": str(provenance_path),
                        "prepared_sha256": provenance["prepared_sha256"],
                        "preparation": preparation,
                        "whisper_gate": gate_payload,
                    }
                    record.update({
                        "status": "pre_gate_failed",
                        "prepared_path": str(prepared),
                        "provenance_path": str(provenance_path),
                        "prepared_sha256": provenance["prepared_sha256"],
                        "preparation": preparation,
                        "whisper_gate": gate_payload,
                        "generation_seed": generation_seed,
                        "attempt_index": attempt_index,
                        "seed_rejections": [*seed_rejections, rejection],
                    })
                    _write_json(report_destination, _report(
                        manifest, records, status="failed", error=str(exc)))
                    scored = (isinstance(exc, WhisperGateError)
                              and exc.evidence is not None)
                    if not scored or attempt_index > seed_retries:
                        if scored:
                            provenance.update({
                                "attempt_count": attempt_index,
                                "seed_rejections": [*seed_rejections, rejection],
                            })
                            _write_json(provenance_path, provenance)
                        raise VibeVoiceError(str(exc)) from exc

                    rejection.update({
                        "output_path": str(preserved_raw),
                        "prepared_path": str(preserved_prepared),
                        "provenance_path": str(preserved_provenance),
                        "preparation": dict(preparation,
                            source_path=str(preserved_raw),
                            output_path=str(preserved_prepared)),
                        "whisper_gate": dict(gate_payload,
                            audio_path=str(preserved_prepared)),
                    })
                    provenance.update({
                        "attempt_count": attempt_index,
                        "seed_rejections": [*seed_rejections, rejection],
                        "output": str(preserved_raw),
                        "prepared_path": str(preserved_prepared),
                        "preparation": dict(preparation,
                            source_path=str(preserved_raw),
                            output_path=str(preserved_prepared)),
                    })
                    _write_json(provenance_path, provenance)
                    os.replace(turn.output, preserved_raw)
                    os.replace(prepared, preserved_prepared)
                    os.replace(provenance_path, preserved_provenance)
                    seed_rejections = list(record["seed_rejections"])
                    _write_json(report_destination, _report(
                        manifest, records, status="failed", error=str(exc)))
                    record.clear()
                    record.update(_pending_record(turn))
                    continue

                if attempt_index > 1:
                    provenance.update({
                        "attempt_count": attempt_index,
                        "seed_rejections": seed_rejections,
                    })
                    _write_json(provenance_path, provenance)
                record.update({
                    "status": "complete",
                    "provenance_path": str(provenance_path),
                    "prepared_path": preparation["output_path"],
                    "prepared_sha256": provenance["prepared_sha256"],
                    "preparation": preparation,
                    "whisper_gate": gate.to_dict(),
                    "generation_seed": generation_seed,
                    "attempt_index": attempt_index,
                    "seed_rejections": seed_rejections,
                })
                _write_json(report_destination, _report(
                    manifest, records, status="in_progress",
                    resumed_turn_count=resumed_count))
                break
        except Exception as exc:
            if record.get("status") == "pre_gate_failed":
                raise
            error = str(exc) or exc.__class__.__name__
            if record.get("status") == "pending":
                record["status"] = "generation_failed"
                if seed_rejections:
                    record["seed_rejections"] = seed_rejections
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


def supply_vibevoice_turns_remote(
    manifest: VibeVoiceManifest, *, host, host_python: str, host_repo: str,
    host_model: str, report_path: str | Path, preparation_runner,
    timeout: float = 1800, pass_bar: float = 0.5,
    whisper_model: str = "small",
    seed_retries: int = 2,
    gpu_lease=None, manage_gpu: bool = True,
) -> dict:
    """Stage, execute the repo module, and verify a fresh host supply run.

    The configured asset map must cover the manifest directory. Host model,
    Python and repository paths are explicit host-namespace inputs; a local
    model installation is not required. Never reuses host or local outputs.
    By default stop the repo-managed judge around remote execution and restore
    it before fetching/publishing artifacts. Inject acquire/release(host) for
    tests; manage_gpu=False is only for an externally managed dedicated GPU.
    """
    validate_voice_references(manifest, runner=preparation_runner)
    _validate_seed_retries(seed_retries)
    _validate_attempt_namespaces(manifest, seed_retries)
    if not math.isfinite(timeout) or timeout <= 0:
        raise VibeVoiceError("remote timeout must be finite and positive")
    if not math.isfinite(pass_bar) or not 0 <= pass_bar <= 1:
        raise VibeVoiceError("pass_bar must be between 0 and 1")
    required = ("map_asset", "makedirs", "push_asset", "write_text",
                "run_argv", "fetch_file")
    if not all(callable(getattr(host, method, None)) for method in required):
        raise VibeVoiceError("host: remote supply requires RenderHost asset/argv seams")
    if not all(isinstance(p, str) and Path(p).is_absolute()
               for p in (host_python, host_repo, host_model)):
        raise VibeVoiceError("host Python/repo/model must be absolute paths")
    lease = (gpu_lease if gpu_lease is not None else VibeVoiceJudgeLease()) if manage_gpu else None
    if lease is not None and not all(
            callable(getattr(lease, method, None)) for method in ("acquire", "release")):
        raise VibeVoiceError("gpu_lease: acquire/release(host) are required")
    destination = Path(report_path).resolve()
    remote_evidence = destination.with_name(destination.name + ".remote.json")
    outputs = [p for t in manifest.turns
               for p in (t.output, _prepared_path(t.output), _provenance_path(t.output))]
    outputs.extend(path for t in manifest.turns
                   for attempt in range(1, seed_retries + 2)
                   for path in _attempt_paths(t.output, attempt))
    if any(p.exists() for p in [destination, remote_evidence, *outputs]):
        raise VibeVoiceError("remote supply requires new local output/report paths")
    run_root = manifest.source_path.parent / (".vibevoice-" + uuid.uuid4().hex)
    host_root = host.map_asset(str(run_root))
    if not isinstance(host_root, str) or not Path(host_root).is_absolute():
        raise VibeVoiceError("host.map_asset must return an absolute run directory")
    host.makedirs(host_root)
    remote_turns = []
    for turn in manifest.turns:
        remote_ref = host.map_asset(str(turn.voice_reference))
        host.makedirs(str(Path(remote_ref).parent))
        if host.push_asset(str(turn.voice_reference)) != remote_ref:
            raise VibeVoiceError("host reference staging path mismatch")
        remote_turns.append(VibeVoiceTurn(
            turn.turn_index, turn.speaker, turn.text, Path(remote_ref),
            Path(host_root) / f"turn-{turn.turn_index}.wav", turn.target_duration_s))
    remote_manifest_path = Path(host_root) / "manifest.json"
    remote_report_path = Path(host_root) / "report.json"
    remote_manifest = VibeVoiceManifest(
        manifest.schema, Path(host_model), manifest.model_sha256, manifest.seed,
        tuple(remote_turns), remote_manifest_path)
    payload = remote_manifest.to_dict()
    for turn in payload["turns"]:
        turn["output"] = Path(turn["output"]).name
    if host.write_text(str(remote_manifest_path), json.dumps(payload)) != str(remote_manifest_path):
        raise VibeVoiceError("host manifest staging path mismatch")
    command = [
        host_python, "-m", "predict.vibevoice", str(remote_manifest_path),
        "--report", str(remote_report_path), "--pass-bar", str(pass_bar),
        "--seed-retries", str(seed_retries),
        "--whisper-model", whisper_model, "--whisper-output-dir",
        str(Path(host_root) / "whisper"),
    ]
    try:
        if lease is not None:
            try:
                if lease.acquire(host) is False:
                    raise RuntimeError("acquire returned False")
            except Exception as exc:
                raise VibeVoiceError(f"GPU lease acquire failed: {exc}") from exc
        result = host.run_argv(command, cwd=host_repo, timeout=timeout)
    finally:
        # Acquisition can stop the judge and then fail: restore even then.
        # A failed restore prevents any successful report/artifact publication.
        if lease is not None:
            try:
                if lease.release(host) is False:
                    raise RuntimeError("release returned False")
            except Exception as exc:
                raise VibeVoiceError(f"GPU lease release failed: {exc}") from exc
    rejected = getattr(result, "returncode", None) != 0
    rejected_root = destination.parent / "rejected" / Path(host_root).name

    destination.parent.mkdir(parents=True, exist_ok=True)
    # Fetch to an empty private directory: a missing transfer can never be
    # satisfied by stale local evidence. Publish only after ALL turns validate.
    with tempfile.TemporaryDirectory(prefix="vibevoice-pull-", dir=destination.parent) as tmp:
        scratch = Path(tmp)
        def fetch(remote, local):
            try:
                host.fetch_file(str(remote), str(local))
            except Exception as exc:
                raise VibeVoiceError(f"missing host artifact: {remote}") from exc
            if not local.is_file() or local.stat().st_size == 0:
                raise VibeVoiceError(f"missing host artifact: {remote}")
        report_file = scratch / "report.json"
        fetch(remote_report_path, report_file)
        report = _read_json_object(report_file, "host report")
        expected = _report(remote_manifest, [], status="failed" if rejected else "complete")
        for field in ("schema", "manifest", "model_sha256", "seed", "status"):
            if report.get(field) != expected[field]:
                raise VibeVoiceError(f"host report {field} mismatch")
        records = report.get("turns")
        if not isinstance(records, list) or len(records) != len(manifest.turns):
            raise VibeVoiceError("host report turn count mismatch")
        statuses = [r.get("status") if isinstance(r, dict) else None for r in records]
        completed_count = statuses.count("complete")
        if rejected:
            terminal = records[completed_count] if completed_count < len(records) else {}
            terminal_status = terminal.get("status")
            prior_rejections = terminal.get("seed_rejections")
            terminal_ok = (
                terminal_status == "pre_gate_failed"
                or (terminal_status == "generation_failed"
                    and isinstance(prior_rejections, list) and prior_rejections))
            if not terminal_ok:
                raise VibeVoiceError(
                    "host failed run must end with scored gate or retry evidence")
            wanted_statuses = (
                ["complete"] * completed_count + [terminal_status]
                + ["pending"] * (len(records) - completed_count - 1))
        else:
            wanted_statuses = ["complete"] * len(records)
        if statuses != wanted_statuses or report.get("completed_turn_count") != completed_count:
            raise VibeVoiceError("host report turn status/count mismatch")
        staged = []
        local_records = []
        for local_turn, remote_turn, record in zip(manifest.turns, remote_turns, records):
            if rejected:
                local_turn = VibeVoiceTurn(
                    local_turn.turn_index, local_turn.speaker, local_turn.text,
                    local_turn.voice_reference, rejected_root / remote_turn.output.name,
                    local_turn.target_duration_s)
            if record.get("status") == "pending":
                if record != _pending_record(remote_turn):
                    raise VibeVoiceError("host pending turn mismatch")
                local_records.append(_pending_record(local_turn))
                continue
            if not isinstance(record, dict):
                raise VibeVoiceError("invalid host turn record")
            gate_passed = record["status"] == "complete"
            generation_failed = record["status"] == "generation_failed"
            expected_fields = {**_pending_record(remote_turn), "status": record["status"]}
            if not generation_failed:
                expected_fields.update({
                    "prepared_path": str(_prepared_path(remote_turn.output)),
                    "provenance_path": str(_provenance_path(remote_turn.output)),
                })
            for field, wanted in expected_fields.items():
                if record.get(field) != wanted:
                    raise VibeVoiceError(f"host turn {field} mismatch")
            gate = record.get("whisper_gate")
            if generation_failed:
                if gate is not None:
                    raise VibeVoiceError("host generation failure must not invent gate evidence")
            elif (not isinstance(gate, dict) or gate.get("passed") is not gate_passed
                    or gate.get("phase") != "pre" or gate.get("intended_text") != local_turn.text
                    or gate.get("audio_path") != str(_prepared_path(remote_turn.output))):
                raise VibeVoiceError("host turn pre-gate missing or invalid")
            if not generation_failed:
                try:
                    checked_gate = run_whisper_gate(
                        gate["audio_path"], local_turn.text,
                        transcriber=lambda _: gate.get("transcript"), phase="pre",
                        pass_bar=pass_bar).to_dict()
                except WhisperGateError as exc:
                    if gate_passed or exc.evidence is None:
                        raise VibeVoiceError(
                            "host turn transcript evidence invalid") from exc
                    checked_gate = exc.evidence.to_dict()
                except Exception as exc:
                    raise VibeVoiceError("host turn transcript evidence invalid") from exc
                if gate != checked_gate:
                    raise VibeVoiceError("host turn gate evidence mismatch")
            raw_rejections = record.get("seed_rejections")
            if not isinstance(raw_rejections, list):
                raise VibeVoiceError("host turn seed rejection evidence missing")
            if generation_failed and not raw_rejections:
                raise VibeVoiceError("host generation failure lacks prior retry evidence")
            pre_gate_failed = record["status"] == "pre_gate_failed"
            final_attempt_index = (
                len(raw_rejections) if pre_gate_failed else len(raw_rejections) + 1)
            if record.get("attempt_index") != final_attempt_index:
                raise VibeVoiceError("host turn attempt index mismatch")
            if record.get("generation_seed") != _generation_seed(
                    remote_manifest, final_attempt_index):
                raise VibeVoiceError("host turn generation seed mismatch")
            localized_rejections = []
            for rejection_index, rejection in enumerate(raw_rejections, start=1):
                if not isinstance(rejection, dict):
                    raise VibeVoiceError("host seed rejection evidence invalid")
                final_failed_rejection = (
                    pre_gate_failed and rejection_index == len(raw_rejections))
                if final_failed_rejection:
                    remote_attempt_raw = remote_turn.output
                    remote_attempt_prepared = _prepared_path(remote_turn.output)
                    remote_attempt_provenance = _provenance_path(remote_turn.output)
                else:
                    (remote_attempt_raw, remote_attempt_prepared,
                     remote_attempt_provenance) = _attempt_paths(
                        remote_turn.output, rejection_index)
                expected_seed = _generation_seed(remote_manifest, rejection_index)
                if (rejection.get("attempt_index") != rejection_index
                        or rejection.get("generation_seed") != expected_seed
                        or rejection.get("output_path") != str(remote_attempt_raw)
                        or rejection.get("prepared_path") != str(remote_attempt_prepared)
                        or rejection.get("provenance_path") != str(
                            remote_attempt_provenance)):
                    raise VibeVoiceError("host seed rejection path or seed mismatch")
                rejection_gate = rejection.get("whisper_gate")
                if (not isinstance(rejection_gate, dict)
                        or rejection_gate.get("passed") is not False
                        or rejection_gate.get("phase") != "pre"
                        or rejection_gate.get("intended_text") != local_turn.text
                        or rejection_gate.get("audio_path") != str(
                            remote_attempt_prepared)):
                    raise VibeVoiceError("host seed rejection gate invalid")
                if final_failed_rejection and rejection_gate != gate:
                    raise VibeVoiceError("host final rejection gate mismatch")

                if final_failed_rejection:
                    local_attempt_raw = local_turn.output
                    local_attempt_prepared = _prepared_path(local_turn.output)
                    local_attempt_provenance = _provenance_path(local_turn.output)
                else:
                    local_attempt_raw, local_attempt_prepared, local_attempt_provenance = (
                        _attempt_paths(local_turn.output, rejection_index))
                localized_preparation = rejection.get("preparation")
                if not isinstance(localized_preparation, dict):
                    raise VibeVoiceError("host seed rejection preparation missing")
                localized_preparation = dict(localized_preparation,
                    source_path=str(local_attempt_raw),
                    output_path=str(local_attempt_prepared))
                localized_rejections.append(dict(rejection,
                    output_path=str(local_attempt_raw),
                    prepared_path=str(local_attempt_prepared),
                    provenance_path=str(local_attempt_provenance),
                    preparation=localized_preparation,
                    whisper_gate=dict(rejection_gate, audio_path=str(
                        local_attempt_prepared))))

                if final_failed_rejection:
                    continue
                attempt_raw = scratch / f"{local_turn.turn_index}.attempt-{rejection_index}.wav"
                attempt_prepared = _prepared_path(attempt_raw)
                attempt_provenance = _provenance_path(attempt_raw)
                fetch(remote_attempt_raw, attempt_raw)
                fetch(remote_attempt_prepared, attempt_prepared)
                fetch(remote_attempt_provenance, attempt_provenance)
                if rejected:
                    original_attempt_provenance = scratch / (
                        f"{local_turn.turn_index}.attempt-{rejection_index}.remote.json")
                    original_attempt_provenance.write_bytes(
                        attempt_provenance.read_bytes())
                    staged.append((original_attempt_provenance, rejected_root / (
                        remote_attempt_raw.name + ".provenance.remote.json")))
                attempt_provenance_data = _read_json_object(
                    attempt_provenance, "host attempt provenance")
                attempt_base = _base_provenance(
                    remote_manifest, remote_turn, VibeVoiceBackend.backend_kind)
                attempt_base.update({
                    "output": str(remote_attempt_raw),
                    "prepared_path": str(remote_attempt_prepared),
                })
                for field, wanted in attempt_base.items():
                    if attempt_provenance_data.get(field) != wanted:
                        raise VibeVoiceError(
                            f"host attempt provenance {field} mismatch")
                if (attempt_provenance_data.get("generation_seed") != expected_seed
                        or attempt_provenance_data.get("attempt_index") != rejection_index):
                    raise VibeVoiceError("host attempt seed provenance mismatch")
                for field, path in (
                        ("voice_reference_sha256", local_turn.voice_reference),
                        ("output_sha256", attempt_raw),
                        ("prepared_sha256", attempt_prepared)):
                    if attempt_provenance_data.get(field) != _sha256(path):
                        raise VibeVoiceError("host attempt provenance hash mismatch")
                attempt_preparation = attempt_provenance_data.get("preparation")
                if (not isinstance(attempt_preparation, dict)
                        or rejection.get("preparation") != attempt_preparation):
                    raise VibeVoiceError("host attempt preparation mismatch")
                attempt_provenance_data["preparation"] = localized_preparation
                attempt_provenance_data.update(_base_provenance(
                    manifest, local_turn, VibeVoiceBackend.backend_kind))
                attempt_provenance_data["output"] = str(local_attempt_raw)
                attempt_provenance_data["prepared_path"] = str(local_attempt_prepared)
                attempt_provenance_data["seed_rejections"] = localized_rejections[:-1]
                _write_json(attempt_provenance, attempt_provenance_data)
                staged.extend((
                    (attempt_raw, local_attempt_raw),
                    (attempt_prepared, local_attempt_prepared),
                    (attempt_provenance, local_attempt_provenance)))
            if generation_failed:
                local_records.append(dict(record,
                    output_path=str(local_turn.output),
                    seed_rejections=localized_rejections))
                continue
            raw = scratch / f"{local_turn.turn_index}.wav"
            prepared = _prepared_path(raw)
            provenance_file = _provenance_path(raw)
            fetch(remote_turn.output, raw)
            fetch(_prepared_path(remote_turn.output), prepared)
            fetch(_provenance_path(remote_turn.output), provenance_file)
            provenance = _read_json_object(provenance_file, "host provenance")
            for field, wanted in _base_provenance(
                    remote_manifest, remote_turn, VibeVoiceBackend.backend_kind).items():
                if provenance.get(field) != wanted:
                    raise VibeVoiceError(f"host provenance {field} mismatch")
            for field, path in (("voice_reference_sha256", local_turn.voice_reference),
                                ("output_sha256", raw), ("prepared_sha256", prepared)):
                if provenance.get(field) != _sha256(path):
                    raise VibeVoiceError(f"host provenance {field} mismatch")
            if record.get("prepared_sha256") != provenance["prepared_sha256"]:
                raise VibeVoiceError("host report prepared hash mismatch")
            preparation = provenance.get("preparation")
            if (not isinstance(preparation, dict) or record.get("preparation") != preparation
                    or preparation.get("source_path") != str(remote_turn.output)
                    or preparation.get("output_path") != str(_prepared_path(remote_turn.output))
                    or preparation.get("speaker_id") != local_turn.speaker
                    or preparation.get("target_duration_s") != local_turn.target_duration_s):
                raise VibeVoiceError("host preparation provenance mismatch")
            try:
                PreparedTurnAudio(**preparation)
                for field in ("target_duration_s", "measured_duration_s", "boost_db", "rms_db"):
                    if not math.isfinite(float(preparation[field])):
                        raise ValueError("non-finite preparation evidence")
            except (TypeError, ValueError) as exc:
                raise VibeVoiceError("host preparation evidence invalid") from exc
            preparation = dict(preparation, source_path=str(local_turn.output),
                               output_path=str(_prepared_path(local_turn.output)))
            if rejected:
                original_provenance = scratch / f"{local_turn.turn_index}.remote.json"
                original_provenance.write_bytes(provenance_file.read_bytes())
                staged.append((original_provenance, rejected_root /
                               (remote_turn.output.name + ".provenance.remote.json")))
            provenance.update(_base_provenance(manifest, local_turn, VibeVoiceBackend.backend_kind))
            provenance["preparation"] = preparation
            provenance["seed_rejections"] = localized_rejections
            provenance["remote_execution"] = {
                "model": host_model, "repo": host_repo, "python": host_python,
                "manifest": str(remote_manifest_path),
            }
            _write_json(provenance_file, provenance)
            local_records.append(dict(record, output_path=str(local_turn.output),
                prepared_path=str(_prepared_path(local_turn.output)),
                provenance_path=str(_provenance_path(local_turn.output)), preparation=preparation,
                whisper_gate=dict(gate, audio_path=str(_prepared_path(local_turn.output))),
                seed_rejections=localized_rejections))
            staged.extend(((raw, local_turn.output), (prepared, _prepared_path(local_turn.output)),
                           (provenance_file, _provenance_path(local_turn.output))))
        if rejected:
            # Only a fully validated bundle is retained. Never use canonical
            # output/report paths, even for the passing prefix of a failed run.
            bundle = scratch / "rejected-bundle"
            bundle.mkdir()
            for source, target in staged:
                os.replace(source, bundle / target.name)
            os.replace(report_file, bundle / "report.remote.json")
            audit = _report(manifest, local_records, status="failed",
                            error=report.get("error"))
            audit["remote_report_path"] = str(rejected_root / "report.remote.json")
            audit["host_returncode"] = getattr(result, "returncode", None)
            _write_json(bundle / "report.json", audit)
            rejected_root.parent.mkdir(parents=True, exist_ok=True)
            os.rename(bundle, rejected_root)
            raise VibeVoiceError(
                f"host VibeVoice execution failed; rejected evidence: {rejected_root}")
        for source, target in staged:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, target)
        os.replace(report_file, remote_evidence)
        localized = _report(manifest, local_records, status="complete")
        localized["remote_report_path"] = str(remote_evidence)
        _write_json(destination, localized)
        return localized


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
    host=None,
    gpu_lease=None,
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
    parser.add_argument("--remote-target", help="RenderHost SSH target")
    parser.add_argument("--host-python", help="absolute host Python executable")
    parser.add_argument("--host-repo", help="absolute host repository checkout")
    parser.add_argument("--host-model", help="absolute host VibeVoice model directory")
    parser.add_argument("--remote-timeout", type=float, default=1800)
    parser.add_argument(
        "--remote-gpu-lease", choices=("judge", "none"), default="judge",
        help="remote GPU policy: timeshare repo judge (default), or none for an externally managed GPU",
    )
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
        "--seed-retries",
        type=int,
        default=2,
        help="scored pre-gate seed retries; each retry bumps the seed by one",
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
    _validate_seed_retries(args.seed_retries)
    manifest = load_vibevoice_manifest(args.manifest)
    report_path = (
        Path(args.report)
        if args.report
        else manifest.source_path.parent / "vibevoice-report.json"
    )

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

    validate_voice_references(manifest, runner=preparation_runner)
    if args.remote_target or host is not None:
        if args.resume:
            raise VibeVoiceError("remote supply uses fresh runs; --resume is local only")
        if not all((args.host_python, args.host_repo, args.host_model)):
            raise VibeVoiceError("remote supply requires --host-python/--host-repo/--host-model")
        if host is None:
            from host.render_host import SshHost
            host = SshHost(target=args.remote_target, wgp_root=args.host_repo,
                           pull_root=str(manifest.source_path.parent))
        report = supply_vibevoice_turns_remote(
            manifest, host=host, host_python=args.host_python,
            host_repo=args.host_repo, host_model=args.host_model,
            report_path=report_path, preparation_runner=preparation_runner,
            timeout=args.remote_timeout, pass_bar=args.pass_bar,
            whisper_model=args.whisper_model, gpu_lease=gpu_lease,
            seed_retries=args.seed_retries,
            manage_gpu=args.remote_gpu_lease == "judge")
        print(json.dumps(report, sort_keys=True))
        return 0
    if any((args.host_python, args.host_repo, args.host_model)):
        raise VibeVoiceError("host options require --remote-target")
    backend = (backend_factory or VibeVoiceBackend)(manifest.model)

    report = supply_vibevoice_turns(
        manifest,
        backend=backend,
        transcriber=transcriber,
        preparation_runner=preparation_runner,
        report_path=report_path,
        resume=args.resume,
        pass_bar=args.pass_bar,
        seed_retries=args.seed_retries,
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "MANIFEST_SCHEMA",
    "PROVENANCE_SCHEMA",
    "VibeVoiceError",
    "VibeVoiceJudgeLease",
    "VibeVoiceBackend",
    "VibeVoiceManifest",
    "VibeVoiceTurn",
    "main",
    "load_vibevoice_manifest",
    "publish_vibevoice_turns",
    "supply_vibevoice_turns",
    "supply_vibevoice_turns_remote",
    "validate_voice_references",
]
