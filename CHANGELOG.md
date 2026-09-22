# Changelog

All notable operator-facing changes to Wangp are documented in this file.
Detailed engineering decision records remain in [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-21

### Added

- Initial repository hygiene contract: README with an executed no-GPU quickstart, a machine-readable version, a contribution guide, third-party model notices, and a top-level [LICENSE](LICENSE).
- Typed Content Brief Gateway and `scripts/run_content_brief.py` for canonical no-GPU planning (`efcba33`, PR #146).
- Committed LF004 operator dogfood brief, plates, audio-guide map, plan, and review input (`26c7c67`, PR #147).
- Preserved LF003 four-cut full-gate chain evidence, including per-cut media, QC evidence, assembly, probes, and contact sheets (`5989810`).
- Preserved the governed LF004 56-frame recovery, its final film/provenance bundle, and review contact sheets (`3094b14`, PR #149).

### Fixed

- Content-brief preflight now requires audio streams and rejects a declared turn duration that differs from the measured guide before planning or GPU work (`4b99b3a`, PR #148).

### Changed

- Repository licence adopted as the [MIT licence](LICENSE), Copyright (c) 2026 Straughter Guthrie, by the owner's recorded decision on 2026-09-22; it replaces the source-available notice that granted no rights. The repository hygiene test now asserts the MIT grant, the holder, and the absence of the retired notice (WD-bosd).

### Security

- Plans and ledgers retain repository root, commit, dirty-tree, status, diff, and untracked-content provenance. Opaque untracked embedded repositories fail closed instead of being silently attributed.

[0.1.0]: https://github.com/jmanhype/wangp-dspy/releases
[efcba33]: https://github.com/jmanhype/wangp-dspy/commit/efcba335c634c09af61f6a47423783cab4ef97ba
[26c7c67]: https://github.com/jmanhype/wangp-dspy/commit/26c7c67c5a098dec6a8cf5351ee91b052c127c07
[5989810]: https://github.com/jmanhype/wangp-dspy/commit/598981045896f8ab6746c56868f60b20330017cf
[4b99b3a]: https://github.com/jmanhype/wangp-dspy/commit/4b99b3a98fd3764cfad6635ae0743e7a07585c96
[3094b14]: https://github.com/jmanhype/wangp-dspy/commit/3094b14b01eb41723f90e58f537f80cce847a5ad
