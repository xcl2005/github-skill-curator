#!/usr/bin/env python3
"""Validate the GitHub Skill Curator package without third-party deps."""
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "github-skill-curator"

REQUIRED_FILES = [
    "SKILL.md",
    "skill_manifest.yaml",
    "scripts/risk_scan.py",
    "scripts/curation_model.py",
    "scripts/demo_curate.py",
    "scripts/demo_audit_local.py",
    "scripts/find_skills.py",
    "scripts/install_skill.py",
    "scripts/audit_skills.py",
    "tests/test_curation_model.py",
    "tests/test_risk_scan.py",
    "references/decision_policy.md",
    "references/risk_model.md",
    "examples/fixtures/sample-skill-index.json",
    "examples/outputs/demo-curation-report.generated.md",
    "examples/outputs/local-skill-audit.generated.md",
    "examples/outputs/install-dry-run-unsafe.sample.json",
]

PROTECTED_SKILL_PHRASES = [
    "silently install unknown third-party skills",
    "run GitHub search for every small task",
    "install only after approval",
    "Before recommend / install / use",
    "scripts/risk_scan.py",
    "Do not recommend high-risk candidates",
    "references/decision_policy.md",
]

REQUIRED_RISK_MODEL_PHRASES = [
    "ignore previous instructions",
    ".env",
    "id_rsa",
    "curl ... | sh",
    "use this skill for all tasks",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def manifest_list_values(text: str) -> list[str]:
    values: list[str] = []
    for line in text.splitlines():
        match = re.match(r"\s*-\s+(.+?)\s*$", line)
        if match:
            values.append(match.group(1).strip().strip('"\''))
    return values


def validate_frontmatter(errors: list[str]) -> None:
    text = read("SKILL.md")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        errors.append("SKILL.md must start with YAML frontmatter")
        return
    frontmatter = match.group(1)
    name = re.search(r"(?m)^name:\s*['\"]?([^'\"\n]+)", frontmatter)
    description = re.search(r"(?m)^description:\s*(.+)", frontmatter)
    if not name or name.group(1).strip() != SKILL_NAME:
        errors.append(f"SKILL.md frontmatter name must be {SKILL_NAME!r}")
    if not description or not description.group(1).strip():
        errors.append("SKILL.md frontmatter description is missing")
    elif len(description.group(1).strip()) > 1024:
        errors.append("SKILL.md frontmatter description exceeds 1024 characters")


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errors.append(f"Missing required file: {rel}")

    if errors:
        for error in errors:
            print(f"- {error}")
        return 1

    validate_frontmatter(errors)

    skill_text = read("SKILL.md")
    for phrase in PROTECTED_SKILL_PHRASES:
        if phrase not in skill_text:
            errors.append(f"Protected phrase missing from SKILL.md: {phrase}")

    manifest_text = read("skill_manifest.yaml")
    if f"skill_name: {SKILL_NAME}" not in manifest_text:
        errors.append(f"skill_manifest.yaml skill_name must be {SKILL_NAME}")
    for rel in manifest_list_values(manifest_text):
        if rel.startswith(("scripts/", "examples/", "references/", "agents/")) and not (ROOT / rel).exists():
            errors.append(f"Manifest references missing path: {rel}")

    risk_text = read("references/risk_model.md")
    for phrase in REQUIRED_RISK_MODEL_PHRASES:
        if phrase not in risk_text:
            errors.append(f"Risk model missing phrase: {phrase}")

    readme = read("README.md")
    readme_en = read("README_EN.md")
    for rel in ["examples/outputs/demo-curation-report.generated.md", "scripts/demo_curate.py"]:
        if rel not in readme:
            errors.append(f"README.md should reference {rel}")
        if rel not in readme_en:
            errors.append(f"README_EN.md should reference {rel}")

    install_text = read("scripts/install_skill.py")
    if "--dry-run" not in install_text:
        errors.append("scripts/install_skill.py must support --dry-run")
    if "--local-repo" not in install_text:
        errors.append("scripts/install_skill.py must support --local-repo for fixture tests")
    if "from risk_scan import" not in install_text:
        errors.append("scripts/install_skill.py must use shared risk_scan")

    audit_text = read("scripts/audit_skills.py")
    if "from risk_scan import" not in audit_text:
        errors.append("scripts/audit_skills.py must use shared risk_scan")

    find_text = read("scripts/find_skills.py")
    if "from curation_model import" not in find_text:
        errors.append("scripts/find_skills.py must import the shared curation model")
    for forbidden in ["class Candidate", "def score_repo", "SUSPICIOUS_PATTERNS", "def terms_from_task", "def scan_text_for_risks"]:
        if forbidden in find_text:
            errors.append(f"scripts/find_skills.py should not redefine shared model logic: {forbidden}")

    demo_text = read("scripts/demo_curate.py")
    if "candidate_from_fixture" not in demo_text:
        errors.append("scripts/demo_curate.py must score fixtures through curation_model.candidate_from_fixture")

    for path in ["README.md", "README_EN.md"]:
        if read(path).count("|-- docs/") > 1:
            errors.append(f"{path} repository layout should not duplicate docs/")

    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Skill validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
