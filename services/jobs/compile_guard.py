"""Compile-guard: real adapter + dspy compile context => typed raise.

Operator ruling 2: planning stays pure. predict/pipeline.Pipeline is a
dspy.Module (optimizable); a real (non-None) adapter firing GPU work
inside an optimizer rollout would burn 3090 hours during compile.

RELIABLE SIGNAL (read from dspy 3.3.1 source, verified live):
- Every stock optimizer (BootstrapFewShot/teleprompt bootstrap.py:188,
  bootstrap_trace.py:65, simba_utils.py:36/162, refine, best_of_n)
  wraps teacher rollouts in ``with dspy.context(trace=[])``.
- Outside any context, ``dspy.settings`` does not carry a thread-local
  override; inside one it does. ``dspy.context`` accepts ARBITRARY
  keys (verified: dspy.context(wangp_compile_guard=True) is visible
  inside, absent outside), so the optimizer harness in this repo also
  sets that explicit flag — belt and suspenders.

Detection = thread-local overrides non-empty (any dspy.context
rollout) AND the explicit flag. ``trace`` alone is not distinguishable
from default (default config also has trace=[]), so we check the
OVERRIDES dict, not the value.
"""
from __future__ import annotations


class CompileContextError(Exception):
    """A real adapter was invoked under dspy compile/optimization."""


def _thread_overrides() -> dict:
    try:
        from dspy.dsp.utils.settings import thread_local_overrides
        return dict(thread_local_overrides.get())
    except Exception:
        return {}


def in_compile_context() -> bool:
    overrides = _thread_overrides()
    if not overrides:
        return False
    # explicit flag set by our optimizer harness
    if overrides.get("wangp_compile_guard"):
        return True
    # any dspy.context rollout: stock optimizers always set `trace`
    return "trace" in overrides


def assert_not_compiling(*, adapter: str = "") -> None:
    if in_compile_context():
        what = f" ({adapter})" if adapter else ""
        raise CompileContextError(
            f"real adapter{what} present under dspy compile/optimization "
            "context — planning must stay pure; render execution belongs "
            "to services.jobs.executor, not the optimizable pipeline "
            "(operator ruling 2, jobs-preflight PR)")


__all__ = ["CompileContextError", "in_compile_context",
           "assert_not_compiling"]
