# LF004 setup launcher deadlock root cause

## Reproduction

At merged base `7393245f59c7ff03f26493d722577e2481657299`, the undeselected
focused test was run under an outer 40-second timeout. Before the fix, the new
local launcher bound reported:

```text
AssertionError: LAUNCHER_TIMEOUT after 15s
assert 124 == 0
```

The launcher had already completed the real `verify.py` integration path (the
captured output included both approved replay hashes and `status: verified`),
so the hang was after verification and in command-record generation.

## Live process evidence

`sample` showed two Bash processes:

- Launcher parent: `execute_connection -> wait_for -> waitchld -> __wait4`
- Forked child: `execute_disk_command -> do_redirections ->
  do_redirection_internal -> heredoc_write -> write`

Descriptor inspection showed the child in `heredoc_write` held both ends of a
pipe (fds 3 and 4) while its stdin remained `/dev/null`. No Python reader had
been exec'd. This is a reader-less inline here-doc: the launcher is dependent on
Bash feeding its own pipe rather than on a directly executed program consuming a
file.

## Fix

Command-record generation moved to
`datasets/content_briefs/lf004-operator-dogfood-56f/run/write_command_record.py`.
The launcher now invokes that helper directly with explicit `--root` and
`--output` arguments. A successful helper invocation is observable through its
exit status, JSON on stdout, and the deterministic setup command record. The
launcher integration test starts Bash in a new process session, redirects output
to files (so descendants cannot hold pytest pipes), and terminates the complete
process group if the real invocation exceeds 15 seconds.
