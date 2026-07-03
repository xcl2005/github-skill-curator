#!/usr/bin/env python3
"""
Find and score curated skill/tool indexes such as awesome-* repositories.

Curated indexes are discovery accelerators, not install allowlists. A low-star
index can be useful when it has focused scope, curation evidence, linked
projects, and a valid skill entrypoint.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from risk_scan import scan_text_for_risks

API = "https://api.github.com"
USER_AGENT = "github-skill-curator/1.2"
ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "references" / "curated_skill_indexes.json"

CURATION_WORDS = [
    "awesome", "curated", "精选", "清单", "汇总", "list", "index", "collection",
    "not exhaustive", "not all", "收录范围", "contributing", "contribute",
]
DOMAIN_TERMS = {
    "pptx": ["ppt", "pptx", "powerpoint", "slides", "deck", "presentation", "幻灯片", "演示"],
    "docx": ["docx", "word", "document", "report", "文档", "报告"],
    "pdf": ["pdf", "ocr", "extract", "annotation", "annotate"],
    "xlsx": ["xlsx", "excel", "spreadsheet", "csv", "表格"],
    "academic": ["paper", "academic", "literature", "citation", "latex", "论文", "科研", "文献"],
    "resume": ["resume", "cv", "ats", "job", "cover letter", "简历", "求职"],
}
@dataclass
class IndexCandidate:
    repo: str
    url: str
    description: str
    stars: int
    forks: int
    updated_at: str
    license: str
    archived: bool
    skill_paths: list[str]
    github_links: int
    curation_signals: list[str]
    safety: list[str]
    score: float
    tier: str
    install_commands: list[str]
    source: str


def github_request(path_or_url: str) -> Any:
    url = path_or_url if path_or_url.startswith("http") else API + path_or_url
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            msg = e.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"GitHub rate limit or permission issue ({e.code}). Set GITHUB_TOKEN. {msg}") from e
        raise


def task_domains(task: str) -> list[str]:
    lower = task.lower()
    domains: list[str] = []
    for domain, terms in DOMAIN_TERMS.items():
        if any(t.lower() in lower for t in terms):
            domains.append(domain)
    return domains or ["general"]


def load_seed_indexes(task: str) -> list[dict[str, Any]]:
    if not INDEX_FILE.exists():
        return []
    data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    domains = set(task_domains(task))
    rows = []
    for item in data.get("indexes", []):
        item_domains = {str(x).lower() for x in item.get("domains", [])}
        if "general" in item_domains or domains.intersection(item_domains):
            rows.append(item)
    return rows


def repo_api_path(repo: str) -> str:
    return "/repos/" + urllib.parse.quote(repo, safe="/")


def get_tree(repo: str, branch: str) -> list[dict[str, Any]]:
    data = github_request(f"{repo_api_path(repo)}/git/trees/{urllib.parse.quote(branch, safe='')}?recursive=1")
    if isinstance(data, dict):
        return data.get("tree", [])
    return []


def get_file_text(repo: str, branch: str, path: str, max_bytes: int = 120_000) -> str:
    raw = f"https://raw.githubusercontent.com/{repo}/{urllib.parse.quote(branch, safe='')}/{path}"
    req = urllib.request.Request(raw, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read(max_bytes).decode("utf-8", errors="replace")
    except Exception:
        return ""


def days_since(iso: str) -> int:
    try:
        d = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return max(0, (dt.datetime.now(dt.timezone.utc) - d).days)
    except Exception:
        return 9999


def score_index(repo: dict[str, Any], tree: list[dict[str, Any]], readme: str, skill_texts: list[str], seed: bool) -> tuple[float, str, list[str], list[str]]:
    signals: list[str] = []
    searchable = " ".join([
        repo.get("full_name", ""),
        repo.get("name", ""),
        repo.get("description") or "",
        readme[:50000],
        " ".join(skill_texts),
    ]).lower()

    for word in CURATION_WORDS:
        if word.lower() in searchable:
            signals.append(f"curation:{word}")

    links = len(set(re.findall(r"github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", readme)))
    if links >= 10:
        signals.append(f"linked-projects:{links}")
    elif links >= 3:
        signals.append(f"some-linked-projects:{links}")

    paths = [x.get("path", "") for x in tree]
    skill_paths = [p for p in paths if p.endswith("SKILL.md")]
    if skill_paths:
        signals.append("has-skill")
    if any(p.lower().endswith("license") or p.lower().endswith("license.md") for p in paths):
        signals.append("has-license")
    if any("docs/" in p.lower() for p in paths):
        signals.append("has-docs")
    if "|" in readme and "---" in readme:
        signals.append("table-format")
    if seed:
        signals.append("seed-index")

    stars = repo.get("stargazers_count") or 0
    forks = repo.get("forks_count") or 0
    age_days = min(days_since(repo.get("pushed_at") or repo.get("updated_at") or ""), days_since(repo.get("updated_at") or ""))
    license_name = (repo.get("license") or {}).get("spdx_id") or "NOASSERTION"

    curation = min(42.0, len(signals) * 5.0 + min(10.0, links / 4.0))
    popularity = min(18.0, math.log10(stars + 1) * 5.0 + math.log10(forks + 1) * 2.0)
    maintenance = 15 if age_days <= 90 else 10 if age_days <= 365 else 5 if age_days <= 730 else 1
    structure = 12 if skill_paths else 5 if readme else 0
    license_score = 5 if license_name not in ("", "NOASSERTION") else 1
    seed_boost = 8 if seed else 0
    safety = scan_text_for_risks(readme + "\n".join(skill_texts))
    safety_score = 0 if any(x.startswith("high") for x in safety) else 5 if safety else 10

    score = round(curation + popularity + maintenance + structure + license_score + seed_boost + safety_score, 1)
    if repo.get("archived") or any(x.startswith("high") for x in safety):
        tier = "reject"
    elif score >= 75 and skill_paths and links >= 5:
        tier = "strong-index"
    elif score >= 60 and (skill_paths or links >= 10):
        tier = "usable-index"
    elif score >= 45 and links >= 3:
        tier = "review-index"
    else:
        tier = "reject"
    return score, tier, signals, safety


def inspect_repo(repo_full_name: str, seed_source: str = "github-search") -> IndexCandidate | None:
    repo = github_request(repo_api_path(repo_full_name))
    if not isinstance(repo, dict):
        return None
    branch = repo.get("default_branch") or "main"
    tree = get_tree(repo_full_name, branch)
    paths = [x.get("path", "") for x in tree]
    readme_path = next((p for p in paths if p.lower() == "readme.md"), "")
    readme = get_file_text(repo_full_name, branch, readme_path) if readme_path else ""
    skill_paths = [p for p in paths if p.endswith("SKILL.md")]
    skill_texts = [get_file_text(repo_full_name, branch, p, max_bytes=16000) for p in skill_paths[:3]]
    score, tier, signals, safety = score_index(repo, tree, readme, skill_texts, seed_source == "seed")
    commands = [
        f"python3 scripts/install_skill.py {repo['html_url']} --skill-path {p.rsplit('/', 1)[0] if '/' in p else '.'}"
        for p in skill_paths[:5]
    ]
    return IndexCandidate(
        repo=repo_full_name,
        url=repo.get("html_url") or f"https://github.com/{repo_full_name}",
        description=repo.get("description") or "",
        stars=repo.get("stargazers_count") or 0,
        forks=repo.get("forks_count") or 0,
        updated_at=repo.get("pushed_at") or repo.get("updated_at") or "",
        license=(repo.get("license") or {}).get("spdx_id") or "NOASSERTION",
        archived=bool(repo.get("archived")),
        skill_paths=skill_paths,
        github_links=len(set(re.findall(r"github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", readme))),
        curation_signals=signals,
        safety=safety,
        score=score,
        tier=tier,
        install_commands=commands,
        source=seed_source,
    )


def build_queries(task: str) -> list[str]:
    domains = task_domains(task)
    base = " ".join(domains)
    queries = [
        f"awesome {base} agent skills SKILL.md",
        f"curated {base} codex skills",
        f"awesome {task} skill",
    ]
    if "pptx" in domains:
        queries += ["awesome ai ppt", "powerpoint automation curated skill"]
    return list(dict.fromkeys(q.strip() for q in queries if q.strip()))


def search_repositories(query: str, per_page: int) -> list[dict[str, Any]]:
    q = f"{query} in:name,description,readme"
    url = "/search/repositories?" + urllib.parse.urlencode({
        "q": q,
        "sort": "updated",
        "order": "desc",
        "per_page": min(per_page, 50),
    })
    try:
        data = github_request(url)
    except (RuntimeError, urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"warning: GitHub search failed for {query!r}: {e}", file=sys.stderr)
        return []
    return data.get("items", []) if isinstance(data, dict) else []


def collect(task: str, top: int, search_github: bool, max_inspect: int) -> list[IndexCandidate]:
    repos: dict[str, str] = {}
    for seed in load_seed_indexes(task):
        repos[seed["repo"]] = "seed"
    if search_github:
        for q in build_queries(task):
            for repo in search_repositories(q, per_page=max(top * 2, 10)):
                repos.setdefault(repo["full_name"], "github-search")
                if len(repos) >= max_inspect:
                    break
            if len(repos) >= max_inspect:
                break
            time.sleep(0.2)
    rows: list[IndexCandidate] = []
    for repo, source in list(repos.items())[:max_inspect]:
        try:
            row = inspect_repo(repo, source)
            if row:
                rows.append(row)
        except Exception as e:
            print(f"warning: cannot inspect {repo}: {e}", file=sys.stderr)
    rows.sort(key=lambda x: (x.tier in {"strong-index", "usable-index"}, x.score, x.stars), reverse=True)
    return rows[:top]


def print_markdown(rows: list[IndexCandidate], task: str) -> None:
    if not rows:
        print("No curated indexes found.")
        print("Fallback roundup command:")
        print(f"  `python3 scripts/build_skill_roundup.py {task!r} --top 12`")
        return
    print(f"# Curated skill indexes for: {task}")
    print()
    print("| Rank | Repo | Tier | Score | Stars | Links | License | Skill paths | Safety |")
    print("|---:|---|---|---:|---:|---:|---|---|---|")
    for i, row in enumerate(rows, 1):
        paths = "<br>".join(row.skill_paths[:3]) if row.skill_paths else "index-only"
        safety = "OK" if not row.safety else "; ".join(row.safety[:2])
        print(f"| {i} | [{row.repo}]({row.url}) | {row.tier} | {row.score} | {row.stars} | {row.github_links} | {row.license} | {paths} | {safety} |")
    print()
    for i, row in enumerate(rows, 1):
        print(f"## {i}. {row.repo}")
        if row.description:
            print(row.description)
        print("- Signals: " + (", ".join(row.curation_signals[:10]) if row.curation_signals else "none"))
        if row.install_commands:
            print("- Install command examples:")
            for cmd in row.install_commands[:3]:
                print(f"  - `{cmd}`")
        else:
            print("- Install command examples: index-only; inspect linked skill folders individually.")
        print()
    print("If no index is strong enough, generate a reviewable shortlist instead:")
    print(f"`python3 scripts/build_skill_roundup.py {task!r} --top 12`")


def main() -> int:
    parser = argparse.ArgumentParser(description="Find curated skill/tool indexes for a task.")
    parser.add_argument("task")
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--search-github", action="store_true", help="Search GitHub in addition to seeded curated indexes")
    parser.add_argument("--max-inspect", type=int, default=12, help="Maximum repositories to inspect during GitHub search")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    rows = collect(args.task, args.top, args.search_github, args.max_inspect)
    if args.json:
        print(json.dumps([asdict(x) for x in rows], ensure_ascii=False, indent=2))
    else:
        print_markdown(rows, args.task)
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
