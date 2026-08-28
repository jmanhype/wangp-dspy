# QC Failure Triage — gate / rule / example (WD-rty2, ADOPT #7)

ADOPT of the shuohao-skills three-tier escalation ladder
(`docs/extraction/shuohao-skills/changelog-design-rationale.md`
section B; CHANGELOG:384-398). When a QC failure recurs in the
VLM-curator loop, decide **explicitly** which tier absorbs it.

## The central axiom

> "误拦的门比没有门更糟——门的信用比数量重要"
>
> *A false-blocking gate is worse than no gate; a gate's credibility
> matters more than its count.*
>
> — extraction :12, citing CHANGELOG:355-356 (the phrase recurs at
> least 5× in the source repo and is its central gate-design axiom)

Consequence: we would rather let one bad render through to a human
than ship a gate that blocks good material. Every recurring failure
is triaged against this before any gate is added.

## The three classes

| Class | Signal (deterministic) | Action |
|---|---|---|
| `gate_false_positive` | Gate fired (REVISE/REJECT) but a human review passed the material, or the material later passed | Fix or **remove** the gate (`action_taken=gate-fixed`) |
| `rule_violation` | A **named** rule was violated and no gate fired on it | Fix the material/brief (`brief-fixed`) |
| `example_gap` | Human flagged something with **no named rule** and no deterministic signal | Add/fix an exemplar (`exemplar-added`) — do **NOT** build a keyword gate |

Escalation (`escalated-human`) is the action when none of the tiers
absorb the failure cleanly.

## Mapped onto our RenderQC vocabulary

- **Verdict.PASS / REVISE / REJECT** (`evaluate/render_qc.py`): the
  gate verdict for an event. A PASS that a human flags → rule
  violation or example gap; a REVISE/REJECT that a human passes →
  gate false positive.
- **GENRE_THRESHOLDS**: per-genre threshold profile; the stats view
  keys fire counts by `gate_id`, so a genre-tuned threshold gate
  that dominates the ledger says *rewrite that gate's wording or
  threshold*, not "add another gate".
- **CONCEPT_ENCODING_FAILURE** (informed-good + blind-bad gap):
  inherently semantic — the informed judge sees the prompt text,
  the blind judge does not. This is the canonical **ungateable**
  case: it lands in `example_gap` (demonstrate the concept in the
  exemplars) or `escalated-human`, never in a new keyword gate.
- **QCEscalationError** (`host/wangp_adapter.py`): the typed
  "one revision already granted and it persists" escalation — the
  event that feeds the ledger as `escalated-human`.
- **Keyword scans leak both ways** (extraction section B, voice
  case :103): a scan for "时"/"区" would flag legitimate "说话时"/
  "低音区". That is why tier 2 is a *craft rule + reasoning* and
  tier 3 is *example-as-norm* ("样例即规范") — never a third kind
  of gate.

## Decision procedure

1. **First ask: is this deterministically judgeable?**
   - Yes → it belongs in a hard gate/rule. If the gate already
     exists and fired wrongly, the class is
     `gate_false_positive` — fix the gate, don't stack another.
   - No → do NOT build a keyword gate. Tier 2 (named craft rule,
     fixed in the brief) if a rule can be named; tier 3 (exemplar)
     otherwise.
2. Record the event in the ledger (append-only JSONL,
   `datasets/qc-triage-ledger.schema.json`). Evidence stays
   **verbatim** — never paraphrased into the record.
3. A human decides the action. The ledger has **no auto-rewrite
   path** ("没有评测集的自动改文档就是瞎改" — auto-editing docs
   without an eval set is blind editing; extraction section G).

## Stats discipline (section G, .gates.jsonl pattern)

`stats()` over the ledger answers exactly three questions:

- **Which class dominates?** — the shape of our failure mode.
- **Which gate fires most?** — rewrite that gate's wording/threshold.
- **Which gate never fires?** — dead gate or internalized; remove
  it (a gate that never fires still costs credibility).

CLI: `python scripts/check_qc_triage.py --stats [PATH]`.

## Contract

- `gates/qc_triage.py` — ZERO-MODEL, deterministic field logic over
  structured events (same contract as `gates/provenance_gate.py`:
  typed errors, loud skip on empty input, `__all__`).
- Existing gates are NOT modified by this story; the classifier
  consumes their verdicts as input records.
- Tests: `tests/test_qc_triage.py` (typed violations, seed data,
  CLI exit-code smoke 0/1/2).
