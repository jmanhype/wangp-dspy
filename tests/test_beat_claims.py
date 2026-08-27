"""WD-4s1b RED tests — beat-grid/lyric-boundary claim validation.

Doctrine: 说明给人读，认领给机器查 (declarations are for humans,
claims are for machines to check) — changelog-design-rationale.md
section C. ZERO-MODEL: no LLM, no network.
"""
import pytest

from gates.beat_claims import (
    BeatGrid, Phrase, CutClaim, CutRecord,
    validate_beat_claims, BeatClaimValidationError,
    EMPTY_GRID, EMPTY_CUTS,
)


def _grid():
    return BeatGrid(phrases=[
        Phrase(id="p1", text="first line here", start=0.0, end=4.0),
        Phrase(id="p2", text="second line", start=4.0, end=8.0),
        Phrase(id="p3", text="third", start=8.0, end=12.0),
    ])


def _cuts(**over):
    base = [
        CutRecord(cut_id="cut-1", time=4.0,
                  claim=CutClaim(phrase_id="p1", offset=4.0)),
        CutRecord(cut_id="cut-2", time=8.0,
                  claim=CutClaim(phrase_id="p2", offset=4.0)),
    ]
    if "replace" in over:
        return over["replace"]
    if "first" in over:
        base[0] = over["first"]
    if "second" in over:
        base[1] = over["second"]
    return base


# ── valid claims pass ─────────────────────────────────────────────────

def test_valid_claims_pass():
    assert validate_beat_claims(_grid(), _cuts(),
                                default_tolerance=0.05) == []


def test_per_cut_tolerance_override():
    # cut-2 drifts 0.3s beyond default but carries its own tolerance
    cuts = _cuts(second=CutRecord(
        cut_id="cut-2", time=8.3,
        claim=CutClaim(phrase_id="p2", offset=4.0, tolerance=0.5)))
    assert validate_beat_claims(_grid(), cuts,
                                default_tolerance=0.05) == []


# ── unknown phrase ref rejected ───────────────────────────────────────

def test_unknown_phrase_ref_rejected():
    cuts = _cuts(first=CutRecord(
        cut_id="cut-1", time=4.0,
        claim=CutClaim(phrase_id="pX", offset=4.0)))
    v = validate_beat_claims(_grid(), cuts, default_tolerance=0.05)
    assert any("pX" in x for x in v)
    assert any("unknown" in x.lower() or "not found" in x.lower()
               for x in v)


# ── offset outside phrase bounds rejected ────────────────────────────

def test_offset_beyond_phrase_end_rejected():
    cuts = _cuts(first=CutRecord(
        cut_id="cut-1", time=4.0,
        claim=CutClaim(phrase_id="p1", offset=5.0)))  # phrase is 0-4
    v = validate_beat_claims(_grid(), cuts, default_tolerance=0.05)
    assert any("offset" in x.lower() and ("bound" in x.lower()
                                          or "p1" in x) for x in v)


def test_negative_offset_rejected():
    cuts = _cuts(first=CutRecord(
        cut_id="cut-1", time=0.0,
        claim=CutClaim(phrase_id="p1", offset=-0.1)))
    v = validate_beat_claims(_grid(), cuts, default_tolerance=0.05)
    assert any("offset" in x.lower() for x in v)


# ── tolerance boundary cases ──────────────────────────────────────────

def test_exactly_at_tolerance_passes():
    # claimed landing p1+4.0 = 4.0; actual 4.05; tolerance 0.05: PASS
    cuts = _cuts(first=CutRecord(
        cut_id="cut-1", time=4.05,
        claim=CutClaim(phrase_id="p1", offset=4.0)))
    assert validate_beat_claims(_grid(), cuts,
                                default_tolerance=0.05) == []


def test_just_beyond_tolerance_rejected():
    # actual 4.0501 > 4.0 + 0.05 -> violation
    cuts = _cuts(first=CutRecord(
        cut_id="cut-1", time=4.0501,
        claim=CutClaim(phrase_id="p1", offset=4.0)))
    v = validate_beat_claims(_grid(), cuts, default_tolerance=0.05)
    assert any("tolerance" in x.lower() or "drift" in x.lower()
               or "cut-1" in x for x in v)


# ── empty inputs: typed, loud, DISTINCT ──────────────────────────────

def test_empty_grid_distinct_typed():
    with pytest.raises(BeatClaimValidationError) as ei:
        validate_beat_claims(BeatGrid(phrases=[]), _cuts(),
                             default_tolerance=0.05)
    assert "grid" in str(ei.value).lower()
    assert ei.value.kind == EMPTY_GRID


def test_empty_cuts_distinct_typed():
    with pytest.raises(BeatClaimValidationError) as ei:
        validate_beat_claims(_grid(), [], default_tolerance=0.05)
    assert "cut" in str(ei.value).lower()
    assert ei.value.kind == EMPTY_CUTS


# ── typed raise mode ──────────────────────────────────────────────────

def test_raise_on_invalid():
    cuts = _cuts(first=CutRecord(
        cut_id="cut-1", time=99.0,
        claim=CutClaim(phrase_id="p1", offset=4.0)))
    with pytest.raises(BeatClaimValidationError):
        validate_beat_claims(_grid(), cuts, default_tolerance=0.05,
                             raise_on_invalid=True)


# ── cut without a claim ───────────────────────────────────────────────

def test_unclaimed_cut_flagged():
    """A cut record with NO claim field: per the doctrine every cut
    that lands timing-sensitive MUST claim — unclaimed is a
    violation (loud), not a silent pass."""
    from gates.beat_claims import CutRecord as CR
    cuts = [CR(cut_id="cut-1", time=4.0, claim=None)]
    v = validate_beat_claims(_grid(), cuts, default_tolerance=0.05)
    assert any("no claim" in x.lower() or "unclaimed" in x.lower()
               for x in v)


# ── CLI contract ──────────────────────────────────────────────────────

def _write(tmp_path, name, obj):
    import json
    p = tmp_path / name
    p.write_text(json.dumps(obj))
    return str(p)


GRID_JSON = {"phrases": [
    {"id": "p1", "text": "first", "start": 0.0, "end": 4.0},
    {"id": "p2", "text": "second", "start": 4.0, "end": 8.0},
]}
CUTS_OK = {"cuts": [
    {"cut_id": "c1", "time": 4.0,
     "claim": {"phrase_id": "p2", "offset": 0.0}},
]}
CUTS_BAD = {"cuts": [
    {"cut_id": "c1", "time": 5.5,
     "claim": {"phrase_id": "p2", "offset": 0.0}},
]}


def test_cli_clean_exit_zero(tmp_path, capsys):
    from scripts.check_beat_claims import main
    rc = main([_write(tmp_path, "g.json", GRID_JSON),
               _write(tmp_path, "c.json", CUTS_OK)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "PASS" in out and "c1" in out


def test_cli_violation_exit_one(tmp_path, capsys):
    from scripts.check_beat_claims import main
    rc = main([_write(tmp_path, "g.json", GRID_JSON),
               _write(tmp_path, "c.json", CUTS_BAD)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "FAIL" in out and "c1" in out


def test_cli_usage_error_exit_two(tmp_path, capsys):
    from scripts.check_beat_claims import main
    rc = main([str(tmp_path / "missing.json"),
               str(tmp_path / "also-missing.json")])
    assert rc == 2


def test_cli_stdin_support(tmp_path, capsys, monkeypatch):
    import io
    import json
    from scripts.check_beat_claims import main
    gp = _write(tmp_path, "g.json", GRID_JSON)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(CUTS_OK)))
    rc = main([gp, "-"])
    assert rc == 0
