"""comic_critics — judge-agnostic port of the COMIC video_eval harness.

Source of truth: /tmp/comic-eval/video_eval/evaluate_videos.py
(arXiv:2603.11048, "COMIC: Agentic Sketch Comedy Generation").

Contract preserved verbatim: INSTRUCTIONS template, [VOTING START]/
[WINNER]/[REVIEW] parsing, pairwise win-rate + per-channel reporting,
CSV/JSON output shapes (comparable with the Gemini baseline
eval_20260821_232933).

DELIBERATE DIVERGENCE from upstream: malformed judge output falls back
DETERMINISTICALLY to candidate-1 and records a parse_error; upstream
used random.choice — replaced per port spec.
"""
from __future__ import annotations

import csv
import json
import random
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

try:
    import numpy as np
except ImportError:  # pragma: no cover — numpy is a hard dep upstream;
    # keep import failure loud at call time, not import time
    np = None

INSTRUCTIONS = """Core Objective
Evaluate multiple candidate scene videos and vote for the one that you find most appealing and enjoyable to watch.

Requirements (MUST DO)
* Apply your perspective to evaluate the videos
* Output in the specified format

Constraints (MUST AVOID)
* Indecisive evaluations

Voting Framework
* Evaluate each candidate video based on your perspective
* Select the candidate that you would most enjoy watching

Input Format
You will receive multiple candidate videos labeled as "Candidate #1", "Candidate #2", etc.

Output Format
[VOTING START]

[WINNER START]Candidate #[number][WINNER END]

[REVIEW START]
Based on your perspective, provide a paragraph explaining your decision
[REVIEW END]

[VOTING END]

The candidate number should be an integer from 1 to N, where N is the number of candidate videos provided."""

FIELDS = ["method", "test_channel", "win_rate", "wins", "trials",
          "method_video_ids", "reference_video_ids", "evaluation_calls",
          "input_tokens", "output_tokens", "gemini_outputs",
          "critic_id", "critic_name", "critic_set", "metadata"]

DEFAULT_FALLBACK = 1  # deterministic, never random


# ── parsing ──────────────────────────────────────────────────────────────

def parse_vote(txt: str, n: int = 2) -> dict:
    """Parse [VOTING START]...[WINNER]...[REVIEW] contract.

    Malformed input -> {"best_candidate": 1 (deterministic),
    "reasoning": "", "parse_error": "<reason>"}.
    """
    out = {"best_candidate": DEFAULT_FALLBACK, "reasoning": "",
           "parse_error": "missing_voting_block"}
    v = re.search(r"\[VOTING START\](.+?)\[VOTING END\]", txt or "",
                  re.DOTALL | re.I)
    if not v:
        return out
    c = v.group(1)
    w = re.search(r"\[WINNER START\](.+?)\[WINNER END\]", c, re.I)
    m = re.search(r"Candidate\s*#?(\d+)", w.group(1) if w else c, re.I)
    if not m:
        out["parse_error"] = "winner_not_parsed"
    else:
        best = int(m.group(1))
        if 1 <= best <= n:
            out["best_candidate"] = best
            out.pop("parse_error")
        else:
            out["parse_error"] = "winner_out_of_range"
    r = re.search(r"\[REVIEW START\](.+?)\[REVIEW END\]", c,
                  re.DOTALL | re.I)
    if r:
        out["reasoning"] = r.group(1).strip()
    return out


# ── data loading ─────────────────────────────────────────────────────────

@dataclass
class Ref:
    id: str
    url: str
    channel: str


@dataclass
class Gen:
    method: str
    path: Path

    @property
    def did(self) -> str:
        return self.path.stem


def load_videos(d: Path) -> dict:
    out = {}
    for sub in sorted(x for x in d.iterdir() if x.is_dir()):
        vids = sorted(sub.glob("*.mp4"))
        if vids:
            out[sub.name] = [Gen(sub.name, v) for v in vids]
    return out


def load_refs(p: Path) -> dict:
    out = {}
    if not p.exists():
        return out
    ch = None
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            ch = line[1:].strip()
            continue
        if not ch:
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            out.setdefault(ch, []).append(Ref(parts[0], parts[1], ch))
    return out


def load_critics(p: Path) -> list:
    d = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(d, list):
        return d
    if isinstance(d.get("video_critics"), list):
        return d["video_critics"]
    return []


def load_clm(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8")).get(
            "channel_leads_map", {})
    except Exception:
        return {}


def build_cca(paths) -> dict:
    out = {}
    for p in paths:
        for ch, cid in load_clm(p).items():
            out.setdefault(cid, set()).add(ch)
    return out


# ── critic agent (judge-agnostic) ────────────────────────────────────────

def build_instructions(spec: dict) -> str:
    base = spec.get("content") or spec.get("system_instructions")
    if base:
        for ph in ["{{TASK-SPECIFIC INSTRUCTIONS WILL BE INSERTED HERE}}",
                   "{TASK-SPECIFIC INSTRUCTIONS WILL BE INSERTED HERE}"]:
            if ph in base:
                return base.replace(ph, INSTRUCTIONS)
        return base
    return INSTRUCTIONS


class CriticAgent:
    """Judge-agnostic critic: persona + judge backend."""

    def __init__(self, judge, spec: dict):
        self.judge = judge
        self.spec = spec or {}
        self.name = self.spec.get("name", "Agent")
        self.instr = build_instructions(self.spec)

    def evaluate(self, u1, u2, lp1=None, lp2=None) -> dict:
        if not (u1 or lp1) or not (u2 or lp2):
            return {"best_candidate": DEFAULT_FALLBACK,
                    "error": "Missing video", "agent_name": self.name}
        out = self.judge.vote_pair(self.instr, u1, u2, lp1, lp2)
        out.update(agent_name=self.name)
        return out


# ── comparison loop (seeded order, deterministic fallback) ──────────────

def run_cmp(agent, refs, gens, method, ch, double, delay, order_seed=0):
    import time
    w = t = ti = to = 0
    calls, gouts = [], []
    rng = random.Random(order_seed)  # seeded; NEVER global random
    for ref in refs:
        for gen in gens:
            # order tuples are (u1, u2, lp1, lp2, gen_is_cand2)
            ords = [(ref.url, "", None, str(gen.path), True)]
            if double:
                ords.append((str(gen.path), "", None, ref.url, False))
            elif rng.random() >= 0.5:
                ords = [(str(gen.path), "", None, ref.url, False)]
            for u1, u2, l1, l2, gw2 in ords:
                t0 = time.time()
                r = agent.evaluate(u1, u2, lp1=l1, lp2=l2)
                dt = time.time() - t0
                if r.get("error"):
                    print(f"      [ERR] {ref.id[:24]} vs {gen.did[:24]}: "
                          f"{r['error']}")
                    calls.append({"ref_id": ref.id, "gen_id": gen.did,
                                  "gen_wins": False,
                                  "error": r["error"]})
                    t += 1
                    time.sleep(delay)
                    continue
                b = r.get("best_candidate", DEFAULT_FALLBACK)
                gw = (b == 2) if gw2 else (b == 1)
                w += int(gw)
                t += 1
                ti += r.get("input_tokens") or 0
                to += r.get("output_tokens") or 0
                raw = r.get("raw_response") or ""
                calls.append({"ref_id": ref.id, "gen_id": gen.did,
                              "gen_wins": gw,
                              **({"parse_error": r["parse_error"]}
                                 if r.get("parse_error") else {}),
                              "raw_response": raw})
                gouts.append(raw)
                print(f"      [eval] {ref.id[:24]} vs {gen.did[:24]} "
                      f"-> #{b} gw={gw} {dt:.1f}s"
                      + (f" parse_error={r['parse_error']}"
                         if r.get("parse_error") else ""))
                time.sleep(delay)
    errs = sum(1 for c in calls if c.get("error"))
    perrs = sum(1 for c in calls if c.get("parse_error") and not c.get("error"))
    if errs or perrs:
        print(f"      [SUMMARY] {errs} transport/error calls, "
              f"{perrs} parse_error fallbacks "
              f"(fallback votes count as candidate-1) — check CSV before "
              f"trusting win_rate" if (errs or perrs) else "", end="\n")
    return {"method": method, "test_channel": ch,
            "win_rate": w / t if t else 0, "wins": w, "trials": t,
            "errors": errs, "parse_errors": perrs,
            "method_video_ids": json.dumps([g.did for g in gens]),
            "reference_video_ids": json.dumps([r.id for r in refs]),
            "evaluation_calls": json.dumps(calls, ensure_ascii=False),
            "input_tokens": ti, "output_tokens": to,
            "gemini_outputs": json.dumps(gouts, ensure_ascii=False)}


# ── metrics (same shapes as baseline) ────────────────────────────────────

def _prob_matrix(rows):
    W = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    T = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    E, B, A = set(), set(), set()
    for row in rows:
        e = row["critic_id"]
        E.add(e)
        ec = row["evaluation_calls"]
        if isinstance(ec, str):
            ec = json.loads(ec)
        for c in ec:
            if c.get("error"):
                continue
            a, b, gw = c["ref_id"], c["gen_id"], c["gen_wins"]
            A.add(a)
            B.add(b)
            T[e][b][a] += 1
            if gw:
                W[e][b][a] += 1
    E, B, A = sorted(E), sorted(B), sorted(A)
    P = {e: {b: {a: (W[e][b][a] / T[e][b][a] if T[e][b][a] else None)
               for a in A} for b in B} for e in E}
    return P, E, B, A


def metrics(rows):
    if not rows:
        return {"avg_win_rate": 0.0, "g_norm_inter": 0.0,
                "g_norm_intra": 0.0}
    P, E, B, A = _prob_matrix(rows)
    vs = [P[e][b][a] for e in E for b in B for a in A
          if P[e][b][a] is not None]
    wr = float(np.mean(vs)) if vs else 0.0
    prof = {b: np.array([P[e][b][a] for e in E for a in A
                         if P[e][b][a] is not None]) for b in B}
    intra = float(np.mean([np.var(prof[b]) for b in B
                           if len(prof[b]) > 0])) if B else 0.0
    iv = []
    for e in E:
        for a in A:
            pv = [P[e][b][a] for b in B if P[e][b][a] is not None]
            if len(pv) > 1:
                iv.append(np.var(pv))
    inter = float(np.mean(iv)) if iv else 0.0
    mx = wr * (1 - wr)
    gi, ga = (inter / mx, intra / mx) if mx > 1e-9 else (0.0, 0.0)
    return {"avg_win_rate": wr, "g_norm_inter": gi, "g_norm_intra": ga}


def _metrics_table(results, label, critic_sets=None):
    rows = results
    if critic_sets is not None:
        rows = [r for r in results if r.get("critic_set") in critic_sets]
    if not rows:
        return {}
    grp = defaultdict(lambda: defaultdict(list))
    for r in rows:
        grp[r["method"]][r["test_channel"]].append(r)
    meths = sorted(grp, key=lambda m: (0 if m == "ours" else 1, m))
    chs = sorted({c for m in grp for c in grp[m]})
    out = {}
    for m in meths:
        pc = {c: metrics(grp[m][c]) for c in chs if grp[m].get(c)}
        avg = {k: float(np.mean([pc[c][k] for c in pc])) for k in
               ["avg_win_rate", "g_norm_inter", "g_norm_intra"]} if pc else {}
        out[m] = {"per_channel": pc, "avg": avg}
    print(f"\n{'=' * 72}\n  {label} — avg across channels\n{'=' * 72}")
    print(f"{'Method':<12} {'WinRate':>10} {'G-N-Inter':>12} "
          f"{'G-N-Intra':>12}")
    print("-" * 72)
    for m in meths:
        a = out[m]["avg"]
        if a:
            print(f"{m:<12} {a['avg_win_rate']:>10.4f} "
                  f"{a['g_norm_inter']:>12.4f} "
                  f"{a['g_norm_intra']:>12.4f}")
    print(f"\n{'=' * 72}\n  {label} — per-channel win rate\n{'=' * 72}")
    hdr = f"{'Method':<12}"
    hdr += "".join(f" {c[:14]:>14}" for c in chs)
    hdr += f" {'MEAN':>8}"
    print(hdr)
    print("-" * len(hdr))
    for m in meths:
        pc = out[m]["per_channel"]
        vs = []
        ln = f"{m:<12}"
        for c in chs:
            if c in pc:
                v = pc[c]["avg_win_rate"]
                ln += f" {v:>14.4f}"
                vs.append(v)
            else:
                ln += f" {'—':>14}"
        ln += f" {float(np.mean(vs)):>8.4f}" if vs else ""
        print(ln)
    print()
    return out


def print_all_metrics(results, combined=True):
    csets = sorted({r.get("critic_set", "") for r in results})
    per_set = {}
    for cs in csets:
        per_set[cs] = _metrics_table(results, f"CRITIC SET: {cs}",
                                     critic_sets={cs})
    out = {f"set_{cs}": per_set[cs] for cs in csets}
    if combined:
        out["combined"] = _metrics_table(
            results, "COMBINED (global_best + channel_best)")
    return out


# ── persistence ──────────────────────────────────────────────────────────

def _csv_append(row, path, first):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, FIELDS, extrasaction="ignore")
        if first:
            w.writeheader()
        w.writerow(row)


def _csv_write(rows, path):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def save(results, csv_path, args_d, combined=True):
    _csv_write(results, csv_path)
    m = print_all_metrics(results, combined=combined)
    jp = csv_path.with_suffix(".json")
    jp.parent.mkdir(parents=True, exist_ok=True)
    with open(jp, "w", encoding="utf-8") as f:
        json.dump({**args_d, "metrics": m}, f, indent=2,
                  ensure_ascii=False)
    print(f"  CSV: {csv_path}\n  JSON: {jp}")
