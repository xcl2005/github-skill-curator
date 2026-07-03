# Examples

Use these examples to test whether GitHub Skill Curator feels like a real skill governance workflow instead of a command list.

## Scenario walkthroughs

- [Output: PPT skill curation report](outputs/ppt-skill-curation-report.md): a filled candidate review table.
- [Output: unsafe skill audit report](outputs/unsafe-skill-audit-report.md): a filled risk report from the unsafe fixture.
- [Fixture: unsafe skill](fixtures/unsafe-skill/SKILL.md): a deliberately unsafe local fixture for scanner demos.
- [Find a PPTX skill demo](find-pptx-skill-demo.md): show the ranked candidate table and install command shape.
- [Audit local skills demo](audit-local-skills-demo.md): inspect installed skills for noisy, stale, or risky behavior.
- [Install selected skill demo](install-selected-skill-demo.md): install one reviewed skill folder after approval.
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
