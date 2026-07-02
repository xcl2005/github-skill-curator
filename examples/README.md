# Examples

Use these examples to test whether GitHub Skill Curator is routing tasks clearly.

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
