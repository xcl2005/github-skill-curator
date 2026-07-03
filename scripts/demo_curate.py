#!/usr/bin/env python3
"""Run a deterministic offline curation demo from a fixture index."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "examples" / "fixtures" / "sample-skill-index.json"
DEFAULT_OUT = ROOT / "examples" / "outputs" / "demo-curation-report.generated.md"


def load_candidates(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Fixture must contain a list of candidates")
    return data


def safety_label(flags: list[str]) -> str:
    if not flags:
        return "OK"
    if any(flag.startswith("high:") for flag in flags):
        return "High risk"
    return "Warning"


def render_report(candidates: list[dict[str, Any]], fixture: Path) -> str:
    sorted_candidates = sorted(candidates, key=lambda item: float(item.get("score", 0)), reverse=True)
    lines = [
        "# Offline Skill Curation Demo",
        "",
        f"Fixture: `{fixture.as_posix()}`",
        "",
        "This deterministic demo mirrors the review shape of `find_skills.py` without calling the GitHub API.",
        "",
        "| Rank | Candidate | Tier | Score | Stars | License | Safety | Decision |",
        "|---:|---|---|---:|---:|---|---|---|",
    ]
    for idx, item in enumerate(sorted_candidates, 1):
        flags = list(item.get("risk_flags") or [])
        lines.append(
            "| {rank} | `{repo}` | {tier} | {score:.1f} | {stars} | {license} | {safety} | {decision} |".format(
                rank=idx,
                repo=item.get("repo", ""),
                tier=item.get("tier", ""),
                score=float(item.get("score", 0)),
                stars=int(item.get("stars", 0)),
                license=item.get("license", "NOASSERTION"),
                safety=safety_label(flags),
                decision=item.get("decision", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Install boundary",
            "",
            "Only install the selected skill folder after review and user approval.",
            "",
            "## Rejected examples",
            "",
        ]
    )
    rejected = [item for item in sorted_candidates if item.get("tier") == "reject"]
    for item in rejected:
        flags = "; ".join(item.get("risk_flags") or ["unspecified risk"])
        lines.append(f"- `{item.get('repo')}`: {flags}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an offline skill curation demo.")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE), help="Fixture JSON path")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Markdown report path")
    args = parser.parse_args()

    fixture = Path(args.fixture)
    out = Path(args.out)
    candidates = load_candidates(fixture)
    report = render_report(candidates, fixture)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

