#!/usr/bin/env python3
"""
Audit and manage installed Codex Agent Skills.

Examples:
  python3 scripts/audit_skills.py audit --dest ~/.agents/skills
  python3 scripts/audit_skills.py disable my-skill --dest ~/.agents/skills
  python3 scripts/audit_skills.py quarantine my-skill --dest ~/.agents/skills
  python3 scripts/audit_skills.py restore my-skill --dest ~/.agents/skills
  python3 scripts/audit_skills.py prune --older-than-days 180 --dry-run --dest ~/.agents/skills
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

SUSPICIOUS_PATTERNS = [
    ("high", r"ignore (all )?(previous|system|developer|user) instructions"),
    ("high", r"exfiltrat(e|ion)|steal\s+(secret|token|key|credential)|credential\s+harvest|private key|ssh key|browser profile"),
    ("high", r"\.env|id_rsa|GITHUB_TOKEN|OPENAI_API_KEY|api[_-]?key"),
    ("high", r"rm\s+-rf\s+(/|~|\$HOME|\*)"),
    ("medium", r"curl\s+[^\n|;]+\|\s*(sh|bash)"),
    ("medium", r"wget\s+[^\n|;]+\|\s*(sh|bash)"),
    ("medium", r"chmod\s+777|sudo\s+"),
    ("medium", r"base64\s+-d|eval\s+\$|Invoke-Expression|iex\b"),
]
SKIP_SCAN_NAMES = {".gitignore", ".difyignore"}
SKIP_SCAN_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".pptx", ".docx", ".xlsx", ".pyc"}
SKIP_SCAN_PARTS = {".git", "__pycache__", "node_modules", ".venv"}
POLICY_DOCS = {
    Path("SKILL.md"),
    Path("references/governance.md"),
    Path("references/scoring.md"),
    Path("references/core-task-policy.md"),
}

OVERBROAD_DESCRIPTION_PATTERNS = [
    r"use (this skill )?for all tasks",
    r"always (use|run|invoke)",
    r"every task",
    r"general helper",
    r"do everything",
    r"any task",
]

REGISTRY = ".skill-curator-registry.json"
DISABLED_DIR = ".disabled"
QUARANTINE_DIR = ".quarantine"

@dataclass
class SkillAudit:
    folder: str
    name: str
    status: str
    description: str
    modified: str
    age_days: int
    risk_count: int
    high_risk: bool
    broad_description: bool
    notes: list[str]


def default_dest() -> Path:
    return Path(os.environ.get("CODEX_SKILLS_DIR") or Path.home() / ".agents" / "skills").expanduser()


def read_text(path: Path, limit: int = 250_000) -> str:
    try:
        return path.read_bytes()[:limit].decode("utf-8", errors="replace")
    except Exception:
        return ""


def is_policy_context(text: str, start: int, end: int) -> bool:
    """Return true when a suspicious phrase appears inside safety guidance."""
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    context_start = max(0, text.rfind("\n", 0, max(0, line_start - 1)))
    nearby = text[max(0, start - 600):min(len(text), end + 600)].lower()
    context = (text[context_start:line_end] + "\n" + nearby).lower()
    policy_terms = [
        "reject", "require explicit warning", "safety", "risk", "warning",
        "avoid", "do not", "without review", "forbid", "suspicious_patterns",
        "安全", "风险", "拒绝", "不要", "避免",
    ]
    return any(term in context for term in policy_terms)


def parse_frontmatter(skill_md: Path) -> tuple[str, str]:
    text = read_text(skill_md, 80_000)
    name = skill_md.parent.name
    desc = ""
    m = re.search(r"(?m)^name:\s*['\"]?([^'\"\n]+)['\"]?\s*$", text)
    if m:
        name = m.group(1).strip()
    m = re.search(r"(?m)^description:\s*(.+)$", text)
    if m:
        desc = m.group(1).strip().strip('"\'')
    return name, desc


def scan_folder(folder: Path) -> tuple[list[str], bool]:
    findings: list[str] = []
    high = False
    for p in folder.rglob("*"):
        try:
            rel_path = p.relative_to(folder)
        except ValueError:
            rel_path = p
        if folder.name == "github-skill-curator" and rel_path in POLICY_DOCS:
            continue
        if p.name in SKIP_SCAN_NAMES:
            continue
        if p.suffix.lower() in SKIP_SCAN_SUFFIXES:
            continue
        if any(part in SKIP_SCAN_PARTS for part in p.parts):
            continue
        if not p.is_file() or p.stat().st_size > 750_000:
            continue
        text = read_text(p)
        for sev, pat in SUSPICIOUS_PATTERNS:
            match = re.search(pat, text, flags=re.IGNORECASE)
            if match and not is_policy_context(text, match.start(), match.end()):
                rel = str(p.relative_to(folder))
                findings.append(f"{sev}: {rel}: `{pat}`")
                if sev == "high":
                    high = True
    return list(dict.fromkeys(findings)), high


def is_broad_description(desc: str) -> bool:
    return any(re.search(p, desc, flags=re.IGNORECASE) for p in OVERBROAD_DESCRIPTION_PATTERNS)


def iter_skill_dirs(dest: Path, include_disabled: bool = False) -> Iterable[tuple[Path, str]]:
    if not dest.exists():
        return
    for child in sorted(dest.iterdir()):
        if child.name.startswith("."):
            continue
        if child.is_dir() and (child / "SKILL.md").exists():
            yield child, "active"
    if include_disabled:
        for status, rootname in [("disabled", DISABLED_DIR), ("quarantined", QUARANTINE_DIR)]:
            root = dest / rootname
            if root.exists():
                for child in sorted(root.iterdir()):
                    if child.is_dir() and (child / "SKILL.md").exists():
                        yield child, status


def audit(dest: Path, include_disabled: bool = False) -> list[SkillAudit]:
    rows: list[SkillAudit] = []
    now = time.time()
    for folder, status in iter_skill_dirs(dest, include_disabled=include_disabled) or []:
        skill_md = folder / "SKILL.md"
        name, desc = parse_frontmatter(skill_md)
        findings, high = scan_folder(folder)
        mtime = max((p.stat().st_mtime for p in folder.rglob("*") if p.exists()), default=folder.stat().st_mtime)
        age_days = max(0, int((now - mtime) // 86400))
        broad = is_broad_description(desc)
        notes = []
        if not desc:
            notes.append("missing description")
        if broad:
            notes.append("overbroad description")
        if findings:
            notes.extend(findings[:3])
        rows.append(SkillAudit(
            folder=str(folder), name=name, status=status, description=desc[:160],
            modified=time.strftime("%Y-%m-%d", time.localtime(mtime)), age_days=age_days,
            risk_count=len(findings), high_risk=high, broad_description=broad, notes=notes,
        ))
    rows.sort(key=lambda r: (r.status != "active", r.high_risk, r.risk_count, r.age_days), reverse=True)
    return rows


def print_markdown(rows: list[SkillAudit]) -> None:
    if not rows:
        print("No skills found.")
        return
    print("| Skill | Status | Modified | Age | Risks | Notes |")
    print("|---|---|---|---:|---:|---|")
    for r in rows:
        notes = "; ".join(r.notes) if r.notes else "OK"
        print(f"| {r.name} | {r.status} | {r.modified} | {r.age_days}d | {r.risk_count} | {notes} |")


def move_skill(dest: Path, name: str, target_status: str) -> Path:
    if target_status not in {"disabled", "quarantined", "active"}:
        raise ValueError("target_status must be disabled, quarantined, or active")
    sources = [dest / name, dest / DISABLED_DIR / name, dest / QUARANTINE_DIR / name]
    src = next((p for p in sources if p.exists() and p.is_dir()), None)
    if src is None:
        raise FileNotFoundError(f"Could not find skill folder named {name!r} under {dest}")
    if target_status == "active":
        target = dest / name
    elif target_status == "disabled":
        target = dest / DISABLED_DIR / name
    else:
        target = dest / QUARANTINE_DIR / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        backup = target.with_name(target.name + f".backup-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.move(str(target), str(backup))
    shutil.move(str(src), str(target))
    return target


def load_registry(dest: Path) -> dict:
    path = dest / REGISTRY
    if not path.exists():
        return {"installs": []}
    try:
        return json.loads(read_text(path, 2_000_000))
    except Exception:
        return {"installs": []}


def save_registry(dest: Path, registry: dict) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    (dest / REGISTRY).write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")


def prune(dest: Path, older_than_days: int, dry_run: bool) -> None:
    rows = [r for r in audit(dest) if r.age_days >= older_than_days or r.high_risk or r.broad_description]
    if not rows:
        print("No prune candidates.")
        return
    print_markdown(rows)
    if dry_run:
        print("Dry run only. No files changed.")
        return
    for r in rows:
        moved = move_skill(dest, Path(r.folder).name, "disabled" if not r.high_risk else "quarantined")
        print(f"Moved {r.name} -> {moved}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit and manage installed Codex Agent Skills.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_dest(p):
        p.add_argument("--dest", default=str(default_dest()), help="Skills root, default ~/.agents/skills or CODEX_SKILLS_DIR")

    p_audit = sub.add_parser("audit", help="Audit installed skills")
    add_dest(p_audit)
    p_audit.add_argument("--include-disabled", action="store_true")
    p_audit.add_argument("--json", action="store_true")

    for command in ["disable", "quarantine", "restore"]:
        p = sub.add_parser(command, help=f"{command} a skill")
        p.add_argument("name")
        add_dest(p)

    p_prune = sub.add_parser("prune", help="Disable/quarantine old or risky skills")
    add_dest(p_prune)
    p_prune.add_argument("--older-than-days", type=int, default=180)
    p_prune.add_argument("--dry-run", action="store_true")

    p_reg = sub.add_parser("registry", help="Print local curator registry")
    add_dest(p_reg)

    args = ap.parse_args()
    dest = Path(args.dest).expanduser()

    if args.cmd == "audit":
        rows = audit(dest, include_disabled=args.include_disabled)
        if args.json:
            print(json.dumps([asdict(r) for r in rows], ensure_ascii=False, indent=2))
        else:
            print_markdown(rows)
        return 0
    if args.cmd == "disable":
        print(move_skill(dest, args.name, "disabled"))
        return 0
    if args.cmd == "quarantine":
        print(move_skill(dest, args.name, "quarantined"))
        return 0
    if args.cmd == "restore":
        print(move_skill(dest, args.name, "active"))
        return 0
    if args.cmd == "prune":
        prune(dest, args.older_than_days, args.dry_run)
        return 0
    if args.cmd == "registry":
        print(json.dumps(load_registry(dest), ensure_ascii=False, indent=2))
        return 0
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
