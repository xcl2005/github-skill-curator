#!/usr/bin/env python3
"""
Install one selected Agent Skill folder from a GitHub repository.

This script copies only the selected skill folder that contains SKILL.md.
It makes a timestamped backup if the destination already exists.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

REGISTRY = ".skill-curator-registry.json"

SUSPICIOUS_PATTERNS = [
    r"ignore (all )?(previous|system|developer|user) instructions",
    r"exfiltrat(e|ion)|steal\s+(secret|token|key|credential)|credential\s+harvest|private key|ssh key|browser profile",
    r"\.env|id_rsa|GITHUB_TOKEN|OPENAI_API_KEY|api[_-]?key",
    r"rm\s+-rf\s+(/|~|\$HOME|\*)",
    r"curl\s+[^\n|;]+\|\s*(sh|bash)",
    r"wget\s+[^\n|;]+\|\s*(sh|bash)",
    r"chmod\s+777|sudo\s+",
    r"base64\s+-d|eval\s+\$|Invoke-Expression|iex\b",
]
SKIP_SCAN_NAMES = {".gitignore", ".difyignore"}
SKIP_SCAN_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".pptx", ".docx", ".xlsx", ".pyc"}
SKIP_SCAN_PARTS = {".git", "__pycache__", "node_modules", ".venv"}


def parse_repo_url(url: str) -> str:
    if re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", url):
        return "https://github.com/" + url
    parsed = urlparse(url)
    if parsed.netloc.lower() != "github.com":
        raise ValueError("Only github.com repository URLs are supported.")
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError("Expected a GitHub repo URL like https://github.com/OWNER/REPO")
    return f"https://github.com/{parts[0]}/{parts[1]}"


def default_dest() -> Path:
    if os.environ.get("CODEX_SKILLS_DIR"):
        return Path(os.environ["CODEX_SKILLS_DIR"]).expanduser()
    return Path.home() / ".agents" / "skills"


def read_text(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_bytes()[:limit].decode("utf-8", errors="replace")
    except Exception:
        return ""


def scan_folder(folder: Path) -> list[str]:
    findings: list[str] = []
    for p in folder.rglob("*"):
        if p.name in SKIP_SCAN_NAMES:
            continue
        if p.suffix.lower() in SKIP_SCAN_SUFFIXES:
            continue
        if any(part in SKIP_SCAN_PARTS for part in p.parts):
            continue
        if not p.is_file():
            continue
        if p.stat().st_size > 500_000:
            continue
        text = read_text(p)
        lower = text.lower()
        for pat in SUSPICIOUS_PATTERNS:
            if re.search(pat, lower, flags=re.IGNORECASE):
                findings.append(f"{p.relative_to(folder)}: `{pat}`")
    # De-duplicate.
    return list(dict.fromkeys(findings))


def skill_name_from_frontmatter(skill_md: Path) -> str | None:
    text = read_text(skill_md, 20_000)
    m = re.search(r"(?m)^name:\s*['\"]?([A-Za-z0-9-]+)['\"]?\s*$", text)
    if m:
        return m.group(1).strip()
    return None


def validate_skill_folder(src: Path) -> tuple[str, str]:
    skill_md = src / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"Selected path does not contain SKILL.md: {src}")
    text = read_text(skill_md, 50_000)
    if not text.startswith("---"):
        raise ValueError("SKILL.md has no YAML frontmatter")
    name = skill_name_from_frontmatter(skill_md)
    if not name:
        raise ValueError("SKILL.md frontmatter is missing a valid hyphen-case name")
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", name):
        raise ValueError(f"Skill name must be lowercase hyphen-case: {name}")
    m = re.search(r"(?m)^description:\s*(.+)$", text)
    description = m.group(1).strip().strip('"\'') if m else ""
    if not description:
        raise ValueError("SKILL.md frontmatter is missing description")
    if len(description) > 1024:
        raise ValueError("SKILL.md description is longer than 1024 characters")
    return name, description


def copy_skill(src: Path, dest_root: Path, name_override: str | None, force: bool) -> Path:
    source_name, _ = validate_skill_folder(src)
    skill_name = name_override or source_name
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", skill_name):
        raise ValueError(f"Skill name must be lowercase hyphen-case: {skill_name}")
    if len(skill_name) > 64:
        raise ValueError(f"Skill name is too long: {skill_name}")
    dest = dest_root / skill_name
    dest_root.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        backup = dest.with_name(dest.name + f".backup-{time.strftime('%Y%m%d-%H%M%S')}")
        if not force:
            print(f"Destination exists. Moving old copy to {backup}")
        shutil.move(str(dest), str(backup))
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".git", "node_modules", ".venv", "__pycache__"))
    return dest



def git_commit(repo_dir: Path) -> str:
    try:
        out = subprocess.check_output(["git", "-C", str(repo_dir), "rev-parse", "HEAD"], text=True).strip()
        return out
    except Exception:
        return ""


def load_registry(dest_root: Path) -> dict:
    path = dest_root / REGISTRY
    if not path.exists():
        return {"installs": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"installs": []}


def save_registry(dest_root: Path, registry: dict) -> None:
    dest_root.mkdir(parents=True, exist_ok=True)
    (dest_root / REGISTRY).write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")


def record_install(dest_root: Path, dest: Path, repo_url: str, skill_path: str, commit: str, findings: list[str]) -> None:
    registry = load_registry(dest_root)
    installs = registry.setdefault("installs", [])
    entry = {
        "name": dest.name,
        "destination": str(dest),
        "repo_url": repo_url,
        "skill_path": skill_path,
        "commit": commit,
        "installed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": "active",
        "risk_count": len(findings),
        "risk_findings": findings[:20],
    }
    installs = [x for x in installs if not (x.get("name") == dest.name and x.get("destination") == str(dest))]
    installs.append(entry)
    registry["installs"] = installs
    save_registry(dest_root, registry)


def main() -> int:
    ap = argparse.ArgumentParser(description="Install one selected Agent Skill folder from GitHub.")
    ap.add_argument("repo", help="GitHub repo URL or OWNER/REPO")
    ap.add_argument("--skill-path", default=".", help="Path inside the repo that contains SKILL.md")
    ap.add_argument("--dest", default=str(default_dest()), help="Destination skills directory")
    ap.add_argument("--name", help="Override installed folder name")
    ap.add_argument("--yes", action="store_true", help="Proceed without interactive confirmation")
    ap.add_argument("--force", action="store_true", help="Replace existing destination after backup")
    ap.add_argument("--skip-safety-scan", action="store_true", help="Skip heuristic local safety scan")
    args = ap.parse_args()

    repo_url = parse_repo_url(args.repo)
    dest_root = Path(args.dest).expanduser()

    with tempfile.TemporaryDirectory(prefix="skill-install-") as td:
        work = Path(td) / "repo"
        print(f"Cloning {repo_url} ...")
        subprocess.run(["git", "clone", "--depth", "1", repo_url, str(work)], check=True)
        src = (work / args.skill_path).resolve()
        if not str(src).startswith(str(work.resolve())):
            raise ValueError("skill-path escapes repository root")
        if not (src / "SKILL.md").exists():
            possible = [str(p.relative_to(work)) for p in work.rglob("SKILL.md")]
            print("Selected path does not contain SKILL.md.")
            if possible:
                print("Available SKILL.md paths:")
                for p in possible[:20]:
                    print(" -", p)
            return 2

        commit = git_commit(work)
        findings = [] if args.skip_safety_scan else scan_folder(src)
        if findings:
            print("Safety scan warnings:")
            for f in findings[:20]:
                print(" -", f)
            if not args.yes:
                ans = input("Continue installation anyway? Type 'yes' to continue: ").strip().lower()
                if ans != "yes":
                    print("Installation cancelled.")
                    return 1

        if not args.yes:
            print(f"About to install {src.relative_to(work)} into {dest_root}")
            ans = input("Type 'yes' to continue: ").strip().lower()
            if ans != "yes":
                print("Installation cancelled.")
                return 1

        dest = copy_skill(src, dest_root, args.name, args.force)
        record_install(dest_root, dest, repo_url, args.skill_path, commit, findings)
        print(f"Installed skill to: {dest}")
        print("Verify with:")
        print(f"  head -40 {dest / 'SKILL.md'}")
        return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}", file=sys.stderr)
        raise SystemExit(e.returncode)
