"""Deterministic tests for the portable consensus engine."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict
from typing import Any

import pytest

from cluxion_effort_ultracode.adapters import CallableLlmAdapter
from cluxion_effort_ultracode.core import ConsensusEngine, ConsensusProtocolError, normalize_stance


class ScriptedLlm:
    def __init__(self, outputs: list[dict[str, Any]]) -> None:
        self.outputs = deque(outputs)
        self.calls: list[dict[str, Any]] = []

    def complete(self, prompt: str, *, schema: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append({"prompt": prompt, "schema": schema})
        if not self.outputs:
            pytest.fail("scripted LLM exhausted")
        return self.outputs.popleft()


def position(stance: str, evidence: list[str] | None = None, rationale: str | None = None) -> dict[str, Any]:
    return {
        "stance": stance,
        "rationale": rationale or f"Rationale for {stance}",
        "evidence": evidence or [f"Evidence for {stance}"],
        "confidence": 0.7,
    }


def update(
    stance: str,
    *,
    conceded: list[dict[str, str]] | None = None,
    maintained: list[dict[str, str]] | None = None,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    return {
        **position(stance, evidence=evidence),
        "conceded": conceded or [],
        "maintained": maintained or [],
    }


def test_round_zero_prompts_are_independent() -> None:
    llm = ScriptedLlm([position("Adopt"), position("Delay"), position("Reject")])
    result = ConsensusEngine(llm, max_rounds=0).decide("Should we ship?")

    assert result.status == "no_consensus"
    assert len(llm.calls) == 3
    for index, call in enumerate(llm.calls):
        prompt = call["prompt"]
        own_agent = f"agent-{index + 1}"
        other_agents = {f"agent-{i}" for i in range(1, 4)} - {own_agent}
        assert own_agent in prompt
        assert "Current positions:" not in prompt
        assert all(other_agent not in prompt for other_agent in other_agents)
        assert call["schema"] is not None


def test_debate_converges_to_unanimity_with_concessions() -> None:
    llm = ScriptedLlm(
        [
            position("Adopt proposal", ["A1"]),
            position("Delay proposal", ["D1"]),
            position("Reject proposal", ["R1"]),
            update(
                "Adopt proposal",
                maintained=[{"point": "Adopt", "reason": "Mitigation evidence remains strongest"}],
                evidence=["A1", "A2"],
            ),
            update(
                "Adopt proposal",
                conceded=[{"point": "Delay", "reason": "The risk is directly mitigated"}],
                evidence=["D1", "A2"],
            ),
            update(
                "Adopt proposal",
                conceded=[{"point": "Reject", "reason": "The blocking concern has a bounded workaround"}],
                evidence=["R1", "A2"],
            ),
        ]
    )

    result = ConsensusEngine(llm, max_rounds=2).decide("Should we adopt the proposal?")
    result_shape = asdict(result)

    assert result.status == "unanimous"
    assert result.decision == "Adopt proposal"
    assert result.rounds == 1
    assert result.dissent == []
    assert result.evidence_trail == ["A1", "A2", "D1", "R1"]
    assert len(result.transcript) == 2
    assert result_shape["status"] == "unanimous"
    assert result_shape["agents_count"] == 3
    assert len(result_shape["transcript"][1]["positions"]) == 3


def test_no_unanimous_consensus_records_dissent() -> None:
    llm = ScriptedLlm(
        [
            position("Adopt proposal", ["A1"]),
            position("Delay proposal", ["D1"]),
            position("Reject proposal", ["R1"]),
            update("Adopt proposal", maintained=[{"point": "Adopt", "reason": "Evidence A still dominates"}]),
            update("Delay proposal", maintained=[{"point": "Delay", "reason": "Evidence D still dominates"}]),
            update("Reject proposal", maintained=[{"point": "Reject", "reason": "Evidence R still dominates"}]),
        ]
    )

    result = ConsensusEngine(llm, max_rounds=1).decide("Should we adopt the proposal?")

    assert result.status == "no_consensus"
    assert result.decision is None
    assert result.majority_stance is None
    assert len(result.dissent) == 3
    assert {dissent.stance for dissent in result.dissent} == {
        "Adopt proposal",
        "Delay proposal",
        "Reject proposal",
    }
    assert len(result.points_of_disagreement) == 3


def test_conceding_requires_a_stated_reason() -> None:
    llm = ScriptedLlm(
        [
            position("Adopt proposal"),
            position("Delay proposal"),
            position("Reject proposal"),
            update("Adopt proposal", maintained=[{"point": "Adopt", "reason": "Evidence remains strongest"}]),
            update("Adopt proposal", conceded=[{"point": "Delay", "reason": ""}]),
        ]
    )

    with pytest.raises(ConsensusProtocolError, match="without a reason"):
        ConsensusEngine(llm, max_rounds=1).decide("Should we adopt the proposal?")


def test_convergence_is_decided_by_code_not_claimed_agreement() -> None:
    llm = ScriptedLlm(
        [
            position("Adopt proposal"),
            position("Delay proposal"),
            position("Reject proposal"),
            update("Adopt proposal", maintained=[{"point": "Adopt", "reason": "I still hold this stance"}]),
            update("Delay proposal", maintained=[{"point": "Delay", "reason": "I still hold this stance"}]),
            update("Reject proposal", maintained=[{"point": "Reject", "reason": "I still hold this stance"}]),
        ]
    )

    result = ConsensusEngine(llm, max_rounds=1).decide("Should we adopt the proposal?")

    assert result.status == "no_consensus"
    assert "agreement was not fabricated" in result.rationale


def test_normalized_stances_can_reach_round_zero_unanimity() -> None:
    llm = ScriptedLlm(
        [
            position("Ship it!"),
            position("ship it"),
            position("SHIP IT."),
        ]
    )

    result = ConsensusEngine(llm).decide("Should we ship?")

    assert result.status == "unanimous"
    assert result.rounds == 0
    assert result.decision == "Ship it!"
    assert normalize_stance("Ship it!") == normalize_stance("SHIP IT.")
    assert len(llm.calls) == 3


def test_callable_adapter_parses_structured_json_text() -> None:
    adapter = CallableLlmAdapter(lambda _prompt: '{"stance":"Adopt","rationale":"R","evidence":["E"],"confidence":1}')

    result = ConsensusEngine(adapter, agents_count=2).decide("Question?")

    assert result.status == "unanimous"
    assert result.decision == "Adopt"
