# WD-qthq authorized execution boundary

- Boundary code: `EDITOR_HOST_EXECUTION_GUARD_HEAD_MISMATCH`
- Command: `bash /tmp/wd_qthq_execute_once.sh`
- Exit: `1`
- Observed repository HEAD: `04f5b7261db2d1e35596bc9761fc38734aafae89`
- Incorrect guard expectation: `04f5b7262d4153c2e58fc4c8f930a6ad30e7bf5b`
- Failure location: local wrapper head equality check, before `scripts/run_editor_host_export.py --execute`
- Host contact: none; `host-run/` was absent immediately afterward
- Transfer/queue/FFmpeg/retrieval: none
- Action: stop without retry, substitution, or delivery
