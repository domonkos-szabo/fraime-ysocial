#!/usr/bin/env python3
"""Idempotent compatibility patch for pinned YPhotoSharing v2.1.0.

Only touches the LLM service in the installed plugin; the experiment database,
agent population and client state are never modified. A backup of the original
module is retained when patching the persistent /data plugin for the first time.
"""
from __future__ import annotations

import argparse
import py_compile
from pathlib import Path

ANCHOR = 'from langchain_ollama import ChatOllama\n'
ANCHOR_REPLACEMENT = 'from langchain_ollama import ChatOllama\nfrom langchain_openai import ChatOpenAI\n'
ORIGINAL = '''        base_url = _build_ollama_url(llm_config)
        self.llm = ChatOllama(
            model=llm_config.get("model", "llama3.2"),
            temperature=llm_config.get("temperature", 0.7),
            base_url=base_url,
        )
'''
REPLACEMENT = '''        # FRAIME: older experiment configs may say "ollama" despite pointing
        # to an OpenAI-compatible /v1 endpoint. Detect that combination without
        # rewriting the persisted experiment configuration.
        backend = str(llm_config.get("backend", "ollama")).strip().lower()
        configured_url = str(llm_config.get("base_url") or "").rstrip("/")
        if backend == "ollama" and configured_url.endswith("/v1"):
            backend = "openai_compatible"
            logger.warning("FRAIME: using OpenAI-compatible API for /v1 endpoint")
        if backend in {"openai_compatible", "openai", "openai-compatible"}:
            if not configured_url:
                raise ValueError("OpenAI-compatible LLM requires llm.base_url")
            self.llm_backend = "openai_compatible"
            params = {
                "model": llm_config.get("model", "gpt-4o-mini"),
                "temperature": llm_config.get("temperature", 0.7),
                "base_url": configured_url,
                "api_key": llm_config.get("api_key") or "not-required",
                "timeout": 120,
                "max_retries": 1,
            }
            if llm_config.get("max_tokens") not in (None, ""):
                params["max_tokens"] = int(llm_config["max_tokens"])
            self.llm = ChatOpenAI(**params)
        elif backend == "ollama":
            self.llm_backend = "ollama"
            self.llm = ChatOllama(
                model=llm_config.get("model", "llama3.2"),
                temperature=llm_config.get("temperature", 0.7),
                base_url=_build_ollama_url(llm_config),
            )
        else:
            raise ValueError(f"Unsupported LLM backend: {backend}")
'''
RENDER_OLD = '''            response = chain.invoke(kwargs).strip()
            self._log_prompt(template_key, kwargs, response, backend="text")
'''
RENDER_NEW = '''            response = chain.invoke(kwargs).strip()
            logger.info("FRAIME LLM success template=%s backend=%s chars=%d",
                        template_key, self.llm_backend, len(response))
            if not response:
                logger.warning("FRAIME LLM returned empty text template=%s backend=%s",
                               template_key, self.llm_backend)
            self._log_prompt(template_key, kwargs, response, backend=self.llm_backend)
'''
ERROR_OLD = '''            logger.warning(f"LLM call failed ({template_key}): {exc}")
            return ""
'''
ERROR_NEW = '''            logger.warning("FRAIME LLM failed template=%s backend=%s error=%s",
                           template_key, self.llm_backend, exc)
            return ""
'''

def transform(source: str) -> tuple[str, bool]:
    if "FRAIME LLM success template=" in source:
        # Existing patch must be complete; never partially patch.
        if ANCHOR_REPLACEMENT not in source or 'self.llm_backend = "openai_compatible"' not in source:
            raise RuntimeError("Detected incomplete existing FRAIME patch")
        return source, False
    for label, old in (
        ("import", ANCHOR), ("LLM constructor", ORIGINAL),
        ("LLM success", RENDER_OLD), ("LLM error", ERROR_OLD),
    ):
        if source.count(old) != 1:
            raise RuntimeError(f"Unexpected YPhotoSharing source: {label} marker count={source.count(old)}")
    source = source.replace(ANCHOR, ANCHOR_REPLACEMENT, 1)
    source = source.replace(ORIGINAL, REPLACEMENT, 1)
    source = source.replace(RENDER_OLD, RENDER_NEW, 1)
    source = source.replace(ERROR_OLD, ERROR_NEW, 1)
    return source, True

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--check", action="store_true", help="Validate without writing")
    args = parser.parse_args()
    target = args.plugin_root / "YPhotoSharing/YClient/LLM_interactions/llm_service.py"
    if not target.is_file():
        raise SystemExit(f"Missing plugin module: {target}")
    original = target.read_text(encoding="utf-8")
    patched, changed = transform(original)
    if args.check:
        print(f"[FRAIME] LLM patch valid: {target} (needs_change={changed})")
        return
    if not changed:
        print(f"[FRAIME] LLM patch already applied: {target}")
        return
    backup = target.with_name(target.name + ".fraime-original.bak")
    if not backup.exists():
        backup.write_text(original, encoding="utf-8")
    target.write_text(patched, encoding="utf-8")
    try:
        py_compile.compile(str(target), doraise=True)
    except Exception:
        target.write_text(original, encoding="utf-8")
        raise
    print(f"[FRAIME] LLM patch applied: {target}")

if __name__ == "__main__":
    main()
