#!/usr/bin/env python3
"""
Classify a user task into high-value skill discovery lanes and recommend or run
fresh GitHub skill searches.

Examples:
  python3 scripts/task_skill_radar.py "帮我写港硕申请 PS 和简历"
  python3 scripts/task_skill_radar.py "rewrite my ML paper abstract and fix LaTeX formulas" --run-search
  python3 scripts/task_skill_radar.py "做 PPT" --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import shlex
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
LANES_FILE = ROOT / "references" / "high_value_discovery_lanes.json"
KNOWN_FILE = ROOT / "references" / "known_good_skills.json"
CURATED_INDEX_FILE = ROOT / "references" / "curated_skill_indexes.json"


def default_dest() -> Path:
    if os.environ.get("CODEX_SKILLS_DIR"):
        return Path(os.environ["CODEX_SKILLS_DIR"]).expanduser()
    return Path.home() / ".agents" / "skills"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_curated_indexes() -> list[dict[str, Any]]:
    if not CURATED_INDEX_FILE.exists():
        return []
    return load_json(CURATED_INDEX_FILE).get("indexes", [])


def installed_skills(dest: Path) -> Dict[str, Dict[str, str]]:
    found: Dict[str, Dict[str, str]] = {}
    if not dest.exists():
        return found
    for child in dest.iterdir():
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.exists():
            continue
        text = skill_md.read_text(encoding="utf-8", errors="replace")[:6000]
        name = child.name
        desc = ""
        for line in text.splitlines()[:30]:
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip().strip('"\'') or name
            if line.startswith("description:"):
                desc = line.split(":", 1)[1].strip().strip('"\'')
        found[name.lower()] = {"name": name, "path": str(child), "description": desc}
    return found


def normalized_contains(text: str, trigger: str) -> bool:
    text_l = text.lower()
    trig_l = trigger.lower()
    if re.search(r"[\u4e00-\u9fff]", trig_l):
        return trig_l in text_l
    return bool(re.search(r"\b" + re.escape(trig_l) + r"\b", text_l)) or trig_l in text_l


def classify(task: str, lanes: Dict[str, Any]) -> List[Tuple[str, int, List[str]]]:
    matches: List[Tuple[str, int, List[str]]] = []
    for key, lane in lanes.items():
        hit = [t for t in lane.get("triggers", []) if normalized_contains(task, t)]
        if hit:
            score = len(hit) * 10
            if lane.get("priority") == "high":
                score += 5
            matches.append((key, score, hit[:8]))
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def skill_hint_matches(installed: Dict[str, Dict[str, str]], lane: Dict[str, Any]) -> List[str]:
    hay = "\n".join((v["name"] + " " + v.get("description", "")).lower() for v in installed.values())
    hits: List[str] = []
    for c in lane.get("seed_candidates", []):
        name = c.get("repo", "").split("/")[-1].lower()
        path = c.get("skill_path", "").split("/")[-1].lower()
        for token in {name, path, c.get("repo", "").lower()}:
            if token and token != "." and token in hay:
                hits.append(c.get("repo", token))
                break
    return list(dict.fromkeys(hits))


def curated_index_matches(task: str, lane_key: str, lane: Dict[str, Any]) -> list[dict[str, Any]]:
    task_l = task.lower()
    lane_text = " ".join([lane_key, lane.get("label", ""), " ".join(lane.get("triggers", []))]).lower()
    rows: list[dict[str, Any]] = []
    for item in load_curated_indexes():
        domains = [str(x).lower() for x in item.get("domains", [])]
        if item.get("name", "").lower() in task_l:
            rows.append(item)
            continue
        if any(domain in task_l or domain in lane_text for domain in domains):
            rows.append(item)
            continue
        if lane_key == "skill_ecosystem_scan" and item.get("status") in {"curated-index", "index-only"}:
            rows.append(item)
    return rows


def print_report(task: str, dest: Path, run_search: bool, top: int, tier: str, force_refresh: bool, as_json: bool) -> int:
    data = load_json(LANES_FILE)
    lanes = data["lanes"]
    matches = classify(task, lanes)
    installed = installed_skills(dest)

    report: Dict[str, Any] = {
        "task": task,
        "dest": str(dest),
        "matched_lanes": [],
        "installed_skill_count": len(installed),
    }

    if not matches:
        report["message"] = "No high-value discovery lane matched. Use generic find_skills.py if a specialized skill may still help."
        if as_json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print("No high-value discovery lane matched.")
            print("Generic command:")
            print(f"  python3 scripts/find_skills.py {task!r} --top {top} --tier {tier}")
        return 1

    for key, score, hits in matches[:5]:
        lane = lanes[key]
        local_hits = skill_hint_matches(installed, lane)
        entry = {
            "key": key,
            "label": lane["label"],
            "priority": lane.get("priority"),
            "install_policy": lane.get("install_policy"),
            "cache_days": lane.get("cache_days", 7),
            "trigger_hits": hits,
            "local_seed_hits": local_hits,
            "seed_candidates": lane.get("seed_candidates", []),
            "curated_indexes": curated_index_matches(task, key, lane),
            "queries": lane.get("queries", []),
            "curated_index_queries": lane.get("curated_index_queries", []),
            "commands": [],
            "curated_index_commands": [],
            "roundup_command": "",
        }
        for q in lane.get("curated_index_queries", [])[:4]:
            cmd = [sys.executable, str(ROOT / "scripts" / "find_curated_indexes.py"), q, "--top", str(top)]
            if force_refresh or lane.get("force_refresh_before_important_work"):
                cmd.append("--search-github")
            entry["curated_index_commands"].append(shlex.join(cmd))
        for q in lane.get("queries", [])[:4]:
            cmd = [sys.executable, str(ROOT / "scripts" / "find_skills.py"), q, "--top", str(top), "--tier", tier, "--cache-days", str(lane.get("cache_days", 7))]
            if force_refresh or lane.get("force_refresh_before_important_work"):
                cmd.append("--force-refresh")
            entry["commands"].append(shlex.join(cmd))
            if run_search:
                print("\n$", " ".join(cmd), file=sys.stderr)
                subprocess.run(cmd, check=False)
        roundup = [sys.executable, str(ROOT / "scripts" / "build_skill_roundup.py"), task, "--top", str(max(top, 12))]
        if force_refresh:
            roundup.append("--force-refresh")
        entry["roundup_command"] = shlex.join(roundup)
        report["matched_lanes"].append(entry)

    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"# Skill radar for: {task}")
    print(f"Destination: {dest}")
    print(f"Installed skill count: {len(installed)}")
    print()
    for entry in report["matched_lanes"]:
        print(f"## {entry['label']} ({entry['key']})")
        print(f"- Priority: {entry['priority']}")
        print(f"- Install policy: {entry['install_policy']}")
        print(f"- Trigger hits: {', '.join(entry['trigger_hits'])}")
        if entry["local_seed_hits"]:
            print(f"- Local possible matches: {', '.join(entry['local_seed_hits'])}")
        else:
            print("- Local possible matches: none from seed list")
        if entry["seed_candidates"]:
            print("- Seed candidates to inspect first:")
            for c in entry["seed_candidates"][:6]:
                print(f"  - {c.get('repo')} ({c.get('status')}): {c.get('why')}")
        if entry["curated_indexes"]:
            print("- Curated indexes to inspect first:")
            for c in entry["curated_indexes"][:6]:
                print(f"  - {c.get('repo')} ({c.get('status')}): {c.get('why')}")
        if entry["curated_index_commands"]:
            print("- Curated index commands:")
            for cmd in entry["curated_index_commands"][:4]:
                print(f"  - `{cmd}`")
        print("- Fresh search commands:")
        for cmd in entry["commands"][:4]:
            print(f"  - `{cmd}`")
        print(f"- If no curated index is good enough, build a human-review roundup: `{entry['roundup_command']}`")
        print()
    if not run_search:
        print("Run again with --run-search to execute these searches now.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Classify high-value tasks and recommend fresh GitHub skill searches.")
    ap.add_argument("task", help="User task description")
    ap.add_argument("--dest", default=str(default_dest()), help="Destination skills directory to inspect")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--tier", choices=["strict", "relaxed", "exploratory"], default="relaxed")
    ap.add_argument("--run-search", action="store_true", help="Execute recommended find_skills.py searches")
    ap.add_argument("--force-refresh", action="store_true", help="Force fresh GitHub searches even if the lane would allow cache")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    return print_report(args.task, Path(args.dest).expanduser(), args.run_search, args.top, args.tier, args.force_refresh, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
