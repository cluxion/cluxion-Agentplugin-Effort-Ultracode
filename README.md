# cluxion-Agentplugin-Effort-Ultracode

Portable multi-agent "ultracode" orchestration whose headline feature is a **3-agent
adversarial debate that converges to unanimous consensus**: three agents argue from evidence
and reasons, concede points that are better-argued, and only a unanimous agreement becomes the
decision.

v0.1 provides:

- host-agnostic `ConsensusEngine`
- core-owned dataclasses and ports
- deterministic code-level convergence checks
- concession-with-reason enforcement
- honest `no_consensus` results with dissent
- a callable reference adapter
- a thin Hermes `cluxion_consensus` registration shim
- `cluxion-ultracode consensus` with deterministic mock adapters

Example:

```bash
cluxion-ultracode consensus --question "Should we adopt the proposal?" --adapter mock-unanimous
```

The broader Ultracode workflow runtime is intentionally deferred; see `DESIGN.md`.
