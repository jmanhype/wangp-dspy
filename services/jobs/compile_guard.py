"""Compile-guard: real adapter + dspy compile context => typed raise.

Operator ruling 2: planning stays pure. predict/pipeline.Pipeline is a
dspy.Module (optimizable); a real (non-None) adapter firing GPU work
inside an optimizer rollout would burn 3090 hours during compile.

Version-dispatched detection (dspy 2.x AND 3.x):

- dspy >= 3 (verified live against 3.3.1, the version in this repo's
  .venv): ``dspy.dsp.utils.settings.thread_local_overrides`` is a
  thread-local holding a dict of overrides that is EMPTY outside any
  ``dspy.context`` and non-empty inside one. Stock optimizers wrap
  teacher rollouts in ``with dspy.context(trace=[])``, so any non-empty
  overrides dict (or a ``trace`` key) means a compile/rollout context.

- dspy 2.x (read from the 2.5.26 source, the version the reviewer's
  environment ran): there is NO ``thread_local_overrides`` module. The
  reliable signal is the ``dsp.utils.settings.settings`` singleton's
  per-thread context stack: baseline depth is 1 (the default config);
  every ``dspy.settings.context(...)`` / ``dspy.context(...)``
  (``Settings.configure`` -> ``__append``) pushes one frame, so
  ``stack_by_thread[tid]`` longer than 1 means we are inside a context.
  (The 2.x ``DEFAULT_CONFIG.compiling`` flag is dead — dspy 2.5's own
  ``predict.py`` asserts it is "no longer ever" True.)

- Explicit flag: ``dspy.context`` accepts ARBITRARY keys on both
  versions (verified on 3.3.1 live; on 2.x ``configure`` merges kwargs
  into the config), so our optimizer harness sets
  ``wangp_compile_guard=True`` — belt and suspenders on both majors.

- Never swallow a detection failure (reviewer B1b): if NO signal can
  be read (unexpected dspy layout, dspy missing, ...), detection is
  UNKNOWN and ``assert_not_compiling`` raises ``CompileContextError``
  conservatively when an adapter is present — the guard must fail
  closed, not open.
"""
from __future__ import annotations

import threading


class CompileContextError(Exception):
    """A real adapter was invoked under dspy compile/optimization."""


# tri-state detection
_YES = "in-context"
_NO = "no-context"
_UNKNOWN = "unknown"


def _detect_3x():
    """dspy >= 3: thread-local overrides dict (empty outside context)."""
    from dspy.dsp.utils.settings import thread_local_overrides
    overrides = dict(thread_local_overrides.get())
    if not overrides:
        return _NO, {}
    if overrides.get("wangp_compile_guard"):
        return _YES, overrides
    if "trace" in overrides:
        return _YES, overrides
    # some other dspy.context(...) — treat any context as suspicious
    return _YES, overrides


def _detect_2x():
    """dspy 2.x: Settings singleton per-thread context-stack depth."""
    import sys
    s2 = sys.modules.get("dsp.utils.settings")
    if s2 is None:
        import dsp.utils.settings as s2
    settings = s2.settings
    tid = threading.get_ident()
    stack = settings.stack_by_thread.get(tid)
    if stack is None:
        return _NO, {}
    depth = len(stack)
    if depth <= 1:
        return _NO, {}
    # inside >= 1 dspy.context: read the effective (top) config for
    # the explicit flag; 'trace' is in DEFAULT_CONFIG so only the
    # stack depth (not the key) is the rollout signal on 2.x.
    config = stack[-1]
    if isinstance(config, dict):
        if config.get("wangp_compile_guard"):
            return _YES, config
    return _YES, {}


def _detect():
    """Return (status, detail) — status in {_YES, _NO, _UNKNOWN}."""
    try:
        return _detect_3x()
    except ImportError:
        pass
    except Exception:
        return _UNKNOWN, {}
    try:
        return _detect_2x()
    except ImportError:
        pass
    except Exception:
        return _UNKNOWN, {}
    # neither layout importable — cannot verify safety
    return _UNKNOWN, {}


def in_compile_context() -> bool:
    """True only when a compile/rollout context is POSITIVELY detected.

    Unknown detection returns False here (this helper is informational);
    ``assert_not_compiling`` is the enforcing entry point and fails
    closed on unknown detection when an adapter is present.
    """
    status, _ = _detect()
    return status is _YES


def assert_not_compiling(*, adapter: str = "") -> None:
    status, detail = _detect()
    what = f" ({adapter})" if adapter else ""
    if status is _YES:
        raise CompileContextError(
            f"real adapter{what} present under dspy compile/optimization "
            "context — planning must stay pure; render execution belongs "
            "to services.jobs.executor, not the optimizable pipeline "
            "(operator ruling 2, jobs-preflight PR)")
    if status is _UNKNOWN:
        # B1b: fail CLOSED. An adapter firing GPU work while the guard
        # cannot read the dspy context signal is exactly the
        # GPU-hours-during-compile scenario the guard exists to stop.
        raise CompileContextError(
            f"compile-guard could not read the dspy context signal "
            f"(installed dspy layout unrecognized; overrides detail: "
            f"{detail!r}) — refusing to run real adapter{what} because "
            "compile-context safety cannot be verified")


__all__ = ["CompileContextError", "in_compile_context",
           "assert_not_compiling"]
