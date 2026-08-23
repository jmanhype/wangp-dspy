"""CLI: python -m qc.comic_critics.evaluate --gen <dir> --judge local|glm|gemini"""
from __future__ import annotations

import argparse
import json
import random
import re
from datetime import datetime
from pathlib import Path

from .core import (build_cca, load_clm, load_critics, load_refs,
                   load_videos, run_cmp, save, _csv_append, CriticAgent)
from .judges import make_judge

DATA = Path("/tmp/comic-eval/data")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gen", type=Path, required=True,
                   help="dir containing per-method subdirs of .mp4s")
    p.add_argument("--judge", choices=["local", "glm", "gemini"],
                   required=True)
    p.add_argument("--refs", type=Path, default=DATA / "test" / "middle.txt")
    p.add_argument("--critics", type=Path, nargs="+", default=[
        DATA / "critics" / "global_best.json",
        DATA / "critics" / "channel_best.json"])
    p.add_argument("--max-refs", type=int, default=2)
    p.add_argument("--max-gens", type=int, default=None)
    p.add_argument("--report-dir", type=Path, required=True)
    p.add_argument("--request-delay", type=float, default=0.0)
    p.add_argument("--double-evaluation", action="store_true")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--methods", nargs="*", default=None)
    p.add_argument("--no-combined", action="store_true")
    p.add_argument("--model", default=None, help="override judge model")
    a = p.parse_args()

    if not a.gen.exists():
        raise SystemExit(f"Not found: {a.gen}")
    meths = load_videos(a.gen)
    if a.methods:
        meths = {m: v for m, v in meths.items() if m in a.methods}
    if a.max_gens:
        meths = {m: v[:a.max_gens] for m, v in meths.items()}
    if not meths:
        raise SystemExit("No method videos found.")
    print(f"Methods: {list(meths.keys())}")

    refs = load_refs(a.refs)
    if a.max_refs:
        refs = {ch: v[:a.max_refs] for ch, v in refs.items()}
    if not refs:
        raise SystemExit(f"No test refs found in {a.refs}")
    print(f"Channels: {list(refs.keys())}")

    specs, seen = [], set()
    for cp in a.critics:
        if not cp.exists():
            continue
        for s in load_critics(cp):
            cid = s.get("id", "?")
            if cid not in seen:
                seen.add(cid)
                specs.append((cp.stem, s))
    if not specs:
        raise SystemExit("No critics.")
    cca = build_cca(a.critics)
    specs.sort(key=lambda x: (0 if x[1].get("id") not in cca else 1))

    kw = {"model": a.model} if a.model else {}
    judge = make_judge(a.judge, **kw)
    print(f"Judge: {a.judge} ({type(judge).__name__}), "
          f"model={getattr(judge, 'model', '?')}, double: "
          f"{a.double_evaluation}")

    ch_ord = []
    for cp in a.critics:
        for c in load_clm(cp):
            if c not in ch_ord:
                ch_ord.append(c)
    ch_ord += sorted(c for c in refs if c not in ch_ord)

    sm = sorted(meths, key=lambda m: (0 if m == "ours" else 1, m))
    stamp = f"eval_{datetime.now():%Y%m%d_%H%M%S}"
    a.report_dir.mkdir(parents=True, exist_ok=True)
    out_csv = a.report_dir / f"{stamp}_{a.judge}.csv"
    ad = {"gen_dir": str(a.gen), "test_refs": str(a.refs),
          "judge": a.judge, "model": getattr(judge, "model", None),
          "double": a.double_evaluation, "seed": a.seed,
          "max_refs": a.max_refs}

    cs, results = {}, []
    for ci, (sn, sp) in enumerate(specs, 1):
        cid = re.sub(r"[^A-Za-z0-9._-]", "_", sp.get("id", f"C{ci}"))
        cp = a.report_dir / f"{stamp}_critic_{ci:02d}_{cid}.csv"
        asgn = cca.get(cid)
        chs = [c for c in ch_ord if c in asgn] if asgn else list(ch_ord)
        if cp.exists():
            cp.unlink()
        cs[cid] = dict(i=ci, sn=sn, sp=sp, cp=cp, fst=True, chs=chs,
                       ag=CriticAgent(judge, sp))

    for mn in sm:
        gv = meths[mn]
        print(f"\n{'#' * 72}\nMETHOD: {mn} ({len(gv)} videos)\n{'#' * 72}")
        for ci, (sn, sp) in enumerate(specs, 1):
            cid = sp.get("id", f"C{ci}")
            c = cs[cid]
            print(f"  Critic {ci}/{len(specs)}: "
                  f"{sp.get('name', cid)} [{sn}]")
            for ch in c["chs"]:
                if ch not in refs:
                    continue
                rv = refs[ch]
                print(f"    {mn} vs {ch}: {len(gv)}x{len(rv)}")
                row = run_cmp(c["ag"], rv, gv, mn, ch,
                              a.double_evaluation, a.request_delay,
                              order_seed=a.seed)
                row.update(critic_id=cid, critic_name=sp.get("name", cid),
                           critic_set=sn,
                           metadata=json.dumps(
                               {"judge": a.judge,
                                "model": getattr(judge, "model", None)}))
                results.append(row)
                _csv_append(row, c["cp"], c["fst"])
                c["fst"] = False
                print(f"      wr={row['win_rate']:.4f} "
                      f"({row['wins']}/{row['trials']})")
        save(results, out_csv, ad, combined=not a.no_combined)


if __name__ == "__main__":
    main()
