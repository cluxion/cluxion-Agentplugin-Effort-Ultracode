"""Hermes plugin shim for exposing the cluxion_consensus tool."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from cluxion_effort_ultracode.core import ConsensusEngine, ConsensusProtocolError


def register(ctx: object) -> None:
    """Register the cluxion_consensus tool with a Hermes-like host context."""

    tool = _build_tool(ctx)
    if hasattr(ctx, "register_tool"):
        ctx.register_tool("cluxion_consensus", tool)
        return
    if hasattr(ctx, "add_tool"):
        ctx.add_tool("cluxion_consensus", tool)
        return
    if hasattr(ctx, "tool"):
        ctx.tool(name="cluxion_consensus")(tool)
        return
    if isinstance(ctx, dict):
        ctx["cluxion_consensus"] = tool
        return
    raise RuntimeError("Hermes context does not expose a known tool registration method")


def _build_tool(ctx: object):
    def cluxion_consensus(
        question: str,
        context: str = "",
        rounds: int = 3,
        agents: int = 3,
    ) -> dict[str, Any]:
        llm = _ContextLlmAdapter(ctx)
        if not llm.available:
            return {
                "ok": False,
                "error": "llm_port_unavailable",
                "message": "Hermes context did not expose complete(...) or llm.complete(...); consensus not run.",
            }
        try:
            result = ConsensusEngine(llm, agents_count=agents, max_rounds=rounds).decide(question, context=context)
        except (ConsensusProtocolError, ValueError) as exc:
            return {"ok": False, "error": type(exc).__name__, "message": str(exc)}
        return {"ok": True, "result": asdict(result)}

    cluxion_consensus.__name__ = "cluxion_consensus"
    cluxion_consensus.__doc__ = "Run a deterministic adversarial debate to unanimous consensus or honest dissent."
    return cluxion_consensus


class _ContextLlmAdapter:
    def __init__(self, ctx: object) -> None:
        self._complete = _find_complete(ctx)
        self.available = self._complete is not None

    def complete(self, prompt: str, *, schema: Mapping[str, Any] | None = None) -> Mapping[str, Any] | str:
        if self._complete is None:
            raise ConsensusProtocolError("LLM port unavailable")
        try:
            return self._complete(prompt, schema=schema)
        except TypeError:
            return self._complete(prompt)


def _find_complete(ctx: object):
    direct = getattr(ctx, "complete", None)
    if callable(direct):
        return direct
    llm = getattr(ctx, "llm", None)
    nested = getattr(llm, "complete", None)
    return nested if callable(nested) else None
