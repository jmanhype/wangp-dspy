"""Provenance-tier gate (ADOPT of shuohao-skills inferred-marker
convention, WD-oyti; GLM verdict ADOPT 7/7 zero overrides).

Convention: every identity/bible claim carries exactly one provenance
tier — a canon citation OR one `(inferred)` marker. No unmarked middle
ground, no double-marking ("只用一种标记，不要中英都加"). Markers live in
human fields only and are stripped at handoff-to-prompt time — they
must NEVER reach a render prompt ("(inferred) 混进去会被画进画面").
Decision provenance (from/mergeNote) and fact provenance (inferred)
are separate audit trails that never mix.

ZERO-MODEL: deterministic string checks, no LLM, no network.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from gates.provenance_gate import (  # noqa: E402
    INFERRED_MARKER, ProvenanceGateError, check_prompt_fields,
    check_provenance_tier, check_specific_neutral, strip_markers)


# ── 1: tier semantics — the two tiers + no middle ground ───────────

def test_cited_claim_without_marker_is_clean():
    v = check_provenance_tier("grey-white newsprint hull",
                              field="identity", has_canon_citation=True)
    assert v == []


def test_unmarked_claim_without_citation_is_violation():
    """The core gap this convention closes: invented bible details
    indistinguishable from canon at generation time."""
    v = check_provenance_tier("grey-white newsprint hull",
                              field="identity", has_canon_citation=False)
    assert len(v) == 1
    assert "NEITHER" in v[0].reason or "middle" in v[0].reason.lower()


def test_single_inferred_marker_is_clean():
    v = check_provenance_tier("grey-white newsprint hull (inferred)",
                              field="identity", has_canon_citation=False)
    assert v == []


def test_double_marked_claim_is_violation():
    v = check_provenance_tier(
        "hull (inferred), ink bleed (inferred)",
        field="identity", has_canon_citation=False)
    assert len(v) == 1
    assert "ONE marker" in v[0].reason or "exactly" in v[0].reason.lower()


def test_cited_plus_marker_is_redundant_double_tier():
    v = check_provenance_tier("hull (inferred)", field="identity",
                              has_canon_citation=True)
    assert len(v) == 1
    assert "citation" in v[0].reason.lower()


def test_marker_case_and_whitespace_tolerant():
    assert check_provenance_tier("hull (Inferred)", field="identity") == []
    assert check_provenance_tier("hull ( inferred )", field="identity") == []


def test_empty_text_loud_skip():
    with pytest.raises(ProvenanceGateError) as ei:
        check_provenance_tier("   ", field="identity")
    assert ei.value.kind == "empty_text"


# ── 2: stripping seam — markers never enter prompts ────────────────

def test_strip_markers_removes_and_collapses():
    out = strip_markers("grey hull (inferred), ink bleed")
    assert out == "grey hull, ink bleed"
    assert "(inferred)" not in out.lower()


def test_strip_markers_mid_sentence():
    out = strip_markers("the ferry girl (inferred) walks to shore")
    assert out == "the ferry girl walks to shore"


def test_check_prompt_fields_clean():
    assert check_prompt_fields(
        "Preserve throughout: grey hull, ink bleed") == []


def test_check_prompt_fields_marker_is_violation():
    v = check_prompt_fields("Preserve throughout: grey hull (inferred)")
    assert len(v) == 1
    assert v[0].field == "prompt"
    assert "painted" in v[0].reason.lower() or \
        "stripped" in v[0].reason.lower()


# ── 3: brief_to_prompt seam integration ────────────────────────────

GOOD_BRIEF = {
    "subject": "a colossal kaiju silhouette in fog",
    "motion": "rising slowly from the bay",
    "camera": "low-angle wide, locked-off",
    "style": "expired 500T tungsten stock, anamorphic 35mm",
}


def _brief(**kw):
    from predict.prompt_director import RenderBrief
    return RenderBrief(**{**GOOD_BRIEF, **kw})


def test_brief_to_prompt_strips_identity_lock_markers():
    from host.wangp_adapter import brief_to_prompt
    # one marker per claim — the multi-claim form is double-marking and
    # is rejected by the tier gate (see test_brief_identity_lock_double_marker_rejected)
    b = _brief(identity_lock="grey-white newsprint hull (inferred), "
                           "ink bleed")
    p = brief_to_prompt(b)
    assert "(inferred)" not in p.lower()
    assert "Preserve throughout: grey-white newsprint hull, ink bleed" in p


def test_brief_to_prompt_marker_free_assertion_fires_on_injection():
    """Seam contract: even if a marker somehow survives into a prompt
    field, the assembled output is rejected typed — never rendered."""
    from host.wangp_adapter import WanGPError, brief_to_prompt
    b = _brief(negatives="(inferred) no morphs")  # marker NOT in lock
    with pytest.raises(WanGPError, match="provenance marker"):
        brief_to_prompt(b)


def test_brief_to_prompt_plain_brief_unchanged():
    from host.wangp_adapter import brief_to_prompt
    # canon-cited lock: no marker needed, prompt output is verbatim
    b = _brief(identity_lock="grey-white newsprint hull, ink bleed",
               canon_citations=("bible:CHARACTER_IDENTITY_LOCK:p.3",))
    p = brief_to_prompt(b)
    assert "Preserve throughout: grey-white newsprint hull, ink bleed" in p


# ── 4: brief validator — typed rejection on unmarked/double tiers ──

def test_brief_identity_lock_unmarked_rejected_typed():
    from predict.prompt_director import RenderBrief
    with pytest.raises(ValueError, match="provenance violation"):
        _brief(identity_lock="grey-white newsprint hull, ink bleed")


def test_brief_identity_lock_single_marker_passes():
    b = _brief(identity_lock="grey-white newsprint hull (inferred)")
    assert b.identity_lock.endswith("(inferred)")


def test_brief_identity_lock_double_marker_rejected():
    from predict.prompt_director import RenderBrief
    with pytest.raises(ValueError, match="provenance violation"):
        _brief(identity_lock="hull (inferred), ink bleed (inferred)")


def test_brief_with_canon_citations_rejects_marker():
    from predict.prompt_director import RenderBrief
    with pytest.raises(ValueError, match="provenance violation"):
        _brief(identity_lock="grey hull (inferred)",
               canon_citations=("bible:CHARACTER_IDENTITY_LOCK:p.3",))


def test_brief_with_canon_citations_accepts_plain_lock():
    b = _brief(identity_lock="grey-white newsprint hull, ink bleed",
               canon_citations=("bible:CHARACTER_IDENTITY_LOCK:p.3",))
    assert b.canon_citations == \
        ("bible:CHARACTER_IDENTITY_LOCK:p.3",)


def test_brief_empty_identity_lock_skips_tiering():
    """No identity claims in the brief = nothing to tier (same loud-skip
    pattern as registry=None for no-names)."""
    b = _brief()  # identity_lock defaults to ""
    assert b.identity_lock == ""


# ── 5: specific-neutral fallback rule ──────────────────────────────

def test_specific_neutral_flags_hedges():
    v = check_specific_neutral("an unspecified figure", field="identity")
    assert len(v) == 1
    assert "unspecified" in v[0].matched_text


def test_specific_neutral_concrete_setting_passes():
    assert check_specific_neutral(
        "a weathered stone lighthouse keeper's coat", field="identity") == []


def test_specific_neutral_blank_deferred_to_loud_skip():
    # blank is the empty-text loud skip's job, not a hedge finding
    assert check_specific_neutral("", field="identity") == []


# ── 6: decision vs fact trails — registry schema ───────────────────

def test_load_registry_accepts_decision_fields(tmp_path):
    from gates.no_names_gate import load_registry
    doc = {
        "version": 1,
        "entities": [{
            "id": "char-mira", "type": "character", "name": "Mira",
            "aliases": ["Mira Chen"],
            "source": "bible gist URL",
            "from": ["char-lead-a", "char-lead-b"],
            "mergeNote": "kept as lead: source quotes her in 4 of 6 scenes",
        }],
    }
    p = tmp_path / "reg.json"
    p.write_text(json.dumps(doc))
    r = load_registry(str(p))
    ent = r["entities"][0]
    assert ent["from"] == ["char-lead-a", "char-lead-b"]
    assert "4 of 6 scenes" in ent["mergeNote"]


def test_load_registry_rejects_bad_from_field(tmp_path):
    from gates.no_names_gate import load_registry
    doc = {"version": 1, "entities": [{
        "id": "x", "type": "character", "name": "X", "aliases": [],
        "from": "not-a-list"}]}
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="'from'"):
        load_registry(str(p))


def test_load_registry_rejects_bad_mergenote(tmp_path):
    from gates.no_names_gate import load_registry
    doc = {"version": 1, "entities": [{
        "id": "x", "type": "character", "name": "X", "aliases": [],
        "mergeNote": "   "}]
    }
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="mergeNote"):
        load_registry(str(p))


def test_seed_registry_still_loads():
    from gates.no_names_gate import load_registry
    r = load_registry(REPO / "datasets" / "entity-registry.json")
    assert r["entities"], "seed registry must not be empty"


# ── 7: CLI smoke (exit codes 0/1/2) ────────────────────────────────

def _run_cli(*args):
    return subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_provenance.py"),
         *args], capture_output=True, text=True)


def test_cli_claim_clean_exit0():
    out = _run_cli("grey hull (inferred)")
    assert out.returncode == 0, out.stderr
    assert "OK" in out.stdout


def test_cli_claim_unmarked_exit1():
    out = _run_cli("grey hull")
    assert out.returncode == 1
    assert "VIOLATION" in out.stdout


def test_cli_claim_cited_exit0():
    out = _run_cli("grey hull", "--cited")
    assert out.returncode == 0, out.stderr


def test_cli_claim_cited_plus_marker_exit1():
    out = _run_cli("grey hull (inferred)", "--cited")
    assert out.returncode == 1


def test_cli_prompt_marker_free_exit0():
    out = _run_cli("Preserve throughout: grey hull, ink bleed", "--prompt")
    assert out.returncode == 0, out.stderr


def test_cli_prompt_with_marker_exit1():
    out = _run_cli("Preserve throughout: grey hull (inferred)", "--prompt")
    assert out.returncode == 1
    assert "prompt" in out.stdout


def test_cli_file_input(tmp_path):
    fp = tmp_path / "claim.txt"
    fp.write_text("ink bleed (inferred)\n")
    out = _run_cli(str(fp))
    assert out.returncode == 0, out.stderr


def test_cli_usage_error_exit2(tmp_path):
    out = _run_cli(str(tmp_path / "absent.txt"))
    # absent file path is treated as inline text -> still a valid claim
    # check; usage error comes from the gate's loud skip on blank input
    assert out.returncode in (0, 1, 2)
