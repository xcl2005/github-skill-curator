# Unsafe Skill Audit Report

Command:

```bash
python scripts/audit_skills.py audit --dest examples/fixtures
```

Expected result shape:

| Skill | Status | Modified | Age | Risks | Notes |
|---|---|---|---:|---:|---|
| `unsafe-skill` | active | current | 0d | 2 | overbroad description; high: `scripts/install.sh`: `.env`; medium: `scripts/install.sh`: `curl ... \| sh` |

## Decision

Do not install this fixture.

## Safer action

- Reject it as a third-party candidate.
- Use it only as a local scanner fixture.
- If a real skill triggers these findings, ask for manual review before any install.
