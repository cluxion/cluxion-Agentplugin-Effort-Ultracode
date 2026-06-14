# cluxion Effort-Ultracode v0.1 Design

## Source Spec Mapping

The authoritative source is `/Users/kimtaekyu/Downloads/rr/Ultracode-통합-마스터.md`.
v0.1 implements one additive quality pattern from that spec: a 3-agent adversarial debate that
can be layered into the broader ultracode loop. It does not replace the loop. The intended future
shape remains:

1. understand
2. design
3. implement
4. review
5. apply quality patterns such as adversarial verification, judge panels, loop-until-dry, and now
   unanimous consensus debate where a decision must be settled.

The important mapping to Part 1 §3.8 is that the model controls only content. Code controls:

- agent count
- round count
- prompt fan-out order
- transcript shape
- stance normalization
- vote/convergence checks
- termination on unanimity or honest no-consensus
- concession validation

The engine never asks the model whether consensus exists. It computes consensus by normalizing the
agents' stances and checking whether every normalized stance is identical.

## Core, Ports, and Adapters

The package follows the Part 2 dependency-inversion requirement:

- `src/cluxion_effort_ultracode/core/types.py` contains dataclasses only.
- `src/cluxion_effort_ultracode/core/ports.py` owns the `LlmPort` protocol and optional ports.
- `src/cluxion_effort_ultracode/core/consensus.py` contains the deterministic algorithm.
- `src/cluxion_effort_ultracode/adapters/callable_llm.py` is a reference adapter for tests and
  plain Python use.
- `src/cluxion_effort_ultracode/plugin.py` is a thin Hermes-facing shim.

The portable core imports no host SDK and knows no Hermes, Claude, Codex, OpenAI, or workflow host
API. The only runtime dependency it needs is an object that satisfies:

```python
complete(prompt: str, *, schema: Mapping[str, Any] | None = None) -> Mapping[str, Any] | str
```

Adapters are intentionally translation layers. If Hermes later exposes a native structured-output
or workflow-agent API, that support should be implemented behind the port, not inside
`ConsensusEngine`.

## Consensus Algorithm

Inputs:

- `question`: the decision, proposal, or question.
- `context`: shared context shown to every agent.
- `agents_count`: default 3.
- `max_rounds`: debate rounds after independent round 0.

State:

- `AgentPosition`: `{agent_id, stance, rationale, evidence, confidence, conceded, maintained}`.
- `ConsensusRound`: one transcript entry for round 0 or a debate round.
- `ConsensusResult`: final structured result.

Round 0:

- The engine calls the LLM port once per agent.
- Each prompt contains only the question, context, and that agent's identifier.
- Round 0 prompts do not include other agents' positions.
- The response must include stance, rationale, evidence, and confidence.

Debate rounds:

- Each agent sees all current positions.
- Each agent must either maintain/rebut a specific point with a reason, or concede a specific point
  with a reason.
- A changed stance requires at least one explicit concession.
- Any conceded or maintained point without a non-empty reason raises `ConsensusProtocolError`.

Convergence:

- After every round, code normalizes stances using Unicode normalization, case-folding, punctuation
  removal, and whitespace collapse.
- Unanimity means exactly one non-empty normalized stance remains.
- The decision is the first agent's display stance for that unanimous normalized value.

Termination:

- On unanimity: `status="unanimous"`, `decision` is set, rationale merges the agent rationales,
  and `evidence_trail` contains deduplicated evidence in deterministic order.
- On max rounds without unanimity: `status="no_consensus"`, `decision=None`, each final stance is
  returned in `dissent`, and `points_of_disagreement` records the remaining split.
- The engine never fabricates agreement from rationales such as "we agree"; only stance equality
  computed by code can produce unanimity.

## Anti-Groupthink Safeguards

v0.1 makes the safeguards explicit and testable:

- Independent round 0.
- Evidence is required and must contain at least one non-empty item.
- Concession requires a stated reason.
- A stance change without concession is invalid.
- Convergence is deterministic code, not model self-reporting.
- A rotating devil's-advocate instruction is included in debate prompts by default.
- No-consensus is a first-class honest result with dissent preserved.

## CLI

The CLI entry point is:

```bash
cluxion-ultracode consensus --question "..." --adapter mock-unanimous
```

v0.1 ships only deterministic mock adapters at the CLI boundary:

- `mock-unanimous`
- `mock-no-consensus`

This keeps tests and local smoke runs network-free. A real Hermes/Codex/Workflow adapter should be
added by implementing the `LlmPort` contract.

## Hermes Shim

`plugin.py` exposes `register(ctx)` and attempts to register a `cluxion_consensus` tool through
common host methods:

- `ctx.register_tool(name, callable)`
- `ctx.add_tool(name, callable)`
- `ctx.tool(name=...)(callable)`
- dictionary insertion for test harnesses

The shim is intentionally conservative. If the host context does not expose `complete(...)` or
`llm.complete(...)`, the registered tool returns an honest `llm_port_unavailable` error instead of
pretending that consensus ran.

## Broader Ultracode Porting Deferred

The rest of the master spec should be added as separate portable core modules and ports:

- Scheduler: concurrency caps, queue rotation, per-call and lifetime fan-out limits.
- Workflow primitives: `agent`, `parallel`, `pipeline`, `phase`, `log`, `budget`, nested workflow.
- Journal/resume: run IDs, immutable-prefix replay, transcript persistence.
- Script runtime: deterministic JavaScript subset, meta literal validation, nondeterminism guards.
- Quality patterns: adversarial verify, perspective-diverse verify, judge panel, loop-until-dry,
  completeness critic, no-silent-caps logging.
- Capability negotiation: background execution, structured output, token metering, model resolution,
  worktree isolation, and graceful degradation warnings.

Recommended build order:

1. Add a `RuntimeProfile` and `LogPort` so all degraded paths are visible.
2. Add a real Hermes adapter after confirming the host registration and completion contracts.
3. Add a workflow-agent adapter if the host can spawn independent sessions.
4. Add journal/transcript persistence before long-running orchestration.
5. Add scheduler and fan-out primitives.
6. Promote this consensus engine into the quality-pattern library so the broader loop can call it
   when a design or implementation decision needs unanimous settlement.

## Open Questions

- What exact Hermes plugin registration API should be treated as canonical?
- Does Hermes expose native JSON schema enforcement, or should the adapter validate and retry?
- Can Hermes spawn isolated sub-agent contexts, or is the first real adapter a single-session
  completion adapter?
- Where should durable journals live for Cluxion/Hermes sessions?
- How should token accounting be reported if the host only exposes post-hoc usage?
