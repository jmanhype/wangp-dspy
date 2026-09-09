# Finding #46 — visual-gate rejections discarded judge evidence

## Symptom

The cut-4 judge rejection was recorded only as the generic string
`visual gate failed: mouth/action/speaker attribution below pass bar`. The
per-component scores and the model's raw response were lost when the
`VisionJudgeError` was wrapped by the Ref2VA QC stage. That made it
impossible to tell a real continuity failure from a judge false negative
without re-running or visually guessing from the video.

## Fix (landed)

Vision judge errors now carry `scores` and `raw_response`; the Ref2VA wrapper
preserves both. ModelScope and local Qwen adapters return the exact response
text alongside normalized scores. The executor persists a
`vision_rejections` list on the clip before any seed retry/reset, including
seed, all component scores, raw response, and failure detail. The same
evidence is included in the immutable retry failure record. Successful
evidence also retains the raw response in the normal vision verdict.

## Acceptance

Regression tests cover low-score rejection propagation through
`run_vision_judge` and `run_ref2va_qc_stage`, adapter response capture for
content/reasoning responses, and durable executor persistence before a
reseed. Missing judge evidence remains fail-closed and is visible as an
empty evidence payload rather than silently disappearing.
