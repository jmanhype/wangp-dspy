# Plan: Controlled Experiment Director (hermes-a1005314)

1. RED: write `tests/test_experiment_director.py` covering all
   required behaviors; run → collection/import failure (module
   `experiments.director` absent). Save evidence.
2. GREEN: implement `experiments/director.py` + `experiments/__init__.py`
   (typed dataclasses, canonical hashing, pure planner, typed errors).
3. Verify: focused suite in clean env (`env -i PYTHONPATH= VIRTUAL_ENV=
   PATH=... python -m pytest tests/test_experiment_director.py -q`),
   then full suite same way; plus preservation check (no diff to
   training/metrics/evaluate/H3 adapter files).
4. Commit, push branch, open PR (do not merge).

Status: step 1 in progress.
