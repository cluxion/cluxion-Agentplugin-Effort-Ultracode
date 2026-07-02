"""Structured types for the host-agnostic Ultracode portable core."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ConsensusStatus = Literal["unanimous", "no_consensus", "aborted"]
RoundPhase = Literal["independent", "debate"]


@dataclass(frozen=True)
class DebatePoint:
    """A maintained or conceded debate point with its explicit reason."""

    point: str
    reason: str


@dataclass(frozen=True)
class AgentPosition:
    """One agent's structured stance in an independent or debate round."""

    agent_id: str
    stance: str
    rationale: str
    evidence: list[str]
    confidence: float
    conceded: list[DebatePoint] = field(default_factory=list)
    maintained: list[DebatePoint] = field(default_factory=list)


@dataclass(frozen=True)
class ConsensusRound:
    """Transcript entry for one consensus round."""

    round_index: int
    phase: RoundPhase
    positions: list[AgentPosition]


@dataclass(frozen=True)
class Dissent:
    """Final non-unanimous position from one agent."""

    agent_id: str
    stance: str
    rationale: str
    evidence: list[str]


@dataclass(frozen=True)
class ConsensusResult:
    """Final structured result returned by the consensus engine."""

    status: ConsensusStatus
    decision: str | None
    rationale: str
    rounds: int
    transcript: list[ConsensusRound]
    agents_count: int
    dissent: list[Dissent]
    evidence_trail: list[str] = field(default_factory=list)
    points_of_disagreement: list[str] = field(default_factory=list)
    majority_stance: str | None = None
    abort_reason: str | None = None
    rounds_completed: int | None = None
