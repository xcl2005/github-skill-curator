#!/usr/bin/env python3
"""Find and rank GitHub repositories that contain Agent Skill packages."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict
from typing import Any

from curation_model import Candidate, decision_for_candidate, risk_level, score_repo, sort_candidates, terms_from_task


API = "https://api.github.com"
USER_AGENT = "github-skill-curator/1.1"


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
            raise RuntimeError(
                f"GitHub rate limit or permission issue ({e.code}). Set GITHUB_TOKEN for higher limits. {msg}"
            ) from e
        raise


def build_queries(terms: list[str]) -> list[str]:
    core = " ".join(terms[:6])
    queries = [
        f'{core} "SKILL.md"',
        f"{core} agent-skill",
        f"{core} codex-skill",
    ]
    seen: list[str] = []
    for query in queries:
        query = query.strip()
        if query and query not in seen:
            seen.append(query)
    return seen


def search_repositories(query: str, per_page: int) -> list[dict[str, Any]]:
    q = f"{query} in:name,description,readme"
    url = "/search/repositories?" + urllib.parse.urlencode({
        "q": q,
        "sort": "stars",
        "order": "desc",
        "per_page": min(per_page, 50),
    })
    data = github_request(url)
    return data.get("items", []) if isinstance(data, dict) else []


def get_tree(repo_full_name: str, branch: str) -> list[dict[str, Any]]:
    encoded = urllib.parse.quote(repo_full_name, safe="/")
    ref = urllib.parse.quote(branch, safe="")
    data = github_request(f"/repos/{encoded}/git/trees/{ref}?recursive=1")
    if not isinstance(data, dict) or "tree" not in data:
        return []
    return data["tree"]


def get_file_text(repo_full_name: str, branch: str, path: str, max_bytes: int = 16_000) -> str:
    raw = f"https://raw.githubusercontent.com/{repo_full_name}/{urllib.parse.quote(branch, safe='')}/{path}"
    req = urllib.request.Request(raw, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read(max_bytes).decode("utf-8", errors="replace")
    except Exception:
        return ""


def cache_root() -> str:
    root = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    path = os.path.join(root, "github-skill-curator")
    os.makedirs(path, exist_ok=True)
    return path


def cache_key(task: str, top: int, min_repos: int) -> str:
    payload = json.dumps({"task": task, "top": top, "min_repos": min_repos}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def load_cache(task: str, top: int, min_repos: int, cache_days: int) -> list[Candidate] | None:
    if cache_days <= 0:
        return None
    path = os.path.join(cache_root(), cache_key(task, top, min_repos) + ".json")
    if not os.path.exists(path):
        return None
    if time.time() - os.path.getmtime(path) > cache_days * 86_400:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [Candidate(**item) for item in raw.get("candidates", [])]
    except Exception:
        return None


def save_cache(task: str, top: int, min_repos: int, candidates: list[Candidate]) -> None:
    path = os.path.join(cache_root(), cache_key(task, top, min_repos) + ".json")
    data = {
        "task": task,
        "saved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "candidates": [asdict(c) for c in candidates],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def collect_candidates(task: str, top: int, min_repos: int) -> list[Candidate]:
    terms = terms_from_task(task)
    repos: dict[str, dict[str, Any]] = {}
    for query in build_queries(terms):
        try:
            for repo in search_repositories(query, per_page=max(top * 4, min_repos)):
                repos.setdefault(repo["full_name"], repo)
            time.sleep(0.2)
        except RuntimeError as e:
            print(f"warning: {e}", file=sys.stderr)
            break

    candidates: list[Candidate] = []
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
        skill_texts = [get_file_text(full, branch, path) for path in skill_paths[:3]]
        score, tier, matched, risks, reasons = score_repo(repo, skill_paths, skill_texts, terms, tree)
        commands = [
            f"python3 scripts/install_skill.py {repo['html_url']} --skill-path {path.rsplit('/', 1)[0] if '/' in path else '.'}"
            for path in skill_paths[:5]
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


def candidate_json(candidate: Candidate) -> dict[str, Any]:
    data = asdict(candidate)
    data["decision"] = decision_for_candidate(candidate)
    data["safety_level"] = risk_level(candidate.safety)
    data["safety_findings"] = candidate.safety
    return data


def print_json(task: str, candidates: list[Candidate], cache_used: bool) -> None:
    payload = {
        "task": task,
        "query_terms": terms_from_task(task),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": "cache" if cache_used else "github_search",
        "cache_used": cache_used,
        "candidates": [candidate_json(candidate) for candidate in candidates],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_markdown(candidates: list[Candidate], requested_tier: str, top: int) -> None:
    order = {"strict": 3, "relaxed": 2, "exploratory": 1, "reject": 0}
    min_level = order.get(requested_tier, 3)
    shown = [c for c in candidates if order.get(c.tier, 0) >= min_level][:top]
    if not shown:
        print("No candidates met the requested tier. Try `--tier relaxed` or broader task terms.")
        return
    print(f"# GitHub skill candidates ({requested_tier}+)")
    print()
    print("| Rank | Repo | Tier | Score | Stars | Updated | License | Skill paths | Safety |")
    print("|---:|---|---|---:|---:|---|---|---|---|")
    for index, candidate in enumerate(shown, 1):
        updated = candidate.pushed_at[:10] or candidate.updated_at[:10]
        safety = "OK" if not candidate.safety else "; ".join(candidate.safety[:2])
        paths = "<br>".join(candidate.skill_paths[:3])
        print(f"| {index} | [{candidate.repo}]({candidate.url}) | {candidate.tier} | {candidate.score} | {candidate.stars} | {updated} | {candidate.license} | {paths} | {safety} |")
    print()
    for index, candidate in enumerate(shown, 1):
        print(f"## {index}. {candidate.repo}")
        print(candidate.description or "No description.")
        print(f"- Decision: {decision_for_candidate(candidate)}")
        if candidate.reasons:
            print("- Reasons: " + "; ".join(candidate.reasons))
        if candidate.safety:
            print("- Safety warnings: " + "; ".join(candidate.safety))
        print("- Install command examples:")
        for cmd in candidate.install_commands[:3]:
            print(f"  - `{cmd}`")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Find and score GitHub Agent Skills for a task.")
    parser.add_argument("task", help="Task description or search terms")
    parser.add_argument("--top", type=int, default=8, help="Number of candidates to show")
    parser.add_argument("--tier", choices=["strict", "relaxed", "exploratory"], default="strict")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--min-repos", type=int, default=24, help="How many GitHub repos to inspect before filtering")
    parser.add_argument("--cache-days", type=int, default=7, help="Use cached results if newer than this many days; 0 disables cache")
    parser.add_argument("--force-refresh", action="store_true", help="Ignore cache and query GitHub now")
    args = parser.parse_args()

    cache_used = False
    candidates = None if args.force_refresh else load_cache(args.task, args.top, args.min_repos, args.cache_days)
    if candidates is None:
        candidates = collect_candidates(args.task, top=args.top, min_repos=args.min_repos)
        save_cache(args.task, args.top, args.min_repos, candidates)
    else:
        cache_used = True
        print(f"Using cached GitHub search results (<= {args.cache_days} days old). Use --force-refresh for latest results.", file=sys.stderr)

    if args.json:
        print_json(args.task, candidates, cache_used)
    else:
        print_markdown(candidates, args.tier, args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
