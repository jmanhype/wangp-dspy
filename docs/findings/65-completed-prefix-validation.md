# 65 — completed-prefix reuse was not dependency- and QC-complete

Status: OPEN; source repair staged for review.

## Evidence

Qodo review of PR #86 found three gaps:

1. every post-prefix cut depended directly on the adopted prefix, not its
   immediate predecessor;
2. a source clip without usable QC evidence could be inserted as completed;
3. an empty `plate_paths` sequence escaped planning as `IndexError`.

With three or more cuts, the first issue could leave later cuts admissible
after their immediate predecessor failed, with unresolved chain placeholders.

## Minimal fix

- chain each successor to the immediately preceding job;
- require source job and source clip state `done`;
- require an accepted workflow QC verdict and usable evidence;
- require completed queue clips to carry verdict/evidence-path fields;
- reject empty plate input with typed `DirectorRunError`.

QC evidence may be a path to an existing evidence file or the embedded Ref2VA
QC document; empty placeholders are rejected.
