"""No-proper-nouns gate (ADOPT of shuohao-skills no-names doctrine,
WD-4k56/qbcj extraction -> promotion story).

Doctrine: image/render prompts must never contain proper nouns the
model might "know" (character names, aliases, real people, IP). Models
bias toward their memorized version of named entities. Detection is
deterministic registry matching — NO LLM, NO network.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from gates.no_names_gate import (  # noqa: E402
    NameViolation, check_no_proper_nouns, load_registry)

# lighthouse / kaiju / heron are common nouns in our banked intents —
# NOT entities. Entities = named characters/places/IP from bibles.
REG = {
    "version": 1,
    "entities": [
        {"id": "char-mira", "type": "character", "name": "Mira",
         "aliases": ["Mira Chen", "the Ferry Girl"]},
        {"id": "ip-godzilla", "type": "ip", "name": "Godzilla",
         "aliases": ["Gojira"]},
        {"id": "place-vermilion-bay", "type": "place",
         "name": "Vermilion Bay", "aliases": []},
    ],
}


def reg():
    return load_registry_dict(REG)


def load_registry_dict(d: dict):
    """load_registry from a dict via a temp-free shim: it accepts a
    path; we exercise the dict path through check_no_proper_nouns
    which also accepts pre-loaded registries."""
    return d


# ── 1: registry matching semantics ─────────────────────────────────

def test_exact_match_hits():
    v = check_no_proper_nouns("Mira walks to the shore", reg())
    assert len(v) == 1 and v[0].matched_name == "Mira"
    assert isinstance(v[0], NameViolation)
    assert v[0].entity_id == "char-mira"


def test_case_insensitive():
    v = check_no_proper_nouns("mira at the harbor, MIRA in close-up", reg())
    assert len(v) == 2
    assert all(x.matched_name.lower() == "mira" for x in v)


def test_alias_hits():
    v = check_no_proper_nouns("Gojira rises from the bay", reg())
    assert len(v) == 1 and v[0].matched_name == "Gojira"
    assert v[0].canonical_name == "Godzilla"


def test_multiword_name_exact_phrase():
    v = check_no_proper_nouns("Vermilion Bay at dawn", reg())
    assert len(v) == 1 and v[0].canonical_name == "Vermilion Bay"


def test_word_boundary_semantics():
    """Boundary rule (explicit in docs/entity-registry.md): a match
    must sit on \\b word boundaries. 'Kaiju' registered as a name hits
    'Kaiju rising' and 'the Kaiju' — both are whole-word uses — but
    NOT 'kaijur' (trailing alnum) or 'kaijux'."""
    r = {"version": 1, "entities": [
        {"id": "x", "type": "character", "name": "Kaiju",
         "aliases": []}]}
    assert len(check_no_proper_nouns("Kaiju rising", r)) == 1
    assert len(check_no_proper_nouns("the Kaiju stirs", r)) == 1
    assert check_no_proper_nouns("kaijur rising", r) == []
    assert check_no_proper_nouns("a kaijux appears", r) == []


def test_boundary_no_false_substring():
    # 'Mira' must not fire inside 'Miramar' or 'admiral'
    assert check_no_proper_nouns("Miramar airfield at dusk", reg()) == []
    assert check_no_proper_nouns("an admiral's coat", reg()) == []


def test_punctuation_boundary_counts():
    v = check_no_proper_nouns("approaching: Mira!", reg())
    assert len(v) == 1


def test_case_insensitive_no_pseudo_overlap():
    # exact case-insensitive but still boundary-anchored: 'godzilla'
    assert len(check_no_proper_nouns("a godzilla-shaped shadow", reg())) == 1
    assert check_no_proper_nouns("godzillaverse merch", reg()) == []


# ── 2: false-positive cases ────────────────────────────────────────

def test_common_words_not_in_registry_pass():
    text = ("a weathered stone lighthouse on a jagged black headland; "
            "a colossal kaiju silhouette; a grey-blue heron; Kodak "
            "Vision3 500T stock character; PS2-era low-poly geometry")
    assert check_no_proper_nouns(text, reg()) == []


def test_empty_registry_passes_everything():
    assert check_no_proper_nouns("Godzilla and Mira", {
        "version": 1, "entities": []}) == []


def test_empty_text():
    assert check_no_proper_nouns("", reg()) == []


# ── 3: load_registry from file ─────────────────────────────────────

def test_load_registry_file(tmp_path):
    p = tmp_path / "reg.json"
    p.write_text(json.dumps(REG))
    r = load_registry(str(p))
    v = check_no_proper_nouns("Mira", r)
    assert len(v) == 1


def test_load_registry_rejects_bad_schema(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"nope": True}))
    with pytest.raises(ValueError):
        load_registry(str(p))


def test_load_registry_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_registry(str(tmp_path / "absent.json"))


# ── 4: seed registry ships and is valid ────────────────────────────

def test_seed_registry_loads():
    r = load_registry(REPO / "datasets" / "entity-registry.json")
    assert r["entities"], "seed registry must not be empty"


# ── 5: integration — brief validator rejects registry names ────────

def test_brief_with_registered_name_fails_typed():
    from predict.prompt_director import RenderBrief
    with pytest.raises(ValueError, match="proper noun"):
        RenderBrief(
            subject="Mira stands on the dock at Vermilion Bay",
            motion="she turns slowly", camera="locked-off wide",
            style="expired 500T tungsten stock",
            registry=load_registry_dict(REG))


def test_brief_name_in_craft_field_fails():
    from predict.prompt_director import RenderBrief
    with pytest.raises(ValueError, match="proper noun"):
        RenderBrief(
            subject="a lone figure", motion="walking", camera="wide",
            style="faded 16mm print",
            identity_lock="wardrobe must match Mira Chen",
            registry=load_registry_dict(REG))


def test_brief_clean_passes_with_registry():
    from predict.prompt_director import RenderBrief
    b = RenderBrief(subject="a colossal kaiju silhouette in fog",
                    motion="rising slowly", camera="low-angle wide",
                    style="anamorphic 35mm", registry=load_registry_dict(REG))
    assert b.subject.startswith("a colossal kaiju")


def test_brief_without_registry_skips_loudly(caplog):
    """Doctrine (CHANGELOG novel-art 1.0.0): missing --cast skips
    LOUDLY, never silently."""
    from predict.prompt_director import RenderBrief
    import logging
    with caplog.at_level(logging.WARNING):
        RenderBrief(subject="Godzilla rises", motion="rising",
                    camera="wide", style="16mm", registry=None)
    assert any("no-names" in r.message.lower() or
               "registry" in r.message.lower() for r in caplog.records)


# ── 6: CLI smoke ───────────────────────────────────────────────────

def _run_cli(*args):
    return subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_names.py"), *args],
        capture_output=True, text=True)


def test_cli_clean_text_exit0(tmp_path):
    rp = tmp_path / "r.json"
    rp.write_text(json.dumps(REG))
    out = _run_cli("a kaiju silhouette in fog", "--registry", str(rp))
    assert out.returncode == 0, out.stderr
    assert "OK" in out.stdout


def test_cli_violation_exit1(tmp_path):
    rp = tmp_path / "r.json"
    rp.write_text(json.dumps(REG))
    out = _run_cli("Mira at the bay", "--registry", str(rp))
    assert out.returncode == 1
    assert "Mira" in out.stdout


def test_cli_file_input(tmp_path):
    rp = tmp_path / "r.json"
    rp.write_text(json.dumps(REG))
    fp = tmp_path / "prompt.txt"
    fp.write_text("Gojira emerges\n")
    out = _run_cli(str(fp), "--registry", str(rp))
    assert out.returncode == 1
    assert "Gojira" in out.stdout
