"""Compile-guard tests: real adapter + compile context => typed raise."""
import dspy
import pytest

from predict.pipeline import Pipeline, PipelineStageError
from services.jobs.compile_guard import (
    CompileContextError,
    assert_not_compiling,
    in_compile_context,
)
from services.jobs.queue import JobQueue


class BoomDirector:
    def __init__(self):
        self.called = False

    def __call__(self, intent, **kw):
        self.called = True
        raise AssertionError("director must not run in this test")


def test_detects_dspy_trace_context():
    assert not in_compile_context()
    with dspy.context(trace=[]):
        assert in_compile_context()
    assert not in_compile_context()


def test_detects_explicit_guard_flag():
    with dspy.context(wangp_compile_guard=True):
        assert in_compile_context()


def test_assert_not_compiling_raises_typed_inside_context():
    with dspy.context(trace=[]):
        with pytest.raises(CompileContextError):
            assert_not_compiling(adapter="WanGPAdapter(3090)")


def test_assert_not_compiling_noop_outside_context():
    assert_not_compiling(adapter="WanGPAdapter(3090)")


def test_pipeline_forward_raises_with_real_adapter_under_compile_context():
    pipe = Pipeline(genre="test",
                    director=BoomDirector(),
                    adapter=object())  # any non-None adapter
    with dspy.context(trace=[]):
        with pytest.raises(CompileContextError):
            pipe.forward("a hood two-shot dialogue")
    # director never ran — the guard fires FIRST
    assert not pipe.director.called


def test_pipeline_forward_allows_real_adapter_outside_compile():
    class NoneDirector:
        def __call__(self, intent, **kw):
            class R:
                brief = None
            return R()

    # adapter present but compile context absent -> no guard raise
    # (stage will fail later for other reasons; that's fine, the
    # guard specifically must NOT fire)
    pipe = Pipeline(genre="test", director=NoneDirector(),
                    adapter=object())
    try:
        pipe.forward("intent")
    except CompileContextError:
        pytest.fail("compile guard fired outside compile context")
    except Exception:
        pass  # unrelated stage failure is acceptable here
