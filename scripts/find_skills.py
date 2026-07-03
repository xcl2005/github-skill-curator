#!/usr/bin/env python3
"""
Find and rank GitHub repositories that contain Agent Skill packages (SKILL.md).

Usage:
  python3 scripts/find_skills.py "pptx presentation codex skill" --top 8
  GITHUB_TOKEN=ghp_... python3 scripts/find_skills.py "latex journal formatting" --tier relaxed
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

API = "https://api.github.com"
USER_AGENT = "github-skill-curator/1.1"

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "for", "of", "in", "on", "with", "by", "from",
    "skill", "skills", "codex", "agent", "agents", "github", "use", "make", "create", "build",
    "自动", "下载", "安装", "合适", "高质量", "任务", "技能", "每次", "寻找", "使用",
}

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

# Keep this separate so older mojibake literals above do not affect Chinese tasks.
STOPWORDS.update({
    "自动", "下载", "安装", "合适", "高质量", "任务", "技能", "每次", "寻找", "使用",
})

@dataclass
class Candidate:
    repo: str
    url: str
    description: str
    stars: int
    forks: int
    open_issues: int
    updated_at: str
    pushed_at: str
    license: str
    archived: bool
    default_branch: str
    skill_paths: List[str]
    matched_terms: List[str]
    safety: List[str]
    score: float
    tier: str
    reasons: List[str]
    install_commands: List[str]


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
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            msg = e.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(
                f"GitHub rate limit or permission issue ({e.code}). Set GITHUB_TOKEN for higher limits. {msg}"
            ) from e
        raise


def terms_from_task(task: str) -> List[str]:
    raw = re.findall(r"[A-Za-z0-9_+.#-]{2,}|[\u4e00-\u9fff]{2,}", task.lower())
    terms = []
    for t in raw:
        t = t.strip("-_+.#")
        if len(t) < 2 or t in STOPWORDS:
            continue
        if t not in terms:
            terms.append(t)
    synonyms = []
    joined = " ".join(terms)
    task_l = task.lower()
    if any(x in task_l for x in ["ppt", "pptx", "slide", "presentation", "powerpoint", "演示", "幻灯"]):
        synonyms += ["pptx", "powerpoint", "presentation", "slides", "deck"]
    if any(x in task_l for x in ["docx", "word", "论文", "paper", "journal", "latex", "research", "academic", "文献", "科研"]):
        synonyms += ["docx", "word", "latex", "paper", "journal", "formatting", "academic", "research", "citation", "bibtex"]
    if any(x in task_l for x in ["formula", "equation", "math", "数学", "公式", "tikz", "overleaf"]):
        synonyms += ["latex", "math", "equation", "formula", "tikz", "compile", "pdf"]
    if any(x in task_l for x in ["resume", "cv", "ats", "cover", "求职", "简历", "实习", "job", "interview", "jd", "career"]):
        synonyms += ["resume", "cv", "ats", "job", "application", "cover-letter", "interview", "career"]
    if any(x in task_l for x in ["sop", "ps", "statement", "purpose", "personal", "申请", "文书", "港硕", "graduate", "scholarship"]):
        synonyms += ["sop", "personal-statement", "statement-of-purpose", "graduate", "application", "cv"]
    if any(x in task_l for x in ["excel", "xlsx", "spreadsheet", "表格"]):
        synonyms += ["xlsx", "excel", "spreadsheet"]
    if any(x in joined for x in ["ppt", "pptx", "slide", "presentation", "powerpoint", "演示", "幻灯"]):
        synonyms += ["pptx", "powerpoint", "presentation", "slides", "deck"]
    if any(x in joined for x in ["docx", "word", "论文", "paper", "journal", "latex", "research", "academic", "文献", "科研"]):
        synonyms += ["docx", "word", "latex", "paper", "journal", "formatting", "academic", "research", "citation", "bibtex"]
    if any(x in joined for x in ["formula", "equation", "math", "数学", "公式", "tikz", "overleaf"]):
        synonyms += ["latex", "math", "equation", "formula", "tikz", "compile", "pdf"]
    if any(x in joined for x in ["resume", "cv", "ats", "cover", "求职", "简历", "实习", "job", "interview", "jd", "career"]):
        synonyms += ["resume", "cv", "ats", "job", "application", "cover-letter", "interview", "career"]
    if any(x in joined for x in ["sop", "ps", "statement", "purpose", "personal", "申请", "文书", "港硕", "graduate", "scholarship"]):
        synonyms += ["sop", "personal-statement", "statement-of-purpose", "graduate", "application", "cv"]
    if any(x in joined for x in ["excel", "xlsx", "spreadsheet", "表格"]):
        synonyms += ["xlsx", "excel", "spreadsheet"]
    if any(x in joined for x in ["pdf"]):
        synonyms += ["pdf", "acrobat", "extract", "annotate"]
    for s in synonyms + ["SKILL.md", "agent-skill", "codex-skill"]:
        sl = s.lower()
        if sl not in terms:
            terms.append(sl)
    return terms[:12]


def build_queries(terms: List[str]) -> List[str]:
    core = " ".join(terms[:6])
    queries = [
        f'{core} "SKILL.md"',
        f'{core} agent-skill',
        f'{core} codex-skill',
    ]
    # GitHub repository search does not support exact file existence; we verify SKILL.md later.
    seen = []
    for q in queries:
        q = q.strip()
        if q and q not in seen:
            seen.append(q)
    return seen


def search_repositories(query: str, per_page: int) -> List[Dict[str, Any]]:
    q = f"{query} in:name,description,readme"
    url = "/search/repositories?" + urllib.parse.urlencode({
        "q": q,
        "sort": "stars",
        "order": "desc",
        "per_page": min(per_page, 50),
    })
    data = github_request(url)
    return data.get("items", []) if isinstance(data, dict) else []


def get_tree(repo_full_name: str, branch: str) -> List[Dict[str, Any]]:
    encoded = urllib.parse.quote(repo_full_name, safe="/")
    ref = urllib.parse.quote(branch, safe="")
    data = github_request(f"/repos/{encoded}/git/trees/{ref}?recursive=1")
    if not isinstance(data, dict) or "tree" not in data:
        return []
    return data["tree"]


def get_file_text(repo_full_name: str, branch: str, path: str, max_bytes: int = 16000) -> str:
    raw = f"https://raw.githubusercontent.com/{repo_full_name}/{urllib.parse.quote(branch, safe='')}/{path}"
    headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(raw, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read(max_bytes)
            return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def scan_text_for_risks(text: str) -> List[str]:
    findings = []
    lower = text.lower()
    for sev, pat in SUSPICIOUS_PATTERNS:
        if re.search(pat, lower, flags=re.IGNORECASE):
            findings.append(f"{sev}: pattern `{pat}`")
    return findings


def days_since(iso: str) -> int:
    try:
        d = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return max(0, (dt.datetime.now(dt.timezone.utc) - d).days)
    except Exception:
        return 9999


def score_repo(repo: Dict[str, Any], skill_paths: List[str], skill_texts: List[str], terms: List[str], tree: List[Dict[str, Any]]) -> Tuple[float, str, List[str], List[str], List[str]]:
    searchable = " ".join([
        repo.get("full_name", ""),
        repo.get("description") or "",
        " ".join(repo.get("topics") or []),
        " ".join(skill_texts[:3]),
    ]).lower()

    matched = [t for t in terms if t.lower() in searchable]
    relevance = min(35.0, 8.0 + len(matched) * 3.5)
    if skill_paths:
        relevance += 4
    if any(p.lower().endswith(("example.json", "examples", "readme.md")) for p in [x.get("path", "") for x in tree]):
        relevance += 2
    relevance = min(35.0, relevance)

    stars = repo.get("stargazers_count") or 0
    forks = repo.get("forks_count") or 0
    issues = repo.get("open_issues_count") or 0
    popularity = min(10.0, math.log10(stars + 1) * 4.0)
    popularity += min(4.0, math.log10(forks + 1) * 2.0)
    if issues > 0:
        popularity += 1.5
    popularity = min(20.0, popularity)

    age_days = min(days_since(repo.get("pushed_at") or repo.get("updated_at") or ""), days_since(repo.get("updated_at") or ""))
    if age_days <= 30:
        maintenance = 15
    elif age_days <= 180:
        maintenance = 12
    elif age_days <= 365:
        maintenance = 8
    elif age_days <= 730:
        maintenance = 4
    else:
        maintenance = 1

    paths = [x.get("path", "") for x in tree]
    structure = 0
    if skill_paths:
        structure += 6
    if any("scripts/" in p for p in paths):
        structure += 2
    if any("references/" in p for p in paths):
        structure += 2
    if any("assets/" in p for p in paths):
        structure += 1
    if any("agents/openai.yaml" in p for p in paths):
        structure += 2
    if any("test" in p.lower() or "example" in p.lower() for p in paths):
        structure += 2
    structure = min(15, structure)

    license_name = (repo.get("license") or {}).get("spdx_id") or "NOASSERTION"
    license_score = 5 if license_name and license_name not in ("NOASSERTION", "") else 1

    risk_findings = []
    for text in skill_texts:
        risk_findings.extend(scan_text_for_risks(text))
    # De-duplicate while preserving order.
    risk_findings = list(dict.fromkeys(risk_findings))
    safety = 10
    if any(f.startswith("high") for f in risk_findings):
        safety = 0
    elif any(f.startswith("medium") for f in risk_findings):
        safety = 4

    score = relevance + popularity + maintenance + structure + license_score + safety
    reasons = []
    if matched:
        reasons.append("matched terms: " + ", ".join(matched[:8]))
    if stars >= 100:
        reasons.append("strong star signal")
    elif stars >= 20:
        reasons.append("moderate star signal")
    if age_days <= 180:
        reasons.append("recently maintained")
    if license_score >= 5:
        reasons.append(f"license: {license_name}")
    if structure >= 10:
        reasons.append("complete skill structure")
    if risk_findings:
        reasons.append("safety warnings present")

    if any(f.startswith("high") for f in risk_findings) or repo.get("archived"):
        tier = "reject"
    elif score >= 75 and skill_paths and len(matched) >= 3:
        tier = "strict"
    elif score >= 60 and skill_paths and len(matched) >= 2:
        tier = "relaxed"
    elif score >= 45 and skill_paths:
        tier = "exploratory"
    else:
        tier = "reject"

    return round(score, 1), tier, matched, risk_findings, reasons


# Use the shared model below so live search and the offline demo cannot drift.
from curation_model import Candidate as SharedCandidate
from curation_model import score_repo as shared_score_repo
from curation_model import sort_candidates
from curation_model import terms_from_task as shared_terms_from_task

Candidate = SharedCandidate
score_repo = shared_score_repo
terms_from_task = shared_terms_from_task


def cache_root() -> str:
    root = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    path = os.path.join(root, "github-skill-curator")
    os.makedirs(path, exist_ok=True)
    return path


def cache_key(task: str, top: int, min_repos: int) -> str:
    payload = json.dumps({"task": task, "top": top, "min_repos": min_repos}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def load_cache(task: str, top: int, min_repos: int, cache_days: int) -> Optional[List[Candidate]]:
    if cache_days <= 0:
        return None
    path = os.path.join(cache_root(), cache_key(task, top, min_repos) + ".json")
    if not os.path.exists(path):
        return None
    age = time.time() - os.path.getmtime(path)
    if age > cache_days * 86400:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [Candidate(**x) for x in raw.get("candidates", [])]
    except Exception:
        return None


def save_cache(task: str, top: int, min_repos: int, candidates: List[Candidate]) -> None:
    path = os.path.join(cache_root(), cache_key(task, top, min_repos) + ".json")
    data = {"task": task, "saved_at": dt.datetime.now(dt.timezone.utc).isoformat(), "candidates": [asdict(c) for c in candidates]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def collect_candidates(task: str, top: int, min_repos: int) -> List[Candidate]:
    terms = terms_from_task(task)
    queries = build_queries(terms)
    repos: Dict[str, Dict[str, Any]] = {}
    for q in queries:
        try:
            for repo in search_repositories(q, per_page=max(top * 4, min_repos)):
                repos.setdefault(repo["full_name"], repo)
            time.sleep(0.2)
        except RuntimeError as e:
            print(f"warning: {e}", file=sys.stderr)
            break

    candidates: List[Candidate] = []
    for repo in repos.values():
        full = repo["full_name"]
        branch = repo.get("default_branch") or "main"
        try:
            tree = get_tree(full, branch)
        except Exception as e:
            print(f"warning: cannot inspect {full}: {e}", file=sys.stderr)
            continue
        skill_paths = [x.get("path", "") for x in tree if x.get("type") == "blob" and x.get("path", "").endswith("SKILL.md")]
        if not skill_paths:
            continue
        skill_texts = [get_file_text(full, branch, p) for p in skill_paths[:3]]
        score, tier, matched, risks, reasons = score_repo(repo, skill_paths, skill_texts, terms, tree)
        commands = [
            f"python3 scripts/install_skill.py {repo['html_url']} --skill-path {p.rsplit('/', 1)[0] if '/' in p else '.'}"
            for p in skill_paths[:5]
        ]
        candidates.append(Candidate(
            repo=full,
            url=repo["html_url"],
            description=repo.get("description") or "",
            stars=repo.get("stargazers_count") or 0,
            forks=repo.get("forks_count") or 0,
            open_issues=repo.get("open_issues_count") or 0,
            updated_at=repo.get("updated_at") or "",
            pushed_at=repo.get("pushed_at") or "",
            license=(repo.get("license") or {}).get("spdx_id") or "NOASSERTION",
            archived=bool(repo.get("archived")),
            default_branch=branch,
            skill_paths=skill_paths,
            matched_terms=matched,
            safety=risks,
            score=score,
            tier=tier,
            reasons=reasons,
            install_commands=commands,
        ))
    return sort_candidates(candidates)


def print_markdown(cands: List[Candidate], requested_tier: str, top: int) -> None:
    order = {"strict": 3, "relaxed": 2, "exploratory": 1, "reject": 0}
    min_level = order.get(requested_tier, 3)
    shown = [c for c in cands if order.get(c.tier, 0) >= min_level][:top]
    if not shown:
        print("No candidates met the requested tier. Try `--tier relaxed` or broader task terms.")
        return
    print(f"# GitHub skill candidates ({requested_tier}+)")
    print()
    print("| Rank | Repo | Tier | Score | Stars | Updated | License | Skill paths | Safety |")
    print("|---:|---|---|---:|---:|---|---|---|---|")
    for i, c in enumerate(shown, 1):
        updated = c.pushed_at[:10] or c.updated_at[:10]
        safety = "OK" if not c.safety else "; ".join(c.safety[:2])
        paths = "<br>".join(c.skill_paths[:3])
        print(f"| {i} | [{c.repo}]({c.url}) | {c.tier} | {c.score} | {c.stars} | {updated} | {c.license} | {paths} | {safety} |")
    print()
    for i, c in enumerate(shown, 1):
        print(f"## {i}. {c.repo}")
        print(c.description or "No description.")
        if c.reasons:
            print("- Reasons: " + "; ".join(c.reasons))
        if c.safety:
            print("- Safety warnings: " + "; ".join(c.safety))
        print("- Install command examples:")
        for cmd in c.install_commands[:3]:
            print(f"  - `{cmd}`")
        print()


def main() -> int:
    p = argparse.ArgumentParser(description="Find and score GitHub Agent Skills for a task.")
    p.add_argument("task", help="Task description or search terms")
    p.add_argument("--top", type=int, default=8, help="Number of candidates to show")
    p.add_argument("--tier", choices=["strict", "relaxed", "exploratory"], default="strict")
    p.add_argument("--json", action="store_true", help="Output JSON instead of Markdown")
    p.add_argument("--min-repos", type=int, default=24, help="How many GitHub repos to inspect before filtering")
    p.add_argument("--cache-days", type=int, default=7, help="Use cached results if newer than this many days; 0 disables cache")
    p.add_argument("--force-refresh", action="store_true", help="Ignore cache and query GitHub now")
    args = p.parse_args()

    cands = None if args.force_refresh else load_cache(args.task, args.top, args.min_repos, args.cache_days)
    if cands is None:
        cands = collect_candidates(args.task, top=args.top, min_repos=args.min_repos)
        save_cache(args.task, args.top, args.min_repos, cands)
    else:
        print(f"Using cached GitHub search results (<= {args.cache_days} days old). Use --force-refresh for latest results.", file=sys.stderr)
    if args.json:
        print(json.dumps([asdict(c) for c in cands], ensure_ascii=False, indent=2))
    else:
        print_markdown(cands, args.tier, args.top)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
