# Find a PPTX Skill Demo

This demo shows the public-facing search and scoring loop for a repeated PowerPoint workflow.

## Command

```bash
python scripts/find_skills.py "PowerPoint PPTX editable presentation Agent Skill" --top 5 --tier relaxed
```

## Output shape

The script prints Markdown so the result can be pasted into an issue, PR, or review note.

```text
# GitHub skill candidates (relaxed+)

| Rank | Repo | Tier | Score | Stars | Updated | License | Skill paths | Safety |
|---:|---|---|---:|---:|---|---|---|---|
| 1 | owner/ppt-skill | strict | 82.5 | 1200 | 2026-06-20 | MIT | skills/pptx/SKILL.md | OK |
| 2 | owner/slides-agent | relaxed | 68.0 | 340 | 2026-05-11 | Apache-2.0 | SKILL.md | medium warning |
```

## Review decision

Install only if the selected candidate has:

- a task-specific `SKILL.md`;
- clear license or reuse intent;
- recent enough maintenance;
- examples or validation guidance;
- no high-risk safety findings;
- a narrow trigger description.

