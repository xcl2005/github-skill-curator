#!/usr/bin/env python3
"""
Ensure pinned core skills for clear, reusable tasks are present.

This script is intentionally conservative by default: it reports missing pinned
skills and prints install commands. Use --install to run install_skill.py.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST = ROOT / "references" / "known_good_skills.json"


def default_dest(agent: str = "codex") -> Path:
    if agent == "claude":
        if os.environ.get("CLAUDE_SKILLS_DIR"):
            return Path(os.environ["CLAUDE_SKILLS_DIR"]).expanduser()
        return Path.home() / ".claude" / "skills"
    if os.environ.get("CODEX_SKILLS_DIR"):
        return Path(os.environ["CODEX_SKILLS_DIR"]).expanduser()
    return Path.home() / ".agents" / "skills"


def load_allowlist() -> dict:
    with ALLOWLIST.open("r", encoding="utf-8") as f:
        return json.load(f)


def builtin_capabilities(data: dict, domain: str) -> list[dict]:
    return data.get("builtin_capabilities", {}).get(domain, [])


def installed_skill_names(dest: Path) -> set[str]:
    names: set[str] = set()
    if not dest.exists():
        return names
    for child in dest.iterdir():
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        if skill_md.exists():
            names.add(child.name)
            text = skill_md.read_text(encoding="utf-8", errors="replace")[:5000]
            for line in text.splitlines()[:20]:
                if line.startswith("name:"):
                    names.add(line.split(":", 1)[1].strip().strip('"\''))
    return names


def main() -> int:
    ap = argparse.ArgumentParser(description="Check or install pinned core skills for reusable artifact tasks.")
    ap.add_argument("domain", nargs="?", default="pptx", help="Domain key from references/known_good_skills.json, e.g. pptx")
    ap.add_argument("--dest", help="Destination skills directory. Defaults to ~/.agents/skills for Codex or ~/.claude/skills for Claude Code")
    ap.add_argument("--install", action="store_true", help="Install missing pinned core skills")
    ap.add_argument("--agent", choices=["codex", "claude"], default="codex", help="Agent target to pass to install_skill.py")
    ap.add_argument("--prefer-external-core", action="store_true", help="Treat missing external pinned skills as missing even when a built-in capability exists")
    ap.add_argument("--yes", action="store_true", help="Pass --yes to install_skill.py")
    args = ap.parse_args()

    data = load_allowlist()
    domain = args.domain
    skills = data.get("domains", {}).get(domain)
    if not skills:
        print(f"No pinned core skills configured for domain: {domain}")
        print("Available domains:", ", ".join(sorted(data.get("domains", {}).keys())))
        return 2

    dest = Path(args.dest).expanduser() if args.dest else default_dest(args.agent)
    installed = installed_skill_names(dest)
    builtins = builtin_capabilities(data, domain)
    missing = []

    print(f"# Core skill check: {domain}")
    print(f"Destination: {dest}")
    print()
    if builtins:
        print("Built-in/system capabilities to consider first:")
        for b in builtins:
            print(f"- {b['name']}: {b.get('why', '')}")
        print()
    for s in skills:
        name = s["name"]
        present = name in installed
        status = "installed" if present else "missing-external"
        print(f"- {name}: {status}")
        print(f"  repo: {s['repo_url']}")
        print(f"  path: {s['skill_path']}")
        print(f"  why: {s.get('why','')}")
        if not present:
            if args.prefer_external_core or args.install or not builtins:
                missing.append(s)
            cmd = f"python3 scripts/install_skill.py {s['repo_url']} --skill-path {s['skill_path']} --agent {args.agent}"
            print(f"  install: {cmd}")
        print()

    if not missing:
        if builtins:
            print("No mandatory external install needed: a built-in/system capability covers this domain. Install pinned external skills only when repeated use or fidelity requirements justify it.")
        else:
            print("All pinned core skills for this domain are installed.")
        return 0

    if not args.install:
        print("Missing pinned core skills found. Re-run with --install to install them after reviewing the upstream repo.")
        return 1

    installer = ROOT / "scripts" / "install_skill.py"
    for s in missing:
        cmd = [sys.executable, str(installer), s["repo_url"], "--skill-path", s["skill_path"], "--dest", str(dest), "--agent", args.agent]
        if args.yes:
            cmd.append("--yes")
        print("Running:", " ".join(cmd))
        subprocess.run(cmd, check=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as e:
        raise SystemExit(e.returncode)
