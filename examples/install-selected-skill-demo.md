# Install Selected Skill Demo

This demo shows the install step after a candidate has already been reviewed.

## Command

```bash
python scripts/install_skill.py https://github.com/owner/repo --skill-path skills/example-skill --agent codex
```

## Expected behavior

1. Fetch the selected repository.
2. Copy only the selected skill folder.
3. Preserve a backup if a destination already exists.
4. Print the installed path.
5. Print the exact next Codex / Claude Code invocation.

## Good result shape

```text
Installed example-skill to ~/.agents/skills/example-skill
Codex: Use $example-skill to ...
Claude Code: /example-skill ...
```

