# 58 — the operator-perfect LF002 control was not a durable golden fixture

Status: CLOSED in PR #88 / commit `b560bcf`; fresh-clone reproduction was
ratified in PR #91 / commit `d811410`.

## Evidence

The operator reviewed the LF002 Archive of Rain two-cut native candidate and
replied verbatim: **“Perfect.”** The run used seed 905, two 56-frame native H3
cuts, real last-frame chaining, and no post-render audio replacement.

Its source artifacts and review evidence initially lived only in ignored pull
output and local review directories. The bundle also depended on locally
available image/WAV inputs that were not committed.

## Minimal fix

Publish the operator-accepted control as content-addressed provenance:

- both native cuts;
- assembled pair;
- chain frame;
- pinned LF002 SHA-256 canary;
- committed plate/reference images and prepared audio guides;
- a fresh-clone bundle that renders both cuts without completed-prefix reuse;
- reproduction instructions and exact expected hashes.

This establishes a second golden control after Devil’s Grandma `v3_pair`. It
does not claim that seed 905 is universally optimal for every future premise.

## Verification — 2026-09-16

A fresh checkout at `3faaf9a` reproduced the pinned cut 1, cut 2, chain frame,
and assembled pair hashes exactly. The operator reviewed the linked result and
replied verbatim: **“Perfect.”** The full suite passed with 1,339 tests, zero
failures/errors, and one skip. See
`datasets/runs/provenance/lf002-golden-20260916/fresh-clone-verification.json`.

## Resolution

The committed control includes the approved plate/reference images, prepared
guides, both native cuts, assembled pair, chain frame, bundle, canary, and
operator approval. The later strict single-ledger evidence at
`datasets/runs/provenance/lf002-golden-20260916/single-ledger-20260916/`
reproduces all pinned hashes with two `done` durable jobs and no prefix reuse.
The full suite at `9b70be1` passed 1380 tests with one intentional skip and no
failures.
