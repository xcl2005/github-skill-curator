# Security Policy

GitHub Skill Curator reviews other Agent Skills, so safety matters.

## Supported versions

The `main` branch is the active version.

## Reporting a vulnerability

Please open a GitHub issue if you find:

- secret or credential leakage;
- unsafe install behavior;
- destructive commands without clear user intent;
- prompt-injection patterns that try to override higher-priority instructions;
- scripts that hide behavior through obfuscation, encoding, or minification;
- broad skill descriptions that could hijack unrelated tasks.

Do not include real secrets, tokens, private files, browser profiles, or personal data in the report.

## Security model

This project provides heuristic scans and governance rules. It cannot prove a third-party skill is safe. It helps users review candidates before installation and keep their local skill folder auditable.
