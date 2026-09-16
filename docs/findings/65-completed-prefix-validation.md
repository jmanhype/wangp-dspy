# 65 — completed-prefix reuse was not dependency- and QC-complete

Status: CLOSED in PR #96 / commit `c7a910b`; dependency- and QC-complete
completed-prefix validation is on `main`.

## Evidence

Qodo review of PR #86 found three gaps:

1. every post-prefix cut depended directly on the adopted prefix, not its
   immediate predecessor;
2. a source clip without usable QC evidence could be inserted as completed;
3. an empty `plate_paths` sequence escaped planning as `IndexError`.

With three or more cuts, the first issue could leave later cuts admissible
after their immediate predecessor failed, with unresolved chain placeholders.

## Minimal fix

- chain each successor to the immediately preceding job;
- require source job and source clip state `done`;
- require an accepted workflow QC verdict and usable evidence;
- require completed queue clips to carry verdict/evidence-path fields;
- reject empty plate input with typed `DirectorRunError`.

QC evidence may be a path to an existing evidence file or the embedded Ref2VA
QC document; empty placeholders are rejected.

## Resolution

The acceptance runner, drain path, DirectorRun planner, and durable queue now
enforce immediate-predecessor dependencies, completed source state, usable QC
evidence, and typed rejection of empty plate input. Regression coverage is in
`tests/test_director_run.py` and `tests/test_run_acceptance.py`. The full
suite at `9b70be1` passed 1380 tests with one intentional skip and no
failures.
