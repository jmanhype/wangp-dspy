# Beat-claim fields — machine-checkable lyric-boundary claims

Adopted from shuohao-skills hookBeat doctrine:
`docs/extraction/shuohao-skills/changelog-design-rationale.md`
**section C** — "说明给人读，认领给机器查" (declarations are for
humans, claims are for machines to check) at **L17-18**; the
`hookBeat` entry at **L47**; upstream CHANGELOG **:482-500** (novel-
script 1.1.0 — "衔接从此是门不是自觉": continuity becomes a gate,
not self-discipline).

## Schema (`gates/beat_claims.py`)

```
Phrase        {id, text, start, end}         # one lyric phrase
BeatGrid      {phrases: [Phrase]}            # timestamped boundaries
CutClaim      {phrase_id, offset,            # claimed landing:
               tolerance?}                   #   phrase.start + offset
CutRecord     {cut_id, time, claim?}         # what cut/shot entries
                                              # carry
```

Field semantics:
- `phrase_id` — MUST exist in the grid (unknown ref = violation).
- `offset` — seconds within the phrase; `0 <= offset <= end-start`
  (outside = violation).
- `tolerance` — optional per-cut override of the validator default;
  PASS when `|time - (start + offset)| <= tolerance`.
- `claim: None` on a CutRecord is a VIOLATION (unclaimed cut) —
  timing-sensitive cuts must claim; loud, never silent.

## Example records

```json
{"phrases": [
  {"id": "p1", "text": "neon rain on asphalt", "start": 0.0, "end": 4.0},
  {"id": "p2", "text": "she counts the sirens", "start": 4.0, "end": 8.0}]}

{"cuts": [
  {"cut_id": "c1", "time": 4.0,  "claim": {"phrase_id": "p2", "offset": 0.0}},
  {"cut_id": "c2", "time": 8.12, "claim": {"phrase_id": "p2", "offset": 4.0,
                                            "tolerance": 0.15}}]}
```

## Validator

`validate_beat_claims(grid, cuts, default_tolerance)` → violation
strings; typed `BeatClaimValidationError` (`.violations`) with
`raise_on_invalid=True`. Empty grid / empty cuts raise DISTINCT
typed kinds (`EMPTY_GRID` / `EMPTY_CUTS`) — loud skip, never a
silent pass. ZERO-MODEL: no LLM anywhere.

## CLI

`python scripts/check_beat_claims.py <grid.json> <cuts.json|->`
Per-cut PASS/FAIL report, violations on stderr; exit 0 clean /
1 violations / 2 usage-or-input error (incl. the loud-skip cases).
