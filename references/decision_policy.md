# Decision Policy

Use candidate decisions as review guidance, not as proof that a third-party skill is safe.

| Tier | Default decision | Meaning |
|---|---|---|
| `strict` | Recommend after upstream review | Strong task fit, usable structure, acceptable maintenance, and no high-risk scanner findings. Still read the upstream `SKILL.md` before install/use. |
| `relaxed` | Review manually before install | Possible fit, but weaker evidence, lower structure confidence, lower popularity, stale maintenance, or non-blocking warnings require manual review. |
| `exploratory` | Learn from it, usually do not install | Useful for ideas, examples, or ecosystem mapping, but not strong enough for default installation. |
| `reject` | Do not install | High-risk findings, archived repository, missing fit, broken structure, or other blocking concerns. Explain the rejection instead of installing. |

## Required Actions

Before recommending installation:

1. Check built-in and already-installed skills first.
2. Score candidates through `scripts/curation_model.py` or `scripts/find_skills.py`.
3. Run or emulate `scripts/risk_scan.py` on the selected `SKILL.md` and bundled scripts.
4. Use `scripts/install_skill.py --dry-run --json` before copying files.
5. Read the installed `SKILL.md` before using it for the current task.

Do not treat stars as approval. A low-star candidate can be reviewed when task fit and structure are strong. A high-star candidate must still be rejected when high-risk findings are present.
