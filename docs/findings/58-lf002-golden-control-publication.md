# 58 — the operator-perfect LF002 control was not a durable golden fixture

Status: OPEN; source repair staged for review.

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
