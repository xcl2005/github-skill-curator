# Install a PPT Skill

This example shows the intended path when a user wants a reusable PowerPoint or slide-generation skill, but does not know which repository is worth installing.

## User request

```text
Use $github-skill-curator to find a high-quality reusable PPTX skill for Codex, compare the options, and install only if the best candidate looks trustworthy.
```

## Expected curator behavior

1. Classify the task as a repeated artifact workflow: `pptx`, `powerpoint`, `slides`, `deck`.
2. Check installed Codex skills before searching GitHub.
3. Check pinned or curated PPT skill sources before broad search.
4. Score candidates by task fit, maintenance, license, examples, install shape, and safety signals.
5. Show the best candidate with risks and an explicit install command.
6. Install only after user approval.
7. After install, read the installed `SKILL.md` and print the next invocation.

## Useful commands

```bash
python scripts/ensure_core_skills.py pptx
python scripts/find_curated_indexes.py "AI presentation PowerPoint Codex skills" --top 8
python scripts/find_skills.py "PowerPoint PPTX editable presentation Agent Skill" --top 8
```

## What a good result looks like

```text
Recommendation: install <owner>/<repo>/<skill-path>
Why: strong PPTX focus, clear SKILL.md, examples, active maintenance, no high-risk install behavior found.
Risks: heuristic scan only; user should review upstream before high-stakes use.
Install: python scripts/install_skill.py owner/repo --skill-path path/to/skill --agent codex
Next use: $skill-name create an editable 12-slide deck from this outline
```

