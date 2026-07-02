# Core reusable task policy

This policy is for clear, repeated artifact workflows where a good specialized skill reliably improves quality and saves time.

Examples:

- PPTX / PowerPoint / slide decks
- DOCX / Word document formatting
- PDF rendering, inspection, extraction, annotation
- XLSX / Excel / spreadsheet cleaning and reporting
- Academic paper formatting and journal-style layout

## Main idea

For these tasks, do not treat skill discovery as optional every time. Maintain a small pinned allowlist of proven, high-quality skills and make sure they are installed once.

The right behavior is:

1. Check whether the pinned/core skill is installed.
2. If missing, verify the current upstream repository quickly.
3. Install the pinned skill if it still passes safety and provenance checks.
4. After installation, read the installed `SKILL.md` and use the installed skill for the current task when it matches.
5. Recheck upstream periodically, not on every task.

This is different from vague or one-off tasks. For vague tasks, conservative search and user confirmation are still preferred.

## PPTX / PowerPoint lane

For PPTX work, treat high-quality editable-PPT workflows as core infrastructure.

Recommended order:

1. Use Codex's built-in/system `$slides` skill if it is already available and sufficient for the requested job.
2. If the user values high-quality, native editable decks, template following, richer presentation workflows, or repeatedly asks for PPT creation/editing, ensure a proven third-party PPTX skill such as `ppt-master` is installed.
3. Keep both if they serve different purposes, but avoid installing multiple overlapping PPTX skills unless each has a clear role.

`ppt-master` is a good example of a pinned candidate because it is highly task-specific, MIT licensed, actively maintained, has examples/docs, and has a very strong GitHub popularity signal. Still review safety warnings before first installation or major updates.

## Core install threshold

A pinned core skill can be installed aggressively when all are true:

- The task domain is clear and repeated.
- The repo or skill is on the local allowlist.
- The repo is not archived.
- It has a clear license or reuse terms.
- It has no high-risk safety findings.
- The skill description is not overbroad.
- It solves a real artifact-quality problem better than generic prompting.

## What not to do

Do not keep searching for alternative skills on every PPT task once a known good skill is installed and working.

Do not install five PPT skills just because they all look useful. Too many overlapping skills can cause wrong invocation and waste context.

Do not auto-install unknown low-star skills for broad tasks. Use the normal strict/relaxed/exploratory ladder instead.

## Maintenance cadence

- Check pinned core skills monthly or when they break.
- Force-refresh before important deliverables if quality matters.
- Update the local allowlist when a clearly better skill emerges.
- Disable duplicate or weaker skills.
