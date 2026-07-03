<div align="center">

<p>
  <img src="./assets/hero.png" alt="GitHub Skill Curator" width="900">
</p>

# GitHub Skill Curator

**Find, rank, install, and safety-check Codex / Claude Agent Skills from GitHub, so your agent uses the right skill instead of a random repo.**

<a href="https://github.com/xcl2005/github-skill-curator/stargazers"><img src="https://img.shields.io/github/stars/xcl2005/github-skill-curator?style=flat-square" alt="GitHub stars"></a>
<a href="https://github.com/xcl2005/github-skill-curator/network/members"><img src="https://img.shields.io/github/forks/xcl2005/github-skill-curator?style=flat-square" alt="GitHub forks"></a>
<a href="https://github.com/xcl2005/github-skill-curator/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT license"></a>
<a href="https://github.com/xcl2005/github-skill-curator/releases"><img src="https://img.shields.io/github/v/release/xcl2005/github-skill-curator?style=flat-square" alt="Latest release"></a>
<img src="https://img.shields.io/badge/Agent%20Skills-Codex%20%7C%20Claude-111827?style=flat-square" alt="Agent Skills for Codex and Claude">
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square" alt="Python 3.10+">
<img src="https://img.shields.io/badge/Install-Review%20First-0F766E?style=flat-square" alt="Review before install">

[简体中文](README.md) · English

[Quick Start](#-quick-start) · [Demo](#-demo-find-and-review-a-pptx-skill) · [Scoring](#-scoring-model) · [Safety Scan](#-safety-scan-examples) · [Codex / Claude](#-codex--claude-code)

</div>

## 🔥 Positioning

Agent Skills are getting useful, but they are also getting messy. **GitHub Skill Curator** is a package manager + safety reviewer for Agent Skills: it checks local skills first, decides whether GitHub search is worth it, scores candidates, scans risk, shows reviewable options, and installs only the selected skill folder after approval.

The point is not to install more skills. The point is to help Codex / Claude Code choose the right skill for a task without missing better options, installing low-quality repos, or misrouting through unsafe trigger descriptions.

This project does not replace built-in artifact tools. It decides when built-in capability or an installed skill is enough, and when a specialized external skill is worth searching for and installing.

It is not only for Codex users. The shared Agent Skills structure is `skill-name/SKILL.md` plus optional `scripts/`, `references/`, and `assets/`. Codex and Claude Code mainly differ in install paths and direct invocation syntax.

## ✨ Why

Agent Skills are powerful, but a messy skill folder makes agents slower, noisier, and easier to misroute through overbroad `description` fields.

**GitHub Skill Curator** helps answer three questions:

| Question | Curator behavior |
|---|---|
| Is an existing skill enough? | Check built-in, user-level, and project-level skills first |
| Is there a better GitHub skill? | Search only for high-value, repeated, latest/high-star, or locally unsupported work |
| Will the installed skill actually be used? | After approval and successful install, read the new skill and use it for the current task by default |

## 🎬 Demo: Find and review a PPTX skill

```bash
python scripts/find_skills.py "PowerPoint PPTX editable presentation Agent Skill" --top 5 --tier relaxed
```

The command prints ranked candidates with the same fields the installer needs for review:

```text
# GitHub skill candidates (relaxed+)

| Rank | Repo | Tier | Score | Stars | Updated | License | Skill paths | Safety |
|---:|---|---|---:|---:|---|---|---|---|
| 1 | owner/ppt-skill | strict | 82.5 | 1200 | 2026-06-20 | MIT | skills/pptx/SKILL.md | OK |
| 2 | owner/slides-agent | relaxed | 68.0 | 340 | 2026-05-11 | Apache-2.0 | SKILL.md | medium warning |
```

Then the curator shows install command examples, but installation stays review-first:

```bash
python scripts/install_skill.py https://github.com/owner/ppt-skill --skill-path skills/pptx --agent codex
```

If a pinned or curated PPT source is already known, the curator checks that route before broad GitHub search. See [`examples/install-ppt-skill.md`](examples/install-ppt-skill.md).

## 👨‍💻 Use Cases

| Scenario | Default route |
|---|---|
| Repeated PPTX / DOCX / PDF / XLSX artifact workflows | Check pinned core skills first |
| Academic writing, LaTeX, resumes, application materials | Run the high-value task radar |
| User asks for latest / best / high-star / GitHub-recommended options | Force a fresh GitHub search |
| Installed skill is broad, stale, or mis-invoked | Audit, disable, quarantine, or replace |
| Low-value one-off task | Do the task directly; do not install just in case |

## 🎯 Highlights

| | Capability |
|---|---|
| 🔎 | Discover repositories with `SKILL.md` for Codex, Claude Code, and Agent Skills-style workflows |
| 🧭 | Route between built-in skills, installed skills, GitHub search, install, and rejection |
| ⭐ | Score candidates by task fit, stars, forks, maintenance, license, structure, docs, and examples |
| 🛡️ | Flag broad triggers, secret access, destructive commands, prompt injection, and opaque installers |
| 📦 | Install only the selected skill folder, not an entire unrelated repository |
| 🔁 | Print exact Codex / Claude Code invocation after installation |

## 📊 Scoring model

Candidates are scored by:

- task relevance;
- stars and forks;
- recent maintenance;
- license / reuse clarity;
- Agent Skill folder structure;
- examples, docs, scripts, references, and assets;
- safety scan result.

The script maps candidates into `strict`, `relaxed`, `exploratory`, or `reject` tiers. Score is a ranking aid, not a proof of quality; high-risk findings can reject an otherwise popular repository.

## 🛡️ Safety scan examples

The curator flags patterns such as:

- prompt injection: `ignore previous instructions`;
- secret access: `.env`, `id_rsa`, `OPENAI_API_KEY`, `GITHUB_TOKEN`;
- destructive commands: `rm -rf /`, `sudo`;
- opaque installers: `curl ... | sh`;
- obfuscated execution: `eval`, `base64 -d`, `Invoke-Expression`.

The scan is heuristic. It makes risk visible before installation; it does not prove that a third-party repository is safe.

## 📦 Quick Start

### Codex

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/xcl2005/github-skill-curator.git ~/.agents/skills/github-skill-curator
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.agents\skills"
git clone https://github.com/xcl2005/github-skill-curator.git "$HOME\.agents\skills\github-skill-curator"
```

Invocation:

```text
Use $github-skill-curator to find a high-quality reusable PPTX skill and explain whether it is worth installing.
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/xcl2005/github-skill-curator.git ~/.claude/skills/github-skill-curator
```

Direct invocation:

```text
/github-skill-curator find a high-quality reusable PPTX skill and install it if approved
```

### Install a candidate skill

```bash
# Install to Codex's default location
python scripts/install_skill.py owner/repo --skill-path path/to/skill --agent codex

# Install to Claude Code's default location
python scripts/install_skill.py owner/repo --skill-path path/to/skill --agent claude

# Install to both default locations
python scripts/install_skill.py owner/repo --skill-path path/to/skill --agent both
```

## 🔁 Codex / Claude Code

| Item | Codex | Claude Code |
|---|---|---|
| Shared structure | `skill-name/SKILL.md`, optionally with `scripts/`, `references/`, `assets/` | Same |
| User-level path | `~/.agents/skills/<skill-name>` | `~/.claude/skills/<skill-name>` |
| Project-level path | `.agents/skills/<skill-name>` | `.claude/skills/<skill-name>` |
| Automatic trigger | Matches the `description` to the task | Matches the `description` to the task |
| Direct invocation | `$skill-name ...` | `/skill-name ...` |
| Installer flag | `--agent codex` | `--agent claude` |

Claude.ai / Claude API custom skills are usually uploaded as a zip or registered through the Skills API. The clone commands in this repository are mainly for local Codex and Claude Code workflows.

## 🚀 Post-install Use

When the user approves installing a skill, that usually means the current skill set is missing, stale, or worse than the candidate. After a successful install, the default behavior is:

| Situation | Behavior |
|---|---|
| The current task still matches the new skill | Read the installed `SKILL.md` immediately and continue the task with it |
| The current agent cannot hot-load new skills | Print the exact path and the next invocation command |
| The user only asked to install, not execute | Install and print verification commands only |
| The skill proves mismatched or risky after install | Do not invoke it; explain why and suggest disable/remove steps |

The installer prints commands like:

```text
Codex: Use $skill-name to ...
Claude Code: /skill-name ...
```

## 🧭 Control Flow

```text
User Task
  -> Check Built-in / Installed Skills
  -> Search GitHub if needed
  -> Score Candidates
  -> Safety Scan
  -> User Approval
  -> Install Selected Skill
  -> Use Immediately
```

| Step | Decision | What happens |
|---:|---|---|
| 1 | Classify the task | Extract terms such as `pptx`, `latex`, `resume`, `research`, `docx`, `pdf`, or framework names |
| 2 | Check local skills | Inspect user-level, project-level, and configured skill directories |
| 3 | Decide freshness | Search only when the user asks for latest/best, the task is high-value, or local skills are weak |
| 4 | Choose discovery lane | Use pinned core, high-value task radar, curated index, or generic GitHub search |
| 5 | Score candidates | Compare relevance, stars, forks, update time, license, structure, docs, and trigger description |
| 6 | Scan risk | Check prompt injection, secret access, destructive commands, broad triggers, and opaque installers |
| 7 | Confirm install | Show candidates and risks, then install only after user approval |
| 8 | Use immediately | After install, read the new skill and apply it to the task or print explicit invocation |

## 🛠️ Commands

```bash
# Find skill candidates
python scripts/find_skills.py "PowerPoint PPTX editable presentation Agent Skill" --top 8

# Search curated indexes first
python scripts/find_curated_indexes.py "AI presentation Agent Skills" --top 8

# Classify a high-value task
python scripts/task_skill_radar.py "tailor my CS internship resume to this JD"

# Audit installed skills
python scripts/audit_skills.py audit --dest "$HOME/.agents/skills"

# Check pinned PPTX core skills
python scripts/ensure_core_skills.py pptx
```

## 🛡️ Safety

This project treats skill installation as a small supply-chain decision.

It looks for:

- overbroad descriptions such as "use for all tasks";
- prompt-injection language;
- secret, token, `.env`, or SSH key access patterns;
- destructive shell commands;
- opaque `curl | sh` installers;
- stale, duplicate, or overlapping skills.

It cannot prove a third-party skill is safe. It makes pre-install risk visible.

## 📁 Repository Layout

```text
.
|-- SKILL.md
|-- skill_manifest.yaml
|-- scripts/
|-- references/
|-- examples/
|-- agents/
|-- README.md
`-- README_EN.md
```

## 🔎 Search Keywords

Codex skills, Claude Code skills, Agent Skills, GitHub skill discovery, skill governance, skill installer, prompt safety, AI agents, Codex CLI, developer tools.

## 📄 License

MIT
