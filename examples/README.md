# Examples

Use these examples to test whether GitHub Skill Curator feels like a real skill governance workflow instead of a command list.

## Scenario walkthroughs

- [Install a PPT skill](install-ppt-skill.md): find, score, review, and install a reusable presentation skill only after approval.
- [Audit an unsafe skill](audit-unsafe-skill.md): inspect a suspicious skill before it can pollute a Codex or Claude Code setup.

## Find a specialist skill

```bash
python scripts/find_skills.py "markdown README documentation generator Codex skill" --top 8
```

## Find curated indexes first

```bash
python scripts/find_curated_indexes.py "AI presentation PowerPoint Codex skills" --top 8
```

## Run the high-value task radar

```bash
python scripts/task_skill_radar.py "write a literature review for a machine learning paper"
```

## Audit local skills

```bash
python scripts/audit_skills.py audit --dest "$HOME/.agents/skills"
```

## Disable a noisy skill

```bash
python scripts/audit_skills.py disable old-skill-name --dest "$HOME/.agents/skills"
```

## Suggested GitHub topics

Use these repository topics to make the project easier to discover:

`codex`, `codex-skills`, `agent-skills`, `skill-discovery`, `skill-governance`, `ai-agents`, `prompt-safety`, `github`, `python`, `developer-tools`
