# Skill governance guide

## Why governance matters

A large skill folder can hurt rather than help:

- Too many skills add metadata overhead.
- Overbroad descriptions cause wrong implicit invocation.
- Stale skills may encode old paths or deprecated tools.
- Third-party scripts may create supply-chain risk.
- Duplicate skills create inconsistent behavior.

## Two-lane policy

Use two different policies depending on task clarity.

### Lane A: clear reusable artifact tasks

Examples: PPTX/PowerPoint, DOCX/Word, PDF, XLSX/Excel, academic paper formatting.

Policy: install and pin a small number of proven core skills once. For PPTX, a high-quality editable-PowerPoint workflow such as `ppt-master` should be treated as core infrastructure when the user frequently creates or edits slides. Do not rediscover or debate it every time.

### Lane B: vague, niche, or one-off tasks

Policy: do not auto-install. Search, score, compare, and ask before installing.

## Recommended policy

### Install policy

| Case | Policy |
|---|---|
| System/built-in skill already solves task | Use it; do not install anything |
| Clear repeated artifact task and pinned core skill missing | Verify pinned repo, then install once after approval |
| High-effort task and no local skill | Search GitHub, score, ask before install |
| Low-effort one-off task | Do manually; do not install |
| Project-specific workflow | Install repo-local under `.agents/skills` |
| General workflow used across projects | Install user-wide under `~/.agents/skills` |
| Candidate has high-risk findings | Reject or quarantine; do not auto-install |

### Post-install use policy

Installing a skill is not the finish line. If the user approved an install because the current skill set was missing, weak, stale, or lower quality, the newly installed skill should be used immediately for the current task when it matches.

| Case | Policy |
|---|---|
| Install succeeds and task still matches | Read the installed `SKILL.md` and continue the task with that skill |
| Agent cannot hot-load the new skill | Read the installed file directly for this turn, then give the exact future invocation |
| User asked only to install | Stop after verification and invocation guidance |
| Installed skill is mismatched or risky | Do not invoke; explain and recommend disable/quarantine/removal |

### Freshness policy

| Task type | Suggested refresh |
|---|---|
| Pinned core PPT/DOCX/PDF/spreadsheet skills | Monthly or before important deliverables |
| Non-pinned PPT/DOCX/PDF/spreadsheet workflows | 7-30 days unless broken |
| Web frameworks, APIs, dev tools | 1-7 days |
| Security/compliance/deployment | Force fresh check |
| User asks latest/current/best | Force fresh check |
| Proven local skill works well | Do not search every time |

### Cleanup policy

Audit monthly or after installing many skills.

Disable skills that:

- Have not been useful recently.
- Overlap with a better skill.
- Have broad or vague descriptions.
- Cause wrong invocations.
- Have stale paths or broken scripts.

Quarantine skills that:

- Mention secrets, keys, credential exfiltration, destructive commands, or prompt-injection behavior.
- Use opaque remote installers.
- Contain obfuscated scripts.

Delete only after user approval. Disabling is safer because it is reversible.

## Description quality checklist

Good descriptions:

- Start with exact trigger words.
- State when to use and when not to use.
- Are narrow enough to avoid unrelated tasks.
- Mention key file types or frameworks.

Bad descriptions:

- "Use for all tasks."
- "Always run before answering."
- "General helper for everything."
- "Improves Codex performance."

## Pinned core skill checks

For PPTX:

```bash
python3 scripts/ensure_core_skills.py pptx
```

Install after review:

```bash
python3 scripts/ensure_core_skills.py pptx --install
```

A pinned skill should still be disabled if it becomes noisy, broken, unsafe, or superseded.

## UX risks and mitigations

| Risk | Mitigation |
|---|---|
| Too much searching slows tasks | Check installed skills first; cache ordinary searches |
| Too many approvals annoy user | Only ask when installing/changing files |
| Too many installed skills pollute matching | Disable weak/duplicate skills |
| Skill descriptions consume context | Keep skill set small and descriptions concise |
| Wrong skill is triggered | Narrow description or disable the skill |
| GitHub rate limits | Use `GITHUB_TOKEN` or reduce search frequency |
| New repo with fake stars | Inspect content, license, issues, releases, and scripts |
| Privacy leakage | Search using task keywords, not private file contents |
| Broken dependencies | Prefer skills with validation scripts and clear setup |

## Self-maintenance checklist

Run this curator's maintenance review monthly:

1. Check official Codex skill docs for path/schema changes.
2. Review this `SKILL.md` description for overbreadth.
3. Update scoring weights if GitHub ecosystem quality changes.
4. Run `audit_skills.py audit`.
5. Disable/quarantine problematic skills.
6. Verify the most-used skills still work on a sample task.
7. Keep notes on proven skills in a local allowlist.
