# WD-bw0h authorized attempt stopped

The one authorized clean-generated command ran at producing commit
`eddff6bc8bf77fb7fa8d711a44beacbb314e4b2c`. It created the isolated
HOME/cache/tool/pull workspace, cloned that exact commit, recorded a clean
tree, and synced the disposable checkout. The recorder then failed while
serializing local workspace identity because a `PosixPath` reached JSON.

The command exited 4 with `UNEXPECTED_GENERATED_PROOF_FAILURE`. In accordance
with the operator boundary, it was not retried and no existing media was
substituted. The proof directory has no `remote-scripts`, `storage`,
`preflight`, `queue.db`, `host-logs`, `outputs`, or `checker` paths;
therefore SSH, model preflight, storage relocation, queue admission, Wan2GP
execution, and artifact generation were not reached. No model bytes were
downloaded or changed, no provider spend or training occurred, and no render
was attempted. The isolated package install downloaded locked Python
dependencies; that is distinct from model-download bytes.
