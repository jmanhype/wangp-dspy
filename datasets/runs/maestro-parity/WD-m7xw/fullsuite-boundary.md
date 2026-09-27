# Full-suite timeout boundary

The requested full pytest command was stopped locally after more than six
minutes. It had reached only about 13% while another developer story was
concurrently running its own full suite in a separate worktree. Only this
story's pytest process was interrupted; the unrelated WD-obkn run was left
alone.

The targeted Maestro-parity checker suite completed 78/78 tests with zero
failures before this attempt. Because WD-m7xw is already blocked before
inference, the concurrent full-suite timeout is not promoted to a delivery or
hardware verdict.
