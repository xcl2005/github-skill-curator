#!/usr/bin/env python3
"""Run a deterministic offline curation demo from a fixture index."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from curation_model import candidate_from_fixture, decision_for_candidate, safety_label, sort_candidates, terms_from_task


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "examples" / "fixtures" / "sample-skill-index.json"
DEFAULT_OUT = ROOT / "examples" / "outputs" / "demo-curation-report.generated.md"
DEFAULT_TASK = "PowerPoint PPTX editable presentation Agent Skill"


def load_candidates(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Fixture must contain a list of candidates")
    return data


def render_report(candidates: list[dict[str, Any]], fixture: Path) -> str:
    terms = terms_from_task(DEFAULT_TASK)
    scored = sort_candidates([candidate_from_fixture(item, terms) for item in candidates])
    try:
        fixture_display = fixture.relative_to(ROOT).as_posix()
    except ValueError:
        fixture_display = fixture.as_posix()
    lines = [
        "# Offline Skill Curation Demo",
        "",
        f"Fixture: `{fixture_display}`",
        "",
        "This deterministic demo uses the same curation model as `find_skills.py` without calling the GitHub API.",
        "",
        "| Rank | Candidate | Tier | Score | Stars | License | Safety | Decision |",
        "|---:|---|---|---:|---:|---|---|---|",
    ]
    for idx, item in enumerate(scored, 1):
        lines.append(
            "| {rank} | `{repo}` | {tier} | {score:.1f} | {stars} | {license} | {safety} | {decision} |".format(
                rank=idx,
                repo=item.repo,
                tier=item.tier,
                score=item.score,
                stars=item.stars,
                license=item.license,
                safety=safety_label(item.safety),
                decision=decision_for_candidate(item),
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
    rejected = [item for item in scored if item.tier == "reject"]
    for item in rejected:
        flags = "; ".join(item.safety or ["tier rejected by score or metadata"])
        lines.append(f"- `{item.repo}`: {flags}")
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
