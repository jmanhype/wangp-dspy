# PR #149 review thread 4 refutation

The six scripts under
`datasets/runs/provenance/lf004-operator-dogfood-20260920/commands/` are
byte-preserved historical evidence from the failed first LF004 execution. They
are intentionally immutable because their SHA-256 values are pinned by the
48-entry preservation manifest
`1b3865666017f3195e36b166a03c5966325e57fc9c1e47d6e322296c6ba73c50`.

The independent acceptor refuted the recommended remote-code refactor for this
story: changing those historical scripts would destroy evidence provenance and
is outside recovery-tooling rework. The active recovery uses
`run_recovery_once.sh` and `recover_once.py`, not those archived scripts. No
preserved script was modified.
