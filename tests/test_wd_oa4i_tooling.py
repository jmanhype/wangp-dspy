"""WD-oa4i STEP 2 — bank re-point + manifest + baseline tooling.

Covers:
1. Bank re-point: every 20260824-* run record's videos[] resolves
   relative to the repo root (datasets/runs/pull/outputs/archive/...),
   except 20260824-112120 whose video is provenance-lost (documented
   exclusion via its "curation" marker — Luna G7 waiver rule).
2. scripts/build_manifest.py — datasets/manifest.json, one row per
   banked run record, curation status from curation.json + marker.
3. scripts/run_baseline.py — zero gepa imports, writes
   metrics/baseline_score.json via load_examples + qc_feedback_metric.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _load_script(name):
    spec = importlib.util.spec_from_file_location(
        name, REPO / "scripts" / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _bank():
    return sorted((REPO / "datasets" / "runs").glob("20260824-*.json"))


# ---------------------------------------------------------------- 1. bank

def test_bank_has_nine_20260824_records():
    assert len(_bank()) == 9


def test_banked_videos_resolve_repo_relative():
    """All records' videos[0] exist relative to repo root; 112120 is
    exempted ONLY if it carries the provenance-lost curation marker."""
    for p in _bank():
        rec = json.loads(p.read_text())
        vids = rec.get("videos", [])
        if not vids:
            continue
        v = vids[0]
        marker = (rec.get("curation") or {}).get(
            "videos_provenance_lost", False)
        if marker:
            # documented exclusion: must NOT invent a path
            assert not v.startswith("/") or not (REPO / v.lstrip("/")).exists()
            assert (rec["curation"].get("note", "")
                    .lower().find("provenance") >= 0)
            continue
        assert not Path(v).is_absolute(), \
            f"{p.name}: videos[0] still absolute: {v}"
        assert (REPO / v).exists(), \
            f"{p.name}: videos[0] does not resolve: {v}"


def test_112120_documented_exclusion():
    rec = json.loads(
        (REPO / "datasets" / "runs" / "20260824-112120.json").read_text())
    cur = rec.get("curation")
    assert cur and cur.get("videos_provenance_lost") is True
    assert "provenance" in cur.get("note", "").lower()
    # the original lost path must be preserved verbatim for the audit
    assert rec["videos"][0].endswith("multishot_1787589072.mp4")


# ------------------------------------------------------- 2. manifest

def _build_manifest(tmp_path, bank_dir):
    mod = _load_script("build_manifest.py")
    out = tmp_path / "manifest.json"
    mod.build_manifest(
        runs_dir=bank_dir,
        curation_path=REPO / "datasets" / "wd-oa4i" / "curation.json",
        out_path=out)
    return json.loads(out.read_text()), out


def test_manifest_dry_run_on_current_bank(tmp_path):
    rows, out = _build_manifest(tmp_path, REPO / "datasets" / "runs")
    assert out.exists()
    assert rows["story"] == "WD-oa4i"
    body = rows["rows"]
    assert len(body) == 9  # one row per banked record (6 kept + 3 dropped)
    kept = [r for r in body if r["curation_status"] == "kept"]
    assert len(kept) == 6
    by_run = {r["run_id"]: r for r in body}
    # kept row shape
    r = by_run["20260824-110409"]
    assert r["intent"].startswith("a lighthouse beacon")
    assert r["qc_score"] == 9
    assert r["critic_id"].startswith("qwen38-27b")
    assert r["video_path"] == ("datasets/runs/pull/outputs/archive/"
                               "multishot_1787588035.mp4")
    # dropped rows carry the curation.json reason
    d = by_run["20260824-103137"]
    assert d["curation_status"] == "dropped"
    assert "exact-intent duplicate" in d["curation_reason"]
    # 112120: excluded + provenance reason from its in-record marker
    e = by_run["20260824-112120"]
    assert e["curation_status"] == "excluded"
    assert "provenance" in e["curation_reason"].lower()
    assert e["video_path"] is None
    # every non-excluded row's video resolves relative to repo root
    for r in body:
        if r["curation_status"] != "excluded":
            assert (REPO / r["video_path"]).exists(), r


def test_manifest_records_are_verifiable_against_bank(tmp_path):
    rows, _ = _build_manifest(tmp_path, REPO / "datasets" / "runs")
    bank = {p.stem: json.loads(p.read_text()) for p in _bank()}
    for r in rows["rows"]:
        rec = bank[r["run_id"]]
        assert r["qc_score"] == rec["qc"]["score"]
        assert r["intent"] == rec["intent"]


# ------------------------------------------------------- 3. baseline

def test_run_baseline_zero_gepa_imports():
    src = (REPO / "scripts" / "run_baseline.py").read_text()
    assert "gepa" not in src.lower().replace(
        "zero gepa", "").replace("no gepa", "")


def test_run_baseline_dry_run(tmp_path, monkeypatch):
    mod = _load_script("run_baseline.py")
    # baseline evaluates a trivial identity-free predictor: reuse gold
    # briefs directly via a stub class so no LLM is called.
    monkeypatch.setattr(mod, "_predict", lambda ex: _GoldAsPred(ex))
    out = tmp_path / "baseline_score.json"
    score = mod.run_baseline(
        runs_dir=REPO / "datasets" / "runs", out_path=out)
    data = json.loads(out.read_text())
    assert data["story"] == "WD-oa4i"
    assert data["n_val"] >= 1
    assert isinstance(data["score"], float)
    assert data["score"] == score
    assert data["timestamp_utc"].endswith("Z")
    assert len(data["git_head"]) == 40
    assert data["git_head"] == subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO,
        capture_output=True, text=True).stdout.strip()


class _GoldAsPred:
    """Predictor stub: returns the gold brief itself (upper bound)."""
    def __init__(self, ex):
        self.brief = ex.brief
