## 2026-08-28 ~05:30 CDT — Discovery cycle 001

**State snapshot**
- Open: WD-cz6a (P1, S2 diarization — merged as #38 but story not yet closed; verify
  evidence + close), WD-j9nx (P2 epic, film lane master), WD-r8n9 (P2 scanner
  false-positive, upstream hermes-agent#93927, blocked on upstream).
- Last merges: #38 S2 diarization schema/validator/converter; #37 S1
  WanGPJobConfig + Ref2VA profile + six entry-point gates; #36 spec/plan templates.
- Ledger was EMPTY before this append (prior cycles' recommendations, if any,
  were never recorded — nothing to promote/supersede/retire).

**What changed since last cycle**
S1 and S2 landed back-to-back. Both are pure contract/schema layers: typed
configs, validators, deterministic converters, gates. Zero GPU contact. Epic
WD-j9nx AC #3 explicitly requires "proven on the real GPU ... through the
PIPELINE, not the adapter alone" — currently 0% satisfied, and every additional
schema-only story (S3 `<d>` speaker gate next) adds integration surface that
has never been exercised end-to-end even once.

**Top recommendation (NEW)**
**Thin vertical slice: one real e2e run before S3.** Take one real audio file →
out-of-repo diarization tool → real timeline JSON → S2 converter → S1 Ref2VA
WanGPJobConfig → G5 prompt assembly → ONE real render on the 3090 → VLM QC
verdict → record artifacts against the run-evidence contract. Small scope
(~1 day): no new schemas, no new gates — glue + one render.

Rationale on the three criteria:
- *Leverage/day*: highest in the backlog. A single live run will surface every
  contract mismatch (timestamp tolerances, `<d>` shape vs G5 reality, Ref2VA
  profile defaults vs WanGP's actual CLI) at once, while fixes are still
  one-file changes instead of cross-layer refactors after S3/S4 land on top.
- *Compounding*: produces the first replayable evidence trail + the baseline
  run the epic's optimizability AC (#4, LabeledFewShot baseline) needs anyway.
  Same artifacts feed metrics later — dual-use.
- *Irreplaceability*: nobody else can do this — it needs the 3090, real audio,
  and operator's keeper-eye QC judgment. Schema stories are agent-commodities;
  the live run is not.

**Priors**: none on record (ledger empty). Notes carried forward: WD-cz6a
needs evidence-verified closure; WD-r8n9 stays parked on upstream — do not
spend local days reimplementing scanner tiers.

**Anti-recommendation (explicit)**: do NOT start S3's speaker gate before the
slice runs. Building a third consecutive unexercised contract layer is the
"paper-only compounding" failure mode the epic's AC #6 exists to prevent.

## 2026-08-28 ~06:40 CDT — Loop closure note (cycle 001)

Cycle 001's top recommendation ("Thin vertical slice: one real e2e run before
S3") is now ACTED ON: filed as **WD-clms** "S2.5: thin vertical slice — one
real e2e render through the full stack" under epic WD-j9nx, P1, per operator
ruling 2026-08-28. The anti-recommendation stands in force until delivery: S3
(`<d>` speaker gate) remains queued and must not start before this slice runs.
Outcome to be appended at delivery (run record path + mismatch count).
