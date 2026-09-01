# Maestro Director Architecture Port

## Attribution

The Director architecture ported here is pattern-matched from
**Maestro** (`/home/straughter/Maestro/app/services/director/` on the
3090), which is licensed under **WanGP Non-Commercial Evaluation 1.1**.
No Maestro source files were vendored or copied verbatim: we read the
code for the architectural pattern and wrote our own implementation
against this repo's verified H3-Ref2VA envelope. A checker test
(`tests/test_no_maestro_verbatim.py`) enforces this continuously — it
compares our tree against a checked-in excerpt corpus of the Maestro
sources (`tests/fixtures/maestro_reference/`) and fails on any shared
verbatim run of >20 non-trivial lines.

## Pattern mapping

| Maestro | wangp-dspy | What changed |
|---|---|---|
| `director/schema.py` (AssetRef, SubjectRef, ShotPlan, ProductionPlan, CharacterProfile, DialogueBeat, CameraPlan, AudioPlan) | `services/director/schema.py` | Reimplemented. Our ShotPlan is flatter: one start image ref (master plate) + one audio guide ref `{path, duration_s}` matching the verified Ref2VA job shape. Frozen dataclasses with typed `SchemaError`; JSON round-trip via `to_json/from_json`. |
| `planners/short_film.py` (multi-pass LLM planner with JSON-schema-constrained pass 2) | `services/director/planners/short_film.py` | Reimplemented as a strict 3-pass planner: pass 1 screenplay beats (creative), pass 2 structured shot breakdown to ShotPlan JSON, pass 3 polish notes. The LLM is a **required injected callable** `llm(pass_tag, system, user) -> str` — no hard-coded endpoint (Maestro binds to llama-server; we keep that at the call site, GLM-5.3 when used live). Deterministic given the same LLM responses. Plate/guide paths are resolved from trusted local mappings, never from LLM output. |
| `renderers/base.py` + 6 LTX renderers (two-pass: deterministic draft + LLM refine) | `services/director/renderers/h3_ref2va.py` + `policy.py` | **The key adaptation.** Instead of LTX prompt strings, the renderer emits our verified gated job config. The "two passes" become (a) deterministic prompt assembly via `predict.subject_prompt.build_subject_prompt` (PR #52 — reused, not duplicated) and (b) typed policy enforcement (see below). No LLM refine pass — our prompt format is fully deterministic. |
| `director/orchestrator.py` (DirectorOrchestrator, DirectorFlags) | `services/director/orchestrator.py` | Reimplemented: ProductionPlan in → validated job-config dicts + per-shot evidence manifests (plan/job/prompt/guide/plate sha256 + lineage) out. Emission only — no GPU, no render execution, no subprocess. |
| `director/policies.py` (prompt hygiene rules, anti-pattern detection) | `services/director/renderers/policy.py` | Replaced wholesale: our policies encode the **render envelope**, not prompt hygiene — that job already lives in `predict/` gates. |

## Renderer policy (the value of the port)

Typed rejections, checked in order in `h3_ref2va.py`:

1. **GridError** — shot duration must be on the 17k+5 second grid
   (5/22/39/56/73/90/107/124/141...s). The 4s Ref2VA floor sits below
   the first grid point, so 5s is the shortest usable shot.
2. **GuideDurationError** — guide duration must equal shot duration
   exactly; the guide is sliced to the shot duration
   (`guide_slice: {start_s: 0, end_s: duration, duration_s: duration}`).
3. **FacingError** — the speaker's master plate must exist on disk and
   be camera-facing, asserted by a `<plate>.plate.json` sidecar
   (`{"facing": "camera"}`) or the CharacterProfile
   `facing_requirement`. Profile-facing or missing plates are rejected
   (lip-sync identity prior — Wet Reckless).
4. **FramingError** — wide/medium-wide framing and bright/natural
   lighting required (grandma-perfect recipe).

Emitted job config additionally pins `audio_prompt_type: "A"`,
`video_prompt_type: "I"`, `multi_prompts_gen_type: "FG"`, `fps: 24`,
grid frame count, and the single `image_refs` entry.

## Adapted vs reimplemented

- **Adapted (concept kept, mechanics ours):** the plan → render → emit
  pipeline shape; multi-pass planning with structured pass-2 output;
  typed policy rejection at render time (Maestro returns error lists,
  we raise typed exceptions); per-shot evidence/manifest emission.
- **Reimplemented from scratch:** all dataclasses (ours are frozen and
  round-trip-JSON), the planner (LLM injection contract is ours),
  the renderer output format (our gated job config, our prompt
  builder), the orchestrator (hash lineage is ours).
- **Deliberately dropped:** Maestro's LLM prompt-polish pass (our
  prompt format is deterministic), safety/NSFW scanning (owned
  upstream in `predict/` gates), guide_loader/nsfw_guidance
  (audio data plane lives in `predict/audio_dataplane.py`).

## Purity

`services/director/` imports only from `services.` and `predict.` —
never from `training/`, `metrics/`, or `evaluate/`
(`tests/test_director_port.py::test_no_training_metrics_evaluate_imports`).
