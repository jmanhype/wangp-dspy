# 61 — fresh checkouts collide on remote render directory numbers

Status: OPEN; source repair staged for review.

## Evidence

The first fresh LF002 checkout allocated local `render-0000`. Its local pull
mirror was empty, so directory numbering knew nothing about the remote host’s
existing `/home/straughter/Wan2GP/acceptance/render-0000`. A stale remote
`remux.mp4` therefore occupied the mapped path.

Finding #60 detected the stale artifact by hash, but existence checks alone do
not repair the namespace collision. Independently numbered local directories
must not map to the same shared remote directory.

## Minimal fix

Assign every `WanGPAdapter` process a 12-hex render namespace and place its
render directories under:

```text
<output_dir>/worker-<namespace>/render-NNNN
```

Use the namespace for Ref2VA and FL2VA lanes. Existing local directories still
advance the sequence inside that namespace, preserving restart safety within a
checkout.

Two fresh checkouts—or two concurrent adapter processes—can both use
`render-0000` locally while mapping to distinct remote paths. The namespace is
validated as path-safe lowercase hexadecimal.

## Verification

Full suite after the repair:

```text
1341 tests
0 failures
0 errors
1 skipped
```

JUnit evidence:
`datasets/runs/provenance/lf002-golden-20260916/finding61-fullsuite.xml`.
