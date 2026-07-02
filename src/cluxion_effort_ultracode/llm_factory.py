"""Shared LLM factory for CLI and plugin entry points."""

from __future__ import annotations

import os

from cluxion_effort_ultracode.adapters.hermes_llm import HermesSubprocessLlm


def default_llm() -> HermesSubprocessLlm:
    binary = os.getenv("CLUXION_EFFORT_ULTRACODE_HERMES_BINARY", "hermes")
    model = os.getenv("CLUXION_EFFORT_ULTRACODE_HERMES_MODEL") or None
    timeout = timeout_from_env()
    return HermesSubprocessLlm(binary=binary, timeout_seconds=timeout, model=model)


def timeout_from_env() -> float:
    raw = os.getenv("CLUXION_EFFORT_ULTRACODE_HERMES_TIMEOUT", "").strip()
    if not raw:
        return 120.0
    try:
        timeout = float(raw)
    except ValueError as exc:
        raise ValueError("CLUXION_EFFORT_ULTRACODE_HERMES_TIMEOUT must be numeric") from exc
    if timeout <= 0:
        raise ValueError("CLUXION_EFFORT_ULTRACODE_HERMES_TIMEOUT must be greater than zero")
    return timeout


__all__ = ["default_llm", "timeout_from_env"]
