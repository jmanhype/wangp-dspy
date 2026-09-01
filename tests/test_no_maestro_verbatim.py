"""Assert no verbatim Maestro code was vendored into this repo.

Reference corpus: excerpts of the Maestro Director sources (read-only,
on the 3090), checked in ONLY under tests/fixtures/maestro_reference
as comparison material. We strip those fixtures and tests/ from the
"our tree" side, then look for any shared verbatim run of >= 21
non-trivial lines.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF_DIR = Path(__file__).resolve().parent / "fixtures" / "maestro_reference"
MIN_MATCH_LINES = 21  # >20-line verbatim match => vendored


def _norm_lines(text: str):
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


def _windows(lines, n):
    for i in range(len(lines) - n + 1):
        yield i, tuple(lines[i:i + n])


def test_no_verbatim_maestro_matches():
    ref_lines = []
    for f in sorted(REF_DIR.glob("*.txt")):
        ref_lines.extend(_norm_lines(f.read_text(errors="replace")))
    assert len(ref_lines) > 500, "reference corpus looks truncated"

    # Our tree: everything except the fixtures and tests themselves.
    ours = []
    for p in ROOT.rglob("*.py"):
        sp = str(p)
        if "/.git/" in sp or "/tests/" in sp or "/.venv/" in sp \
                or "/__pycache__/" in sp:
            continue
        ours.append((p, _norm_lines(p.read_text(errors="replace"))))

    n = MIN_MATCH_LINES
    # index our windows once
    ours_index = {}
    for p, lines in ours:
        for _, w in _windows(lines, n):
            ours_index.setdefault(w, []).append(p)

    hits = []
    for i in range(0, len(ref_lines) - n + 1, 5):  # stride for speed
        w = tuple(ref_lines[i:i + n])
        if w in ours_index:
            hits.append((i, ours_index[w]))

    assert not hits, (
        f"verbatim {n}-line Maestro matches found in our tree: {hits[:3]}")
