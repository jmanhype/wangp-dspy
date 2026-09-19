# PLAN FRAGMENT — Thin Talker-Reasoner Bridge follow-up sequencing

Status: planning input only; do not execute until WD-dd81 is signed off and
follow-up stories exist. This story changes documentation only.

**Order of work.** Approve the contract, then build observability before any
live model or execution:

1. Implement fixture corpus and event serializer/hash checks first; no model,
   execution, memory, or credentials.
2. Add the deterministic/Jev-style three-route router and repeatable routing
   metrics; do not add safety labels or dynamic tools.
3. Add the fixed action validator and fail-closed rejection/provenance path;
   do not dispatch actions yet.
4. In parallel only after step 3, add non-release `Pipeline.forward()` and
   release-only `run_bundle()` consumer adapters. The release adapter must
   remain the sole release-quality route and must not modify existing seams.
5. Add consented Voxtral Small and PersonaPlex/Moshi adapters as shadow
   implementations, with latency/GPU/privacy measurements and no tool
   execution in either model.
6. Evaluate durable memory last, only after routing, false wakeups, latency,
   privacy, validation, and governed production gates pass twice.

**Stop conditions.** Reopen the contract for raw prompt/audio persistence,
arbitrary schemas, direct bridge execution, `run_bundle()` bypass, unconsented
network, or a cited signature that no longer matches source.
