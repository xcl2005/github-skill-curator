# Audit Local Skills Demo

This demo shows the local hygiene path. It is useful when the agent starts invoking the wrong skill, or when the skill folder has accumulated old experiments.

## Command

```bash
python scripts/audit_skills.py audit --dest "$HOME/.agents/skills"
```

## What to look for

| Finding | Action |
|---|---|
| Overbroad `description` | Narrow the trigger or disable the skill |
| Duplicate domain skills | Keep the stronger one and disable the weaker one |
| Stale skill with no examples | Review before future use |
| Secret-access pattern | Quarantine until manually reviewed |
| Destructive command pattern | Do not invoke without explicit user intent |

## Follow-up commands

```bash
python scripts/audit_skills.py disable old-skill-name --dest "$HOME/.agents/skills"
python scripts/audit_skills.py quarantine suspicious-skill --dest "$HOME/.agents/skills"
python scripts/audit_skills.py restore old-skill-name --dest "$HOME/.agents/skills"
```

