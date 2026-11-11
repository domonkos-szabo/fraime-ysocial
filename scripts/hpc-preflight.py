#!/usr/bin/env python3
"""Read-only FRAIME YSocial / YPhotoSharing HPC preflight.

Run against the persistent experiment directory, even while the YSocial service is stopped.
No application imports, subprocesses, network calls, or writes.
"""
import argparse
import json
import os
from pathlib import Path
import sys

def check(root: Path, stage: str) -> int:
    print(f"[FRAIME HPC] stage={stage} root={root}")
    if not root.is_dir():
        print("[FAIL] Experiment directory missing")
        return 2
    failures = 0
    for filename in ("server_config.json", "prompts_ygram.json"):
        p = root / filename
        if not p.is_file():
            print(f"[FAIL] Missing {filename}")
            failures += 1
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(obj, dict) or not obj:
                raise ValueError("empty or non-object JSON")
            print(f"[OK] {filename} ({len(obj)} keys)")
        except (OSError, ValueError) as exc:
            print(f"[FAIL] Invalid {filename}: {exc}")
            failures += 1
    clients = sorted(root.glob("client_*.json"))
    if not clients:
        print("[FAIL] No client_*.json files")
        failures += 1
    for p in clients:
        try:
            conf = json.loads(p.read_text(encoding="utf-8"))
            llm = conf.get("servers", {}).get("llm", "")
            models = conf.get("agents", {}).get("llm_agents", [])
            print(f"[CLIENT] {p.name} llm_url={llm!r} models={models!r}")
            if not isinstance(llm, str) or not llm.startswith(("http://", "https://")):
                print("[FAIL] Client LLM URL is not an HTTP(S) endpoint")
                failures += 1
            if not models or models == [None]:
                print("[FAIL] Client has no LLM agent model")
                failures += 1
            image_cfg = conf.get("image_generation", {})
            if image_cfg.get("enabled") or image_cfg.get("use_local_diffusion"):
                print("[WARN] Image generation is enabled; this can overload a CPU-only host")
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            print(f"[FAIL] Invalid client {p.name}: {exc}")
            failures += 1
    for marker in ("ray_config.temp", "ray_namespace.temp", "ray_ready.temp"):
        p = root / marker
        present = p.exists()
        print(f"[RAY] {marker}: {'present' if present else 'absent'}")
        if stage == "server" and marker in ("ray_config.temp", "ray_ready.temp") and not present:
            failures += 1
    logdir = root / "logs"
    if logdir.is_dir():
        logs = sorted((p for p in logdir.rglob("*") if p.is_file() and p.suffix in (".log", ".err", ".out")), key=lambda p: p.stat().st_mtime, reverse=True)[:8]
        for p in logs:
            print(f"[LOG] {p.relative_to(root)} ({p.stat().st_size} bytes)")
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in lines[-12:]:
                print("  " + line[:300])
    else:
        print("[WARN] No experiment logs/ folder")
    print(f"[RESULT] {'FAIL' if failures else 'PASS'} ({failures} issues)")
    return 1 if failures else 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("prestart", "server"), default="prestart")
    args = parser.parse_args()
    return check(args.root, args.stage)

if __name__ == "__main__":
    sys.exit(main())
