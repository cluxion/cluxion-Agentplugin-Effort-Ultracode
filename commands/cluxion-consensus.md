---
description: Run Cluxion Ultracode adversarial consensus.
---

Run:

```bash
cluxion-ultracode consensus --question "$ARGUMENTS"
```

Useful flags:

```bash
cluxion-ultracode consensus --question "$ARGUMENTS" --rounds 3 --agents 3 --agent-timeout 180 --debate-budget 600
```

Worst-case cost: `agents * (rounds + 1)` model calls. Budget/quorum aborts return JSON with
`status: "aborted"` and a partial transcript.
