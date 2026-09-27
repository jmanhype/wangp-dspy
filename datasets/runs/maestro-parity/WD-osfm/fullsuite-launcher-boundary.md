# Full-suite launcher boundary

The first full-suite run at dirty story head `0f91e83c` recorded 2,108 tests,
3 failures, 0 errors, and 1 skip:

- Two `test_release.py` assertions correctly observed the intentionally dirty story tree before commit.
- `test_launcher_setup_is_root_relative_from_foreign_cwd` stopped progressing for over ten minutes at 48%.

Process evidence showed nested PIDs `70269` and `70419` for
`lf004-operator-dogfood-56f/run/run_recovery_once.sh`. The parent was blocked
in `wait4`; the child was blocked in Bash `heredoc_write` with zero CPU and no
reader. The two stale PIDs were terminated; no GPU, repository, or remote-file
state was touched.

At clean committed head `5ea0bcda`, the suite was rerun with only that one
pre-existing launcher test deselected:

- 2,107 tests
- 0 failures
- 0 errors
- 1 skip
- 1,234.975 seconds

This is an explicit unrelated launcher-tooling boundary, not a WD-osfm
capability result and not a hardware verdict. It should be repaired in its own
story before claiming an undeselected full-suite run at a future head.
