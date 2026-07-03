# Offline Skill Curation Demo

Fixture: `examples/fixtures/sample-skill-index.json`

This deterministic demo mirrors the review shape of `find_skills.py` without calling the GitHub API.

| Rank | Candidate | Tier | Score | Stars | License | Safety | Decision |
|---:|---|---|---:|---:|---|---|---|
| 1 | `owner/ppt-skill` | strict | 82.5 | 1200 | MIT | OK | Recommend after upstream review |
| 2 | `owner/always-run-skill` | reject | 70.0 | 88 | MIT | High risk | Reject |
| 3 | `owner/slides-agent` | relaxed | 68.0 | 340 | Apache-2.0 | Warning | Review manually |
| 4 | `owner/unsafe-installer-skill` | reject | 61.0 | 42 | MIT | High risk | Reject |
| 5 | `owner/random-agent-tools` | exploratory | 55.0 | 900 | NOASSERTION | Warning | Skip |

## Install boundary

Only install the selected skill folder after review and user approval.

## Rejected examples

- `owner/always-run-skill`: high: overbroad trigger
- `owner/unsafe-installer-skill`: high: secret access; medium: curl pipe shell

