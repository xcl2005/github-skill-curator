#!/usr/bin/env python3
"""
Build a reviewable skill shortlist when no good curated index exists.

This script does not install anything. It gathers candidates with find_skills.py,
groups them by decision, and emits a concise Markdown report for human review.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_find_skills(task: str, top: int, tier: str, force_refresh: bool) -> list[dict]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "find_skills.py"),
        task,
        "--top",
        str(max(top, 12)),
        "--tier",
        tier,
        "--json",
    ]
    if force_refresh:
        cmd.append("--force-refresh")
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0 and not proc.stdout.strip():
        raise RuntimeError(proc.stderr.strip() or f"find_skills.py failed with exit code {proc.returncode}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Could not parse find_skills.py JSON output: {e}\n{proc.stdout[:500]}") from e


def decision_for(candidate: dict) -> str:
    tier = candidate.get("tier")
    safety = candidate.get("safety") or []
    score = float(candidate.get("score") or 0)
    paths = candidate.get("skill_paths") or []
    if tier == "reject" or any(str(x).startswith("high") for x in safety):
        return "reject"
    if tier == "strict" and score >= 75 and paths:
        return "installable_after_review"
    if tier in {"strict", "relaxed"} and score >= 60 and paths:
        return "review_candidate"
    return "watch_or_manual_inspect"


def print_report(task: str, candidates: list[dict], top: int) -> None:
    rows = []
    for c in candidates:
        row = dict(c)
        row["decision"] = decision_for(c)
        rows.append(row)
    order = {
        "installable_after_review": 0,
        "review_candidate": 1,
        "watch_or_manual_inspect": 2,
        "reject": 3,
    }
    rows.sort(key=lambda x: (order.get(x["decision"], 9), -float(x.get("score") or 0), -int(x.get("stars") or 0)))
    shown = rows[:top]
    print(f"# Skill roundup for: {task}")
    print()
    print("This is a human-review shortlist, not an auto-install list.")
    print()
    print("| Rank | Decision | Repo | Tier | Score | Stars | License | Skill paths | Safety |")
    print("|---:|---|---|---|---:|---:|---|---|---|")
    for i, c in enumerate(shown, 1):
        paths = "<br>".join((c.get("skill_paths") or [])[:3])
        safety = "OK" if not c.get("safety") else "; ".join(c["safety"][:2])
        print(
            f"| {i} | {c['decision']} | [{c.get('repo')}]({c.get('url')}) | {c.get('tier')} | "
            f"{c.get('score')} | {c.get('stars')} | {c.get('license')} | {paths} | {safety} |"
        )
    print()
    for i, c in enumerate(shown, 1):
        print(f"## {i}. {c.get('repo')} ({c['decision']})")
        if c.get("description"):
            print(c["description"])
        if c.get("reasons"):
            print("- Reasons: " + "; ".join(c["reasons"][:6]))
        print("- Install commands to review:")
        for cmd in (c.get("install_commands") or [])[:3]:
            print(f"  - `{cmd}`")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a reviewable skill candidate roundup.")
    parser.add_argument("task")
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--tier", choices=["strict", "relaxed", "exploratory"], default="relaxed")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--out", help="Write report to this Markdown file instead of stdout")
    args = parser.parse_args()
    candidates = run_find_skills(args.task, args.top, args.tier, args.force_refresh)
    if args.out:
        from contextlib import redirect_stdout

        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f, redirect_stdout(f):
            print_report(args.task, candidates, args.top)
        print(out)
    else:
        print_report(args.task, candidates, args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
