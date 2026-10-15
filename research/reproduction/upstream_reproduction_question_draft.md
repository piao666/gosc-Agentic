# Unsent draft: throughput frontier reproduction provenance

This is a local draft only. No GitHub issue, email or other message has been sent.

Suggested title: `gosc_bits saved frontier differs from a fresh API run at 387b493`

At upstream commit `387b49389385b51c275dc5a22ec1672087edda1d`, we can regenerate the
displayed paper tables from saved data and reproduce the default GOSC seed-0 reference.
However, the following pure-Planner run differs from the saved frontier record:

```python
from gosc import Config, run_episode
o = run_episode(Config().with_(energy_price=0.0), "gosc_bits", 0)
print({k: o[k] for k in ("completion_time", "symbols", "bits")})
```

Fresh Windows result: `76, 29596, 22109`.
Saved `results/rev_frontier.json` record (`gosc_bits`, `W100/eta0.0`, seed 0):
`83, 31011, 23468`.

CPython 3.12.10 with NumPy 2.5.3 and an existing NumPy 2.3.5 environment give the same
local result. Direct execution inside an untouched Git archive also does. Original
tests pass. We have retained the configuration, full output and a non-intervening
scheduling trace. We have not altered the saved reference or the algorithm.

Could you provide the Python/NumPy versions, OS/architecture, and source/configuration
snapshot used to generate the throughput frontier? Was it generated with exactly the
released `schemes.py`, message accounting and confirmation-priority settings? A matching
seed-0 scheduling trace or environment manifest would help identify the first divergence.

The root cause is currently unresolved; this report does not assert an upstream bug.
