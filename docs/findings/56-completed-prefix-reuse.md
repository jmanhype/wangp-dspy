# 56 — completed-prefix reuse lacks a repo-owned contract

Status: OPEN; source repair staged for review.

## Evidence

The operator-accepted LF002 two-cut film reused a verified seed-905 cut 1 and
rendered only cut 2. Before this repair, the generic acceptance runner could
only submit an entire new plan, so reusing an accepted cut required either a
second unnecessary GPU render or an off-road helper.

## Minimal fix

Add a `completed_prefix` bundle object that names the source database, job,
clip index, and expected native SHA-256. The runner:

1. reads the source durable job and requires state `done`;
2. compares effective renderer fingerprints between old and planned clips;
3. requires matching native raw/final hashes and `native_h3` runtime evidence;
4. inserts a completed synthetic job with real log/video/QC paths;
5. submits only the dependent cuts;
6. materializes the chain frame through the existing repo seam;
7. records source-job provenance in the new queue.

The prefix is evidence reuse, not artifact adoption by filename.
