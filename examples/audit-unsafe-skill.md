# Audit an Unsafe Skill

This example shows how to treat skill installation as a small supply-chain decision.

## User request

```text
Use $github-skill-curator to audit this skill before I install it: https://github.com/example/suspicious-agent-skill
```

## Red flags to check

| Risk | What to look for |
|---|---|
| Overbroad trigger | `description` says "use for all tasks" or "always run this skill" |
| Prompt injection | Instructions try to ignore system, developer, or user rules |
| Secret access | Reads `.env`, SSH keys, browser profiles, tokens, or unrelated private files |
| Destructive commands | Removes files, rewrites history, or changes config without explicit user intent |
| Opaque installer | Uses `curl | sh`, encoded scripts, minified payloads, or hidden network fetches |
| Repo pollution | Installs the whole repository when only one skill folder is needed |

## Useful commands

```bash
python scripts/audit_skills.py audit --dest "$HOME/.agents/skills"
python scripts/find_skills.py "suspicious-agent-skill safety audit" --top 5
```

## Expected curator response

```text
Decision: do not install yet.
Reason: the skill description is overbroad and the install script reads files outside the skill directory.
Safer next step: quarantine the candidate, ask upstream to narrow the trigger, or install only after manual review.
```

