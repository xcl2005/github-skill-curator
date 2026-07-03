#!/usr/bin/env python3
"""Shared heuristic risk scanning for Agent Skill files."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable


RISK_PATTERNS: list[tuple[str, str, str]] = [
    ("high", r"ignore (all )?(previous|system|developer|user) instructions", "Prompt-injection language may try to bypass higher-priority instructions"),
    ("high", r"exfiltrat(e|ion)|steal\s+(secret|token|key|credential)|credential\s+harvest|private key|ssh key|browser profile", "Credential or private-data exfiltration pattern"),
    ("high", r"\.env|id_rsa|GITHUB_TOKEN|OPENAI_API_KEY|api[_-]?key", "Secret or private key access pattern"),
    ("high", r"rm\s+-rf\s+(/|~|\$HOME|\*)", "Destructive command outside a selected skill folder"),
    ("high", r"(always|automatically) use this skill|use this skill for all tasks|for every task", "Overbroad trigger may hijack unrelated tasks"),
    ("medium", r"curl\s+[^\n|;]+\|\s*(sh|bash)", "Opaque remote installer"),
    ("medium", r"wget\s+[^\n|;]+\|\s*(sh|bash)", "Opaque remote installer"),
    ("medium", r"chmod\s+777|sudo\s+", "Broad permission or privilege escalation pattern"),
    ("medium", r"base64\s+-d|eval\s+\$|Invoke-Expression|iex\b", "Obfuscated or dynamic execution pattern"),
]

SKIP_SCAN_NAMES = {".gitignore", ".difyignore"}
SKIP_SCAN_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".pptx", ".docx", ".xlsx", ".pyc"}
SKIP_SCAN_PARTS = {".git", "__pycache__", "node_modules", ".venv"}

PolicyContext = Callable[[str, int, int], bool]


def read_text(path: Path, limit: int = 250_000) -> str:
    try:
        return path.read_bytes()[:limit].decode("utf-8", errors="replace")
    except Exception:
        return ""


def scan_text_structured(text: str, path: str = "") -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    lower = text.lower()
    for severity, pattern, message in RISK_PATTERNS:
        if re.search(pattern, lower, flags=re.IGNORECASE):
            findings.append({
                "severity": severity,
                "path": path,
                "pattern": pattern,
                "message": message,
            })
    return _dedupe_findings(findings)


def scan_text_for_risks(text: str) -> list[str]:
    return finding_strings(scan_text_structured(text))


def scan_folder(folder: Path, policy_context: PolicyContext | None = None, max_size: int = 750_000) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in folder.rglob("*"):
        if path.name in SKIP_SCAN_NAMES:
            continue
        if path.suffix.lower() in SKIP_SCAN_SUFFIXES:
            continue
        if any(part in SKIP_SCAN_PARTS for part in path.parts):
            continue
        if not path.is_file() or path.stat().st_size > max_size:
            continue
        text = read_text(path)
        rel = str(path.relative_to(folder))
        for severity, pattern, message in RISK_PATTERNS:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match and not (policy_context and policy_context(text, match.start(), match.end())):
                findings.append({
                    "severity": severity,
                    "path": rel,
                    "pattern": pattern,
                    "message": message,
                })
    return _dedupe_findings(findings)


def finding_strings(findings: list[dict[str, str]] | list[str]) -> list[str]:
    if not findings:
        return []
    if isinstance(findings[0], str):
        return list(dict.fromkeys(findings))  # type: ignore[arg-type]
    strings: list[str] = []
    for finding in findings:  # type: ignore[assignment]
        path = finding.get("path") or "<text>"
        strings.append(f"{finding.get('severity')}: {path}: `{finding.get('pattern')}`")
    return list(dict.fromkeys(strings))


def risk_level(findings: list[dict[str, str]] | list[str]) -> str:
    if not findings:
        return "ok"
    severities: list[str] = []
    for finding in findings:
        if isinstance(finding, str):
            severities.append(finding.split(":", 1)[0])
        else:
            severities.append(finding.get("severity", ""))
    if "high" in severities:
        return "high"
    if "medium" in severities:
        return "medium"
    return "ok"


def safety_label(findings: list[dict[str, str]] | list[str]) -> str:
    level = risk_level(findings)
    if level == "high":
        return "High risk"
    if level == "medium":
        return "Warning"
    return "OK"


def _dedupe_findings(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, str]] = []
    for finding in findings:
        key = (finding.get("severity", ""), finding.get("path", ""), finding.get("pattern", ""))
        if key not in seen:
            seen.add(key)
            result.append(finding)
    return result
