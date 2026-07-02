<div align="center">

# GitHub Skill Curator

**帮 Codex 找到更好的 Agent Skills，同时避免技能目录被污染。**

<a href="https://github.com/xcl2005/github-skill-curator/stargazers"><img src="https://img.shields.io/github/stars/xcl2005/github-skill-curator?style=flat-square" alt="stars"></a>
<a href="https://github.com/xcl2005/github-skill-curator/network/members"><img src="https://img.shields.io/github/forks/xcl2005/github-skill-curator?style=flat-square" alt="forks"></a>
<a href="https://github.com/xcl2005/github-skill-curator/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="license"></a>
<img src="https://img.shields.io/badge/Codex-Agent%20Skill-111827?style=flat-square" alt="Codex Agent Skill">
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square" alt="Python 3.10+">

[English](README.md) · 简体中文

[安装](#安装) · [为什么需要](#为什么需要) · [控制流程](#控制流程) · [常用命令](#常用命令) · [安全策略](#安全策略)

</div>

## 为什么需要

Agent Skill 很有用，但技能目录一旦变乱，Codex 会变慢、误触发、甚至被过宽的提示词带偏。

**GitHub Skill Curator** 是一个 skill 治理层。它会先检查本地已有 skill，再判断是否值得搜索 GitHub；搜索后会评分、做风险扫描、展示候选，并且默认要求用户批准后才安装。

## 亮点

| | 能力 |
|---|---|
| 🔎 | 搜索包含 `SKILL.md` 的 Codex / Claude Code 风格 skill |
| 🧭 | 判断该用内置 skill、本地 skill，还是寻找新 skill |
| 🧪 | 按任务匹配、star、维护时间、许可证、结构和文档质量评分 |
| 🛡️ | 标记过宽触发、密钥访问、破坏性命令、不透明安装脚本 |
| 🧹 | 支持审计、禁用、隔离、恢复和清理本地 skill |

## 控制流程

这个 skill 不是简单的搜索脚本，而是一个路由器。它的目标是让 Codex 在“直接做、用本地 skill、搜索新 skill、安装、拒绝风险候选”之间做出更稳的判断。

| 步骤 | 决策点 | 行为 |
|---:|---|---|
| 1 | 任务分类 | 提取 `pptx`、`latex`、`resume`、`research`、`docx`、`pdf`、测试、框架名等关键词。 |
| 2 | 检查本地 | 先检查用户级、项目级和配置目录里的 skill。 |
| 3 | 判断新鲜度 | 只有在用户要最新/最佳、高价值任务、本地能力不足时才搜索。 |
| 4 | 选择发现通道 | 在 pinned core、高价值任务雷达、curated index、通用 GitHub 搜索之间选择。 |
| 5 | 候选评分 | 比较相关性、star、fork、更新时间、license、结构、文档和触发描述质量。 |
| 6 | 风险扫描 | 检查 prompt injection、密钥访问、破坏性命令、过宽触发、不透明安装器。 |
| 7 | 安装确认 | 展示候选和风险，默认只在用户批准后安装选中的 skill 文件夹。 |
| 8 | 生命周期维护 | 后续可审计、禁用、隔离、恢复或清理 stale/noisy skills。 |

### 路由策略

| 情况 | 默认处理 |
|---|---|
| 内置/system skill 已足够 | 直接使用，不搜索 |
| 本地已有强匹配 skill | 使用本地 skill |
| PPTX/DOCX/PDF/XLSX 等重复产物工作流 | 检查 pinned core skill |
| 学术写作、LaTeX、简历、申请材料、报告 | 运行高价值任务雷达 |
| 用户明确要 latest/best/high-star | 强制刷新 GitHub 搜索 |
| 候选过宽、过旧或有风险 | 拒绝、隔离或要求显式确认 |

### 发现通道

- **Pinned core 通道：** 适合稳定可复用的产物工作流，例如可编辑 PPT。
- **高价值任务雷达：** 覆盖学术写作、文献综述、LaTeX、简历、申请材料、DOCX/PDF/XLSX 报告。
- **Curated index 通道：** 使用 awesome list 或精选列表作为线索，不盲信整仓库。
- **通用 GitHub 通道：** 搜索带 `SKILL.md` 的候选仓库。
- **生命周期通道：** 审计本地 skill，禁用噪音项，默认不删除用户文件。

## 安装

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/xcl2005/github-skill-curator.git ~/.agents/skills/github-skill-curator
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.agents\skills"
git clone https://github.com/xcl2005/github-skill-curator.git "$HOME\.agents\skills\github-skill-curator"
```

如果 Codex 没有自动刷新 skill 列表，重启 Codex。

## 常用命令

```bash
# 查找候选 skill
python scripts/find_skills.py "PowerPoint PPTX editable presentation Codex skill" --top 8

# 先查 curated index
python scripts/find_curated_indexes.py "AI presentation Codex skills" --top 8

# 分类高价值任务
python scripts/task_skill_radar.py "tailor my CS internship resume to this JD"

# 审计本地 skill
python scripts/audit_skills.py audit --dest "$HOME/.agents/skills"
```

## 安全策略

这个项目把 skill 安装视为一个小型供应链决策。

它会关注：

- “use for all tasks” 这类过宽描述；
- prompt injection 语言；
- 密钥、token、`.env`、SSH key 访问模式；
- 破坏性 shell 命令；
- `curl | sh` 这类不透明安装方式；
- stale、重复、互相覆盖的 skill。

它不能证明第三方 skill 一定安全，但会让安装前的风险变得可见。

## 值得阅读的文件

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 主入口、触发规则和操作原则 |
| `references/scoring.md` | 候选评分规则 |
| `references/governance.md` | 长期治理和生命周期管理 |
| `references/high_value_discovery_lanes.json` | 高价值任务雷达配置 |
| `references/known_good_skills.json` | pinned reusable skill 候选 |
| `scripts/install_skill.py` | 可审查的 skill 安装脚本 |

## 项目质量检查

```bash
python scripts/validate_readme_quality.py
```

检查会阻止 README 中出现大尺寸 banner、Mermaid 图、残留 hero/workflow SVG 引用，以及缺失安装/安全说明。

## 搜索关键词

Codex skills, Agent Skills, GitHub skill discovery, skill governance, skill installer, prompt safety, AI agents, Claude Code skills, Codex CLI, developer tools.

## License

MIT
