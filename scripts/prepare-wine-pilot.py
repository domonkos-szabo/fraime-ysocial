#!/usr/bin/env python3
"""Explicit, backed-up preparation of an *unstarted* FRAIME wine pilot.

No automatic migrations, no database changes, no state reset. Run against a
fresh experiment before first client launch. Dry-run unless --apply is passed.
"""
import argparse
import json
import shutil
from pathlib import Path

TOPICS = [
    "Italian wine",
    "vineyard life",
    "food pairing",
    "sustainable viticulture",
    "wine tourism",
]

def visit_agents(node):
    if isinstance(node, dict):
        if "activity_profile" in node and ("daily_activity_level" in node or "round_actions" in node):
            yield node
        for value in node.values():
            yield from visit_agents(value)
    elif isinstance(node, list):
        for value in node:
            yield from visit_agents(value)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path)
    parser.add_argument("--apply", action="store_true", help="Write config after backups")
    args = parser.parse_args()
    d = args.experiment_dir
    population_file = d / "fraime_wine_pilot_5.json"
    client_files = sorted(d.glob("client_*-fraime_wine_pilot_5.json"))
    if not population_file.is_file() or not client_files:
        raise SystemExit("Missing population or client configuration; no changes made")
    if list(d.glob("*.state.json")):
        raise SystemExit("Experiment already has client state. Use a fresh experiment, not this one.")
    pending = []
    population = json.loads(population_file.read_text())
    agents = list(visit_agents(population))
    if len(agents) != 5:
        raise SystemExit(f"Expected exactly 5 wine agents, found {len(agents)}; no changes made")
    for agent in agents:
        agent["interests"] = list(TOPICS)
        agent["llm"] = True
    pending.append((population_file, population))
    for path in client_files:
        c = json.loads(path.read_text())
        llm = c.get("llm")
        if not isinstance(llm, dict):
            raise SystemExit(f"Missing llm configuration in {path}")
        base_url = str(llm.get("base_url") or "").rstrip("/")
        if not base_url.endswith("/v1"):
            raise SystemExit(f"Expected OpenAI-compatible /v1 URL in {path}; no changes made")
        llm["backend"] = "openai_compatible"
        c.setdefault("simulation", {})["discussion_topics"] = list(TOPICS)
        pending.append((path, c))
    print("Wine agents:", len(agents), "Topics:", ", ".join(TOPICS))
    print("Mode:", "APPLY" if args.apply else "DRY RUN")
    for path, obj in pending:
        print("Config:", path)
        if args.apply:
            backup = path.with_name(path.name + ".before-wine-pilot.bak")
            if not backup.exists():
                shutil.copy2(path, backup)
            path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
    print("Complete. Existing SQLite databases and simulation state untouched.")

if __name__ == "__main__":
    main()
