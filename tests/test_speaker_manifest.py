import json
import pathlib

import pytest

from predict.speaker_manifest import (
    SCHEMA, SpeakerManifest, SpeakerManifestError, SpeakerTurn,
    build_speaker_manifest, readback_validate_speaker_manifest,
    write_speaker_manifest,
)


def _turn(index=1, speaker="S1"):
    return SpeakerTurn(index, speaker, 1, f"audio/cut{index}.wav", "A line")


def test_manifest_is_versioned_and_maps_turns():
    payload = build_speaker_manifest([_turn()])
    assert payload["schema"] == SCHEMA
    assert payload["turns"][0]["speaker_id"] == "S1"
    assert payload["turns"][0]["picture_n"] == 1
    assert SpeakerManifest.from_dict(payload).to_dict() == payload


def test_manifest_rejects_noncontiguous_turns_or_bad_speaker():
    with pytest.raises(SpeakerManifestError, match="contiguous"):
        build_speaker_manifest([_turn(2)])
    with pytest.raises(SpeakerManifestError, match="SN tag"):
        build_speaker_manifest([_turn(speaker="Ada")])


def test_manifest_writes_and_readback_validates(tmp_path):
    payload = build_speaker_manifest([_turn()])
    output = pathlib.Path(tmp_path) / "render" / "cut.mp4"
    output.parent.mkdir()
    output.write_bytes(b"mp4")
    path = write_speaker_manifest(payload, output)
    assert path.name == "speaker_manifest.json"
    loaded = json.loads(path.read_text())
    assert readback_validate_speaker_manifest(loaded, payload)
    loaded["turns"][0]["speaker_id"] = "S2"
    with pytest.raises(SpeakerManifestError, match="mismatch"):
        readback_validate_speaker_manifest(loaded, payload)
