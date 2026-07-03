#!/usr/bin/env python3
"""Generate a deterministic local-skill audit demo from fixtures."""
from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import tempfile
from pathlib import Path

from audit_skills import audit, render_markdown


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "examples" / "fixtures" / "unsafe-skill"
DEFAULT_AS_OF = "2026-07-03"


def timestamp_for(date_text: str) -> float:
    return dt.datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()


def set_tree_mtime(root: Path, timestamp: float) -> None:
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        os.utime(path, (timestamp, timestamp))
    os.utime(root, (timestamp, timestamp))


def build_demo(fixture: Path, as_of: str) -> str:
    fixed_time = timestamp_for(as_of)
    with tempfile.TemporaryDirectory(prefix="skill-curator-audit-demo-") as tmp:
        dest = Path(tmp) / "local-skills"
        target = dest / fixture.name
        shutil.copytree(fixture, target)
        set_tree_mtime(target, fixed_time)
        rows = audit(dest, as_of=fixed_time)
    return render_markdown(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic local skill audit report.")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE), help="Fixture skill folder to audit")
    parser.add_argument("--as-of", default=DEFAULT_AS_OF, help="Fixed report date in YYYY-MM-DD")
    parser.add_argument("--out", help="Write Markdown report to this path")
    args = parser.parse_args()

    report = build_demo(Path(args.fixture), args.as_of)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
