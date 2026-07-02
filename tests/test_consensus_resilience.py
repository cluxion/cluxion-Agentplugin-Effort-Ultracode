from __future__ import annotations

import time

import pytest
from tests.test_consensus import ScriptedLlm, position

from cluxion_effort_ultracode.core.consensus import ConsensusEngine, ConsensusProtocolError


class SlowThenFineLlm:
    """First agent call hangs past the per-agent timeout; the rest answer."""

    def __init__(self, hang_seconds: float) -> None:
        self.hang_seconds = hang_seconds
        self.calls = 0

    def complete(self, prompt: str, *, schema: object = None) -> str:
        self.calls += 1
        if self.calls == 1:
            time.sleep(self.hang_seconds)
        return position("Adopt proposal")


def test_hung_agent_is_dropped_and_quorum_continues() -> None:
    llm = SlowThenFineLlm(hang_seconds=2.0)
    engine = ConsensusEngine(llm, agents_count=3, max_rounds=1, agent_timeout_s=0.3, debate_budget_s=30.0)
    result = engine.decide("Should we adopt the proposal?")
    assert result.status == "unanimous"
    assert len(result.transcript[0].positions) == 2


class SlowScriptedLlm(ScriptedLlm):
    def complete(self, prompt: str, *, schema: object = None) -> str:
        time.sleep(0.01)
        return super().complete(prompt, schema=schema)


def test_total_debate_budget_is_enforced() -> None:
    llm = SlowScriptedLlm([position("Adopt"), position("Delay"), position("Reject")] * 10)
    engine = ConsensusEngine(llm, agents_count=3, max_rounds=8, debate_budget_s=0.005)
    with pytest.raises(ConsensusProtocolError, match="debate_budget_s"):
        engine.decide("Q?")


def test_invalid_timeouts_rejected() -> None:
    llm = ScriptedLlm([])
    with pytest.raises(ValueError):
        ConsensusEngine(llm, agent_timeout_s=0)
    with pytest.raises(ValueError):
        ConsensusEngine(llm, debate_budget_s=-1)
