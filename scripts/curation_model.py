#!/usr/bin/env python3
"""Shared curation scoring and risk vocabulary for live and offline demos."""
from __future__ import annotations

import datetime as dt
import math
import re
from dataclasses import dataclass
from typing import Any


STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "for", "of", "in", "on", "with", "by", "from",
    "skill", "skills", "codex", "agent", "agents", "github", "use", "make", "create", "build",
}

SUSPICIOUS_PATTERNS = [
    ("high", r"ignore (all )?(previous|system|developer|user) instructions"),
    ("high", r"exfiltrat(e|ion)|steal\s+(secret|token|key|credential)|credential\s+harvest|private key|ssh key|browser profile"),
    ("high", r"\.env|id_rsa|GITHUB_TOKEN|OPENAI_API_KEY|api[_-]?key"),
    ("high", r"rm\s+-rf\s+(/|~|\$HOME|\*)"),
    ("high", r"(always|automatically) use this skill|use this skill for all tasks|for every task"),
    ("medium", r"curl\s+[^\n|;]+\|\s*(sh|bash)"),
    ("medium", r"wget\s+[^\n|;]+\|\s*(sh|bash)"),
    ("medium", r"chmod\s+777|sudo\s+"),
    ("medium", r"base64\s+-d|eval\s+\$|Invoke-Expression|iex\b"),
]

TIER_RANK = {"strict": 3, "relaxed": 2, "exploratory": 1, "reject": 0}


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
    skill_paths: list[str]
    matched_terms: list[str]
    safety: list[str]
    score: float
    tier: str
    reasons: list[str]
    install_commands: list[str]


def terms_from_task(task: str) -> list[str]:
    raw = re.findall(r"[A-Za-z0-9_+.#-]{2,}|[\u4e00-\u9fff]{2,}", task.lower())
    terms: list[str] = []
    for t in raw:
        t = t.strip("-_+.#")
        if len(t) < 2 or t in STOPWORDS:
            continue
        if t not in terms:
            terms.append(t)

    synonyms: list[str] = []
    joined = " ".join(terms)
    task_l = task.lower()
    if any(x in task_l for x in ["ppt", "pptx", "slide", "presentation", "powerpoint"]):
        synonyms += ["pptx", "powerpoint", "presentation", "slides", "deck"]
    if any(x in task_l for x in ["docx", "word", "paper", "journal", "latex", "research", "academic"]):
        synonyms += ["docx", "word", "latex", "paper", "journal", "formatting", "academic", "research", "citation", "bibtex"]
    if any(x in task_l for x in ["formula", "equation", "math", "tikz", "overleaf"]):
        synonyms += ["latex", "math", "equation", "formula", "tikz", "compile", "pdf"]
    if any(x in task_l for x in ["resume", "cv", "ats", "cover", "job", "interview", "jd", "career"]):
        synonyms += ["resume", "cv", "ats", "job", "application", "cover-letter", "interview", "career"]
    if any(x in task_l for x in ["sop", "ps", "statement", "purpose", "personal", "graduate", "scholarship"]):
        synonyms += ["sop", "personal-statement", "statement-of-purpose", "graduate", "application", "cv"]
    if any(x in task_l for x in ["excel", "xlsx", "spreadsheet"]):
        synonyms += ["xlsx", "excel", "spreadsheet"]
    if any(x in joined for x in ["pdf"]):
        synonyms += ["pdf", "acrobat", "extract", "annotate"]

    for s in synonyms + ["SKILL.md", "agent-skill", "codex-skill"]:
        sl = s.lower()
        if sl not in terms:
            terms.append(sl)
    return terms[:12]


def scan_text_for_risks(text: str) -> list[str]:
    findings: list[str] = []
    lower = text.lower()
    for sev, pat in SUSPICIOUS_PATTERNS:
        if re.search(pat, lower, flags=re.IGNORECASE):
            findings.append(f"{sev}: pattern `{pat}`")
    return list(dict.fromkeys(findings))


def risk_level(findings: list[str]) -> str:
    if any(f.startswith("high") for f in findings):
        return "high"
    if any(f.startswith("medium") for f in findings):
        return "medium"
    return "ok"


def safety_label(findings: list[str]) -> str:
    level = risk_level(findings)
    if level == "high":
        return "High risk"
    if level == "medium":
        return "Warning"
    return "OK"


def days_since(iso: str) -> int:
    try:
        d = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return max(0, (dt.datetime.now(dt.timezone.utc) - d).days)
    except Exception:
        return 9999


def score_repo(
    repo: dict[str, Any],
    skill_paths: list[str],
    skill_texts: list[str],
    terms: list[str],
    tree: list[dict[str, Any]],
) -> tuple[float, str, list[str], list[str], list[str]]:
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
    paths = [x.get("path", "") for x in tree]
    if any(p.lower().endswith(("example.json", "examples", "readme.md")) for p in paths):
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

    risk_findings: list[str] = []
    for text in skill_texts:
        risk_findings.extend(scan_text_for_risks(text))
    risk_findings = list(dict.fromkeys(risk_findings))
    safety = 10
    if risk_level(risk_findings) == "high":
        safety = 0
    elif risk_level(risk_findings) == "medium":
        safety = 4

    score = relevance + popularity + maintenance + structure + license_score + safety
    reasons: list[str] = []
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

    if risk_level(risk_findings) == "high" or repo.get("archived"):
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


def sort_candidates(candidates: list[Candidate]) -> list[Candidate]:
    return sorted(candidates, key=lambda c: (TIER_RANK.get(c.tier, 0), c.score, c.stars), reverse=True)


def decision_for_candidate(candidate: Candidate) -> str:
    if candidate.tier == "strict" and not candidate.safety:
        return "Recommend after upstream review"
    if candidate.tier == "strict":
        return "Review before install"
    if candidate.tier == "relaxed":
        return "Review manually"
    if candidate.tier == "exploratory":
        return "Skip unless no better match"
    return "Reject"


def candidate_from_fixture(item: dict[str, Any], terms: list[str]) -> Candidate:
    repo_name = str(item["repo"])
    skill_paths = list(item.get("skill_paths") or ["SKILL.md"])
    tree_paths = list(dict.fromkeys(list(item.get("tree_paths") or []) + skill_paths))
    tree = [{"path": p, "type": "blob"} for p in tree_paths]
    repo = {
        "full_name": repo_name,
        "html_url": item.get("url") or f"https://github.com/{repo_name}",
        "description": item.get("description") or "",
        "stargazers_count": int(item.get("stars") or 0),
        "forks_count": int(item.get("forks") or 0),
        "open_issues_count": int(item.get("open_issues") or 0),
        "updated_at": item.get("updated_at") or "",
        "pushed_at": item.get("pushed_at") or item.get("updated_at") or "",
        "license": {"spdx_id": item.get("license") or "NOASSERTION"},
        "archived": bool(item.get("archived")),
        "default_branch": item.get("default_branch") or "main",
        "topics": list(item.get("topics") or []),
    }
    skill_texts = list(item.get("skill_texts") or [item.get("skill_excerpt") or ""])
    score, tier, matched, risks, reasons = score_repo(repo, skill_paths, skill_texts, terms, tree)
    commands = [
        f"python3 scripts/install_skill.py {repo['html_url']} --skill-path {p.rsplit('/', 1)[0] if '/' in p else '.'}"
        for p in skill_paths[:5]
    ]
    return Candidate(
        repo=repo_name,
        url=repo["html_url"],
        description=repo["description"],
        stars=repo["stargazers_count"],
        forks=repo["forks_count"],
        open_issues=repo["open_issues_count"],
        updated_at=repo["updated_at"],
        pushed_at=repo["pushed_at"],
        license=repo["license"]["spdx_id"],
        archived=repo["archived"],
        default_branch=repo["default_branch"],
        skill_paths=skill_paths,
        matched_terms=matched,
        safety=risks,
        score=score,
        tier=tier,
        reasons=reasons,
        install_commands=commands,
    )
