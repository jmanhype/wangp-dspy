# Mismatches — S2.5 Vertical Slice (WD-clms)

Run: 2026-08-28-104248 · branch feat/wd-clms-s25-vertical-slice · 3090 /tmp/s25/

## 1. timeline.json MISSING (referenced, not persisted)

- job.json meta declares: `"timeline": "/tmp/s25/timeline.json"`
- Actual state on 3090: file does not exist (`ls` confirms absent)
- MASTER_LOCK.md discipline: "timeline honestly authored out-of-repo (no whisper/pyannote in repo paths)"
- Interpretation: the diarization timeline for two_speakers.wav was produced outside the repo
  workflow and never copied to the expected path. The guide window (0.0–6.648s, SPEAKER_00)
  was used directly from the source audio without a persisted timeline artifact.
- Impact: run_record evidence chain has a dangling reference. Not a render failure — the
  correct guide slice was fed to the model — but the provenance record is incomplete.

## 2. attribution.txt MISSING (referenced, not persisted)

- job.json meta declares: `"attribution": "/tmp/s25/attribution.txt"`
- Actual state on 3090: file does not exist
- Same root cause as #1: out-of-repo authoring, artifact not persisted.
- Impact: speaker-to-line attribution for the dungeon scene dialogue is undocumented in the
  run artifacts. The script in job.json settings contains the full dialogue with <Picture 1>
  and <Audio 1> markers, so content is recoverable, but the formal attribution record is absent.

## 3. QC CONTENT FIDELITY DIVERGENCE (VLM misread suspected)

- qc_result.json summary describes: "a person in a kitchen setting, speaking and gesturing
  behind a wooden box"
- Intended scene (job.json script): "a dim stone dungeon cell lit by a single hanging oil lamp;
  an elderly woman in a worn shawl stands at the iron gate... a young man sits chained to the wall...
  a tall horned figure in a long dark coat"
- These are clearly different scenes. Two hypotheses:
  a) VLM misread the dungeon/lamp lighting as a kitchen (plausible — warm lamp light + wooden
     elements could be confused), OR
  b) The render drifted significantly from the master image reference.
- Score 7/10 PASSes the surreal threshold (4.5) either way, but this divergence means the
  automated QC did NOT verify that the intended characters and set were rendered.
- Action required: human review of the mp4 before treating this run as a validated vertical slice.

## 4. Render retries (5 log files)

- /tmp/s25/render.log through render5.log indicate multiple render attempts.
- Final successful output: render5.log shows "Task 1 completed", "Queue completed: 1/1 tasks
  in 14m 16s", output saved to the mp4 filename in run_record.
- Earlier logs (render.log–render4.log) likely contain failed or interrupted attempts.
  Not investigated further in this step; flagged for completeness.

## Summary

| # | Item | Severity | Blocks merge? |
|---|------|----------|---------------|
| 1 | timeline.json missing | Low (provenance gap) | No — flag in PR |
| 2 | attribution.txt missing | Low (provenance gap) | No — flag in PR |
| 3 | QC content fidelity divergence | Medium (unverified scene) | Yes — human review required |
| 4 | Multiple render attempts | Info | No |
