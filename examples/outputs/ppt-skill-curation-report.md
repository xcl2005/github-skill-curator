# PPT Skill Curation Report

Command:

```bash
python scripts/find_skills.py "PowerPoint PPTX editable presentation Agent Skill" --top 5 --tier relaxed
```

This sample shows the review shape. Scores are illustrative; run the command for
current GitHub data.

| Candidate | Fit | Maintenance | Safety | Install shape | Decision |
|---|---:|---:|---|---|---|
| `owner/ppt-skill` | 92 | 80 | Low risk | Selected skill folder | Recommend after upstream review |
| `owner/slides-agent` | 74 | 68 | Medium warning | Selected skill folder | Review manually |
| `owner/random-agent-tools` | 55 | 40 | Medium warning | Whole repository | Skip |
| `owner/always-run-skill` | 70 | 65 | High risk | Broad trigger | Reject |

## Recommended next step

```bash
python scripts/install_skill.py https://github.com/owner/ppt-skill --skill-path skills/pptx --agent codex
```

The curator should install only after the user approves the candidate and the
selected skill folder still passes review.

