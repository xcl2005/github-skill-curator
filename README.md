<div align="center">

# GitHub Skill Curator

**Find better Codex Agent Skills without polluting your skill folder.**

<a href="https://github.com/xcl2005/github-skill-curator/stargazers"><img src="https://img.shields.io/github/stars/xcl2005/github-skill-curator?style=flat-square" alt="stars"></a>
<a href="https://github.com/xcl2005/github-skill-curator/network/members"><img src="https://img.shields.io/github/forks/xcl2005/github-skill-curator?style=flat-square" alt="forks"></a>
<a href="https://github.com/xcl2005/github-skill-curator/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="license"></a>
<img src="https://img.shields.io/badge/Codex-Agent%20Skill-111827?style=flat-square" alt="Codex Agent Skill">
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square" alt="Python 3.10+">

English · [简体中文](README_ZH.md)

[Install](#install) · [Why](#why) · [Control Flow](#control-flow) · [Commands](#commands) · [Safety](#safety) · [Examples](examples/)

</div>

## Why

Agent skills are powerful, but a messy skill folder makes Codex slower, noisier, and easier to misroute.

**GitHub Skill Curator** is a governance layer for skill discovery. It checks local skills first, searches GitHub only when useful, scores candidates, asks before installation, and helps audit stale or risky skills later.

## Highlights

| | Capability |
|---|---|
| 🔎 | Discover Codex / Claude Code style skills that contain `SKILL.md` |
| 🧭 | Route tasks to built-in, installed, or new skills with less guesswork |
| 🧪 | Score candidates by task fit, stars, recency, license, docs, and structure |
| 🛡️ | Flag broad prompts, secret access, destructive commands, and opaque installers |
| 🧹 | Audit, disable, quarantine, restore, and prune local skills |

## Control flow

The skill is intentionally more like a router than a single command. It decides whether Codex should use a built-in skill, use an installed skill, search GitHub, install a new skill, or refuse a risky candidate.

| Step | Decision | What happens |
|---:|---|---|
| 1 | Classify the task | Extract task terms such as `pptx`, `latex`, `resume`, `research`, `docx`, `pdf`, `testing`, or framework names. |
| 2 | Check local skills | Inspect user-wide, repo-local, and configured skill folders before searching online. |
| 3 | Decide freshness | Search only when the user asks for latest/best options, the task is high-value, or the local skill set is weak. |
| 4 | Choose discovery lane | Use pinned core checks, high-value task radar, curated index search, or generic GitHub search. |
| 5 | Score candidates | Compare relevance, stars, forks, update time, license, structure, docs, examples, and skill description quality. |
| 6 | Scan risk | Flag suspicious instructions, broad triggers, secret access, destructive commands, and opaque installers. |
| 7 | Ask before install | Show candidates and install only the selected skill folder after approval. |
| 8 | Maintain lifecycle | Audit, disable, quarantine, restore, or prune skills as the local environment changes. |

### Routing policy

| Situation | Default route |
|---|---|
| Built-in/system skill is enough | Use it immediately |
| Strong installed skill already matches | Use the installed skill |
| Repeated artifact workflow such as PPTX/DOCX/PDF/XLSX | Check pinned core skills |
| Academic writing, LaTeX, resumes, applications, reports | Run high-value task radar |
| User asks for latest/best/high-star skill | Force fresh GitHub discovery |
| Candidate is broad, stale, or risky | Reject, quarantine, or ask for explicit review |

### Discovery lanes

- **Pinned core lane:** stable reusable workflows such as editable PowerPoint generation.
- **High-value task radar:** academic writing, literature review, LaTeX, resumes, graduate applications, DOCX/PDF/XLSX reports.
- **Curated index lane:** awesome lists and curated collections used as discovery sources.
- **Generic GitHub lane:** fallback search for repositories with `SKILL.md`.
- **Lifecycle lane:** audit local skills and remove noise without deleting user work by default.

## Install

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/xcl2005/github-skill-curator.git ~/.agents/skills/github-skill-curator
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.agents\skills"
git clone https://github.com/xcl2005/github-skill-curator.git "$HOME\.agents\skills\github-skill-curator"
```

Restart Codex if the skill list does not refresh automatically.

## Commands

```bash
# Find skill candidates
python scripts/find_skills.py "PowerPoint PPTX editable presentation Codex skill" --top 8

# Search curated indexes first
python scripts/find_curated_indexes.py "AI presentation Codex skills" --top 8

# Classify a high-value task
python scripts/task_skill_radar.py "tailor my CS internship resume to this JD"

# Audit installed skills
python scripts/audit_skills.py audit --dest "$HOME/.agents/skills"
```

## Files worth reading

| File | Purpose |
|---|---|
| `SKILL.md` | Main operating policy and trigger description |
| `references/scoring.md` | Candidate scoring rubric |
| `references/governance.md` | Long-term skill lifecycle rules |
| `references/high_value_discovery_lanes.json` | Task radar configuration |
| `references/known_good_skills.json` | Pinned reusable skill candidates |
| `scripts/install_skill.py` | Reviewable skill-folder installer |

## Safety

This skill treats installation like a reviewable dependency decision.

It looks for:

- overbroad descriptions such as "use for all tasks";
- prompt-injection language;
- secret or credential access patterns;
- destructive shell commands;
- opaque `curl | sh` style installers;
- stale or overlapping skills.

It does not prove third-party code is safe. It makes the review visible before the install.

## Good for

- Codex users building a reusable skill stack.
- Developers looking for task-specific agent workflows.
- People who work with PPTX, DOCX, PDF, XLSX, LaTeX, resumes, research, reports, and codebase automation.
- Anyone who wants skill discovery without turning GitHub search into copy-paste roulette.

## Project quality checks

This repository includes a README quality gate:

```bash
python scripts/validate_readme_quality.py
```

The check blocks oversized README images, generated diagrams, stale hero assets, and missing install/safety sections.

## Repository layout

```text
.
|-- SKILL.md
|-- scripts/
|-- references/
|-- examples/
|-- agents/
`-- README.md
```

## Search keywords

Codex skills, Agent Skills, GitHub skill discovery, skill governance, skill installer, prompt safety, AI agents, Claude Code skills, Codex CLI, developer tools.

## License

MIT
