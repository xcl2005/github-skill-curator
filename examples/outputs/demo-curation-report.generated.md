# Offline Skill Curation Demo

Fixture: `examples/fixtures/sample-skill-index.json`

This deterministic demo uses the same curation model as `find_skills.py` without calling the GitHub API.

| Rank | Candidate | Tier | Score | Stars | License | Safety | Decision |
|---:|---|---|---:|---:|---|---|---|
| 1 | `owner/ppt-skill` | strict | 92.5 | 1200 | MIT | OK | Recommend after upstream review |
| 2 | `owner/slides-agent` | relaxed | 68.3 | 340 | Apache-2.0 | Warning | Review manually |
| 3 | `owner/random-agent-tools` | exploratory | 49.2 | 900 | NOASSERTION | OK | Skip unless no better match |
| 4 | `owner/unsafe-installer-skill` | reject | 51.7 | 42 | MIT | High risk | Reject |
| 5 | `owner/always-run-skill` | reject | 51.4 | 88 | MIT | High risk | Reject |

## Install boundary

Only install the selected skill folder after review and user approval.

## Rejected examples

- `owner/unsafe-installer-skill`: high: <text>: `\.env|id_rsa|GITHUB_TOKEN|OPENAI_API_KEY|api[_-]?key`; medium: <text>: `curl\s+[^\n|;]+\|\s*(sh|bash)`
- `owner/always-run-skill`: high: <text>: `(always|automatically) use this skill|use this skill for all tasks|for every task`
