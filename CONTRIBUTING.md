# Contributing

Thanks for helping improve GitHub Skill Curator.

This project is about reliable Codex Agent Skill discovery and governance. Good contributions make skill selection more useful, more transparent, and safer.

## Useful contribution types

- Add high-quality known-good skill candidates.
- Improve scoring rules for task fit, maintenance, license, and safety.
- Add safer detection patterns for risky skill files.
- Improve README examples and installation guidance.
- Fix Windows, macOS, or Linux path behavior.
- Add tests or sample outputs for the Python scripts.

## Contribution principles

- Keep skill descriptions narrow and specific.
- Do not add broad "use for everything" prompts.
- Do not add opaque install scripts.
- Do not include credentials, tokens, browser profiles, `.env` files, or private logs.
- Prefer reviewable JSON, Markdown, and Python code over hidden magic.

## Before opening a pull request

Run the basic script checks:

```bash
python -m py_compile scripts/*.py
python scripts/audit_skills.py audit --dest "$HOME/.agents/skills"
```

For new discovery logic, include:

- the task query used;
- the selected candidate repositories;
- why they match;
- safety notes;
- any false positives or false negatives you noticed.

## Good pull request titles

- `Add curated index support for documentation skills`
- `Improve risk scan for opaque shell installers`
- `Document Windows install path`
- `Add known-good academic writing skill candidate`
