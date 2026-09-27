# WD-7fvx standing gates and owned diagnostics

## Terminal gates

- Checker: `uv run --frozen python scripts/verify_maestro_parity.py
  datasets/runs/maestro-parity/WD-7fvx` — exit `0`,
  `PASS wangp-dspy.maestro-parity-evidence/v1`, `owned_warnings=0`.
- Backlog lint: `pvg lint --backlog` — exit `0`; scanned `139`; `0` errors and
  `0` review findings.
- Targeted director tests: `uv run --frozen --extra dev pytest -q
  tests/test_director_capabilities.py` — exit `0`, `34 passed`.
- Full suite: clean-tree `/bin/bash`-precedence run of `uv run --frozen
  --extra dev pytest -q --junitxml=/tmp/WD-7fvx-full.xml` — exit `0`; parsed
  JUnit `tests=2108`, `errors=0`, `failures=0`, `skipped=1`.
- Release: `uv run --frozen --extra dev wgp release verify` — exit `0`;
  version/changelog/recipe/tree checks pass, `tag-ready=v0.1.0`,
  `tag_created=false`, `release=ready`.
- Protected parity: `git diff --exit-code 2b4714bf -- services/jobs/queue.py
  services/director/renderers/policy.py services/director/wiring.py
  services/jobs/preflight.py scripts/run_film.py` — exit `0`.
- Diff hygiene: `git diff --check` — exit `0`.

## DISCOVERED_BUG 1

```text
title: Homebrew Bash 5.2.37 heredoc can deadlock the LF004 launcher test
context: Two independent worktree full-suite runs blocked indefinitely in bash heredoc_write while executing tests/test_lf004_recovery_tooling.py::test_launcher_setup_is_root_relative_from_foreign_cwd. A process sample is retained in homebrew-bash-heredoc-sample.txt. The exact test passes with /bin/bash precedence (bash-precedence-probe.out), and the final clean-tree full suite passes with that environment. No test or toolchain dependency was changed in this story.
affected_files: tests/test_lf004_recovery_tooling.py; datasets/content_briefs/lf004-operator-dogfood-56f/run/run_recovery_once.sh
discovered_during: WD-7fvx
```

## DISCOVERED_BUG 2

```text
title: FastAPI testclient emits Starlette httpx deprecation warning
context: The clean full suite emits one StarletteDeprecationWarning from .venv/lib/python3.14/site-packages/fastapi/testclient.py:1. Dependency mutation is prohibited by WD-7fvx, so the warning is retained and reported rather than suppressed or upgraded.
affected_files: .venv/lib/python3.14/site-packages/fastapi/testclient.py
discovered_during: WD-7fvx
```
