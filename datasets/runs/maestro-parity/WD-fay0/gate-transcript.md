# WD-fay0 gate transcript

All commands ran locally/read-only unless a retrieval commit is named. No render host was contacted by WD-fay0.

## Checker WD-0zj8

Retrieval: `82f6c38570a818dd8dbd3e70baebd037459661b3`

Command: `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-0zj8`

```text
FAIL manifest: [Errno 2] No such file or directory: '/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-fay0/datasets/runs/maestro-parity/WD-0zj8/evidence.json'
```

exit=1

## Checker WD-2gyw

Retrieval: `82f6c38570a818dd8dbd3e70baebd037459661b3`

Command: `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-2gyw`

```text
PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/WD-2gyw
```

exit=0

## Checker WD-bxhc

Retrieval: `82f6c38570a818dd8dbd3e70baebd037459661b3`

Command: `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-bxhc`

```text
PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/WD-bxhc
```

exit=0

## Checker WD-cpow

Retrieval: `82f6c38570a818dd8dbd3e70baebd037459661b3`

Command: `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-cpow`

```text
PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/WD-cpow
```

exit=0

## Checker WD-m0r5

Retrieval: `82f6c38570a818dd8dbd3e70baebd037459661b3`

Command: `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-m0r5`

```text
PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/WD-m0r5
```

exit=0

## Checker WD-r81u

Retrieval: `82f6c38570a818dd8dbd3e70baebd037459661b3`

Command: `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-r81u`

```text
PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/WD-r81u
```

exit=0

## Checker WD-rous

Retrieval: `82f6c38570a818dd8dbd3e70baebd037459661b3`

Command: `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-rous`

```text
PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/WD-rous
```

exit=0

## Checker WD-dmf2

Retrieval: PM-recorded accepted commit `741a8bb27c4bec3be38667b090a03bedb00e3010` in a disposable detached worktree; it is absent from capstone base `82f6c38`.

Command: `python3 <detached-worktree>/scripts/verify_maestro_parity.py <detached-worktree>/datasets/runs/maestro-parity/WD-dmf2`

```text
FAIL objective_gate_results[21].verdict: must be pass
FAIL objective_gate_results[23].verdict: must be pass
FAIL objective_gate_results[24].verdict: must be pass
FAIL objective_gate_results[26].verdict: must be pass
FAIL objective_gate_results[27].verdict: must be pass
FAIL reviewer_verdict.decision: must be approved
```

exit=1

## Index validation

{"bundle_files": 4, "failing_bundles": 2, "lanes": 8, "matrix_rows": 208, "matrix_totals": {"not_applicable": 2, "pending_operator_consent": 6, "planned": 120, "unsupported": 34, "verified": 46}, "passing_bundles": 6, "result": "PASS"}

## Targeted fail-closed and clean-machine proofs

$ uv run --frozen --extra dev pytest -q tests/test_maestro_parity_evidence.py tests/test_readme_quickstart.py::test_clean_checkout_install_plan_then_typed_generation_refusal --junitxml=/tmp/WD-fay0-targeted.xml
Using CPython 3.14.4
Creating virtual environment at: .venv
   Building wangp-dspy @ file:///Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-fay0
      Built wangp-dspy @ file:///Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-fay0
Installed 84 packages in 254ms
.............................................................            [100%]
exit=0

JUnit counters:
{'tests': '61', 'errors': '0', 'failures': '0', 'skipped': '0', 'time': '24.693'}

## Backlog lint

$ pvg lint --backlog
[LINT] backlog: scanned 126 issues
[LINT] PASSED: 0 error(s), 0 review finding(s)
exit=0

## Full suite

$ timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-fay0-full.xml
........................................................................ [  3%]
........................................................................ [  6%]
........................................................................ [ 10%]
........................................................................ [ 13%]
........................................................................ [ 17%]
........................................................................ [ 20%]
........................................................................ [ 24%]
........................................................................ [ 27%]
........................................................................ [ 31%]
........................................................................ [ 34%]
........................................................................ [ 37%]
........................................................................ [ 41%]
.................................................s...................... [ 44%]
........................................................................ [ 48%]
........................................................................ [ 51%]
........................................................................ [ 55%]
........................................................................ [ 58%]
........................................................................ [ 62%]
........................................................................ [ 65%]
........................................................................ [ 69%]
..................................................F.F................... [ 72%]
........................................................................ [ 75%]
........................................................................ [ 79%]
........................................................................ [ 82%]
........................................................................ [ 86%]
........................................................................ [ 89%]
........................................................................ [ 93%]
........................................................................ [ 96%]
.....................................................................    [100%]
=================================== FAILURES ===================================
__________ test_clean_checkout_and_real_repository_are_release_ready ___________

tmp_path = PosixPath('/private/var/folders/7q/tx7m0tg12m5cgq7k8z8q2dzw0000gn/T/pytest-of-speed/pytest-19/test_clean_checkout_and_real_r0')

    def test_clean_checkout_and_real_repository_are_release_ready(tmp_path: Path) -> None:
        clone = _clone(tmp_path)
        guard = tmp_path / "success-human"
        human = _run_verified(clone, guard, None, "release", "verify")
        assert human.returncode == 0, human.stdout + human.stderr
        assert all(phrase in human.stdout for phrase in (
            "version=0.1.0", "check=version status=pass",
            "check=changelog status=pass", "check=recipe_schema status=pass",
            "check=tree status=pass", "tag-ready=v0.1.0", "tag_created=false",
            "no tag was created", "release=ready"))

        guard = tmp_path / "success-json"
        json_run = _run_verified(clone, guard, None, "release", "verify", "--json")
        assert json_run.returncode == 0, json_run.stdout + json_run.stderr
        payload = _release_payload(json_run)
        assert (payload["version"], payload["ready"], payload["tag"],
                payload["tag_created"]) == ("0.1.0", True, "v0.1.0", False)
        names = " ".join(check["name"] for check in payload["checks"])
        assert names == "version changelog recipe_schema tree"
        assert all(check["status"] == "pass" for check in payload["checks"])
        assert payload["checks"][2]["observed"] == SCHEMA

>       assert _git(ROOT, "status", "--short").stdout == ""
E       AssertionError: assert ' M datasets/...l-suite.txt\n' == ''
E
E         +  M datasets/runs/maestro-parity/WD-fay0/validate_index.py
E         + ?? datasets/runs/maestro-parity/WD-fay0/gate-transcripts/full-suite.txt

tests/test_release.py:170: AssertionError
__________ test_probe_fails_closed_when_import_shadowing_is_disabled ___________

tmp_path = PosixPath('/private/var/folders/7q/tx7m0tg12m5cgq7k8z8q2dzw0000gn/T/pytest-of-speed/pytest-19/test_probe_fails_closed_when_i0')

    def test_probe_fails_closed_when_import_shadowing_is_disabled(
            tmp_path: Path) -> None:
        clone = _clone(tmp_path)
        version = clone / "VERSION"
        version.write_text("0.2.0\n", encoding="utf-8")
        _commit(clone, version, "release-test: wrong-tree version")

        guard = tmp_path / "unshadowed"
        result, guard, ssh_log = _execute(
            clone, guard, "release", "verify", "--json",
            neutralise_imports=False, prefix_paths=(ROOT,))
>       assert result.returncode == 0, result.stdout + result.stderr
E       AssertionError: {"diagnostics":[{"code":"INPUT_INVALID","evidence_refs":["/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-fay0"],"metadata":{"source":"/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-fay0"},"next_command":"wgp release verify --json","observed":"tree is dirty: changed_path_count=2, untracked_path_count=1","remediation":"Fix the named field/path/configuration value, then rerun the same command.","severity":"error","title":"Typed input or configuration check failed","why":"The CLI rejected the request before an engine side effect."}],"release":{"checks":[{"expected":"0.1.0","message":null,"name":"version","observed":{"VERSION":"0.1.0","pyproject.toml":"0.1.0","wangp.__version__":"0.1.0"},"source":"VERSION, pyproject.toml, wangp/__init__.py","status":"pass"},{"expected":"0.1.0","message":null,"name":"changelog","observed":"0.1.0","source":"CHANGELOG.md","status":"pass"},{"expected":"wangp-dspy.render-recipe/v3","message":null,"name":"recipe_schema","observed":"wangp-dspy.render-recipe/v3","source":"wangp/recipe.py, datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921","status":"pass"},{"expected":"clean_tree=true changed_path_count=0 untracked_path_count=0","message":"tree is dirty: changed_path_count=2, untracked_path_count=1","name":"tree","observed":{"changed_path_count":2,"clean_tree":false,"commit_sha":"c6c4aa49c82bb09681be6f260c33b70c41476bae","dirty_tree":true,"status_sha256":"bca0c7d724396a219d37390a0c83fb3c5567f1dd3963f96e10cdc236da6b9533","tracked_diff_sha256":"42e40dc7d0ea5de54c2c4f5973a10762cc88cd7461bbe69280e2ba0c84015d3b","untracked_content_sha256":"f88642f92214e934f58f97e2db6d444f5b0f1cc5b4e48a7bfe721e3a21e16ec2","untracked_path_count":1},"source":"services.director.run_ledger.repository_identity","status":"failed"}],"guidance":"resolve failed checks before tagging v0.1.0; no tag was created","ready":false,"tag":"v0.1.0","tag_created":false,"version":"0.1.0"}}
E
E       assert 2 == 0
E        +  where 2 = CompletedProcess(args=['/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-fay0/.venv/bin/wgp', 'releas...tagging v0.1.0; no tag was created","ready":false,"tag":"v0.1.0","tag_created":false,"version":"0.1.0"}}\n', stderr='').returncode

tests/test_release.py:230: AssertionError
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-fay0/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_release.py::test_clean_checkout_and_real_repository_are_release_ready
FAILED tests/test_release.py::test_probe_fails_closed_when_import_shadowing_is_disabled
exit=1

JUnit counters:
{'tests': '2085', 'errors': '0', 'failures': '2', 'skipped': '1', 'time': '823.911'}

### Final clean-tree rerun

Command: `timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-fay0-full.xml`

```text
........................................................................ [  3%]
........................................................................ [  6%]
........................................................................ [ 10%]
........................................................................ [ 13%]
........................................................................ [ 17%]
........................................................................ [ 20%]
........................................................................ [ 24%]
........................................................................ [ 27%]
........................................................................ [ 31%]
........................................................................ [ 34%]
........................................................................ [ 37%]
........................................................................ [ 41%]
.................................................s...................... [ 44%]
........................................................................ [ 48%]
........................................................................ [ 51%]
........................................................................ [ 55%]
........................................................................ [ 58%]
........................................................................ [ 62%]
........................................................................ [ 65%]
........................................................................ [ 69%]
........................................................................ [ 72%]
........................................................................ [ 75%]
........................................................................ [ 79%]
........................................................................ [ 82%]
........................................................................ [ 86%]
........................................................................ [ 89%]
........................................................................ [ 93%]
........................................................................ [ 96%]
.....................................................................    [100%]
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-fay0/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
```

```text
```

Parsed JUnit counters: `{'tests': '2085', 'errors': '0', 'failures': '0', 'skipped': '1', 'time': '797.986'}`

exit=0

## Release verify

$ uv run --frozen --extra dev wgp release verify
version=0.1.0
check=version status=pass
check=changelog status=pass
check=recipe_schema status=pass
check=tree status=pass
tag-ready=v0.1.0
tag_created=false
v0.1.0 is tag-ready; no tag was created
release=ready
exit=0

## Pre-commit release sanity refusal

The first release attempt ran while the capstone bundle was intentionally untracked. It failed only `check=tree` (`release=not_ready`, exit 2); the final clean-tree result above is authoritative.


## Protected-file parity

$ git diff --exit-code 82f6c38 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py
exit=0

Story-base protected files are unchanged. Relative to `40f8c2b`, the sole accepted exception is `services/jobs/preflight.py` from accepted WD-e4r7; see the diagnostic transcript tail below.

```text
     rc, out, _err = _safe_probe(
-        host, ["nvidia-smi", "--query-compute-apps=pid,process_name",
-               "--format=csv,noheader"])
+        host, [
+            "nvidia-smi",
+            "--query-compute-apps=pid,used_memory,process_name",
+            "--format=csv,noheader",
+        ])
     if rc != 0:
         return PreflightCheck("gpu_state", False,
                               f"nvidia-smi rc={rc}")
-    m = _GPU_PROC_RE.search(out or "")
-    if m:
-        return PreflightCheck(
-            "gpu_state", False,
-            f"GPU busy: stale tenant pid {m.group(1)} "
-            f"({out.strip().splitlines()[0]})")
-    return PreflightCheck("gpu_state", True, "idle")
+    return _gpu_check_from_state(_parse_gpu_compute_apps(out))


 def _probe_qc(host, qc_url) -> PreflightCheck:
@@ -151,5 +208,6 @@ def run_preflight(host, *, models: Sequence[dict], min_free_gb: float,

 __all__ = [
     "PreflightCheck", "PreflightReport", "PreflightError",
+    "GpuComputeProcess", "GpuComputeState",
     "run_preflight", "PROBE_TIMEOUT_SECS",
 ]
exit=1
```

## Whitespace gate

$ git diff --check
exit=0
