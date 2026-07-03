# Changelog

## 0.1.0 - 2026-07-03

- Added CI workflow and validation badge.
- Added `scripts/demo_curate.py` for deterministic offline curation demos without GitHub API access.
- Added deterministic local audit demo output and a decision policy reference for tier actions.
- Added fixed sample skill index fixture and generated demo curation report.
- Added `--dry-run` to `scripts/install_skill.py` so users can clone, validate, and safety-check a selected skill without copying files.
- Added `--dry-run --json` install plans for agent and CI consumers.
- Added shared `scripts/curation_model.py` so offline demos and live search share scoring, tiering, risk labels, and safety-first sorting.
- Added shared `scripts/risk_scan.py` and wired curation, install, and audit paths toward one risk vocabulary.
- Simplified `scripts/find_skills.py` so it no longer carries a second scoring model.
- Added risk scanner unit tests and CI assertions for unsafe installer dry-run JSON.
- Added `scripts/validate_skill.py` to validate SKILL frontmatter, manifest paths, README demo links, dry-run support, and risk-model coverage.
- Changed CI to regenerate the committed curation demo and fail when the generated output drifts.
- Added local fixture dry-run support and curation model unit tests.
- Fixed installer replacement behavior: existing skill folders now require `--force` before backup-and-replace.
- Added issue and pull request templates for skill recommendations, unsafe skill reports, scanner false positives, and docs improvements.
- Added filled demo outputs, an unsafe fixture skill, and a risk model with default review actions.
- Added README `Star this if` / `Not for` blocks to help users self-identify quickly.
- Added social preview copy guidance for GitHub repository sharing.
- Sharpened the repository positioning around Agent Skill discovery, ranking, installation, and safety review.
- Added demo examples for finding PPTX skills, auditing local skills, installing selected skills, and reviewing suspicious skills.
- Added `skill_manifest.yaml` for Codex / Claude Code audience, canonical paths, core functions, scoring dimensions, and safety scan patterns.
- Added README demo output shape, scoring model, safety scan examples, release badge, and built-in-tool relationship.
- Kept the default install policy review-first: show candidates and risks before installing third-party skills.
- Added README-ready framing for the project as an Agent Skills package manager plus safety reviewer.
