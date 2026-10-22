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

## Follow-up evidence and requested provenance (local draft, still unsent)

With unchanged source and the same seed/configuration, our existing Linux x86_64
containers produce 76/29565/22201 (Python 3.11.17 or 3.14.8, NumPy 2.4.6) and
72/29896/22228 (Python 3.11.17, NumPy 1.24.4 or 1.26.4). Disabling
AVX512F/AVX2/FMA3 under Linux NumPy 1.26.4 produces 76/29596/22109.
Windows NumPy 1.26.4 and 2.4.6 match our original Windows 2.5.3 result.
None matches the saved 83-slot trajectory.

We isolated a local numerical sensitivity between two of these environments:
at slot 40, agent 3, a one-ULP candidate value difference changes the residual
greedy group's density ordering in `lagrangian_select`. Replaying the identical
candidate set with only that value changed reproduces the different selection.
This establishes local sensitivity, but we do not have your trace and therefore
cannot identify the first divergence relative to your original run.

In addition to version numbers, could you share the NumPy wheel/build, CPU
architecture/available SIMD path, relevant dispatch settings, and exact source and
configuration used for generation? A trace including candidate groups, option
values/rates/symbol counts, selected options and channel state for this seed would
be particularly helpful. We will keep the saved records unchanged and distinguish
exact replay failure from any subsequent statistical reproduction.
