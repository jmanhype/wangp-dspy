---
run_id: luna-wdoa4i-gates-20260826
status: open
story: WD-oa4i
type: capture
---
Gate checklist artifact defining the PASS/BLOCK gates for WD-oa4i acceptance criteria (a)-(e) in issues/WD-oa4i.md. Prepared read-only by luna-tester 2026-08-26 ~08:46-09:00 CDT at HEAD 8c60eaa; renders not yet complete at capture time, so all gates remain OPEN pending the final 31-record dataset.

GATES (run on final 31-example dataset):
(a) Manifest completeness: manifest covering all 31 examples must carry source run_id, intent, QC score, provenance (video path + critic id), curation status. Today only 20260824-164317 has a curation field; no manifest file exists yet -> BLOCK until present and complete for all 31.
(b) Dedup + no train/val leakage: exact-intent dedup, normalized-subject dedup, full-brief sha256 (7 fields: subject/motion/camera/style/audio_direction/negatives/identity_lock) across all 31; plus cross-split check that no duplicate brief lands one copy in train and one in val. Loader is deterministic positional split (sorted glob, k=int(n*0.7), NO seed/shuffle/hash) so identical intents are adjacent -> guaranteed same-split today, but gate still verifies post-split. Known pre-existing dupes in bank: lighthouse x3 (103137/110409/112120), kaiju x2 (114250/121701) — 6 unique of 9; dev must document disposition (keep as repeats or curate out).
(c) Independent held-out validation: verify valset = 10 examples, disjoint from trainset by identity AND by brief-hash; confirm 31 -> exactly 21/10 under metrics/qc_feedback.py load_examples (verified arithmetic: int(31*0.7)=21).
(d) Baseline eval recorded BEFORE any GEPA: compiled/baseline_director.json must exist with a recorded valset score timestamped before any gepa run; training/run_baseline_then_gepa.py runs baseline-first but the recorded artifact + score must be checked.
(e) No GPU render during optimization: verify via git log/process evidence that the 22 new records were produced by real Pipeline.forward 3090 runs (decisions[].model=h3, videos[] paths exist, qc.critic typed verdict) and that no render was invoked inside any optimization step.

PROVENANCE: analysis performed read-only by luna-tester against repo state at HEAD 8c60eaa (working tree dirty: datasets/wd-oa4i/intents.json untracked; 22 new intents verified distinct vs bank, max Jaccard 0.189 < 0.25 claim holds, no 60-char prefix collisions).