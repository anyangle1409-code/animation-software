# Superseded exploratory candidates (r39, r40)

r39 and r40 were the first two iterations of the rev2 twist-helper authoring (declarations
`repair_preparation/r39_twist_helpers_declared`, `r40_twist_helpers_declared`) and were measured under an earlier
revision of stress-pose definition P2 (before the thumb-flatten and solved push-up plank angle were added). Their
evidence is preserved here, unmodified, and is NOT part of the current lineage: r41 (declaration
`r41_twist_helpers_declared`) is the helper-revision candidate that carries full evidence under the final P2 definition.
Findings that drove the iterations: r39 collapsed arm-ring vertices to one twist station (arm edge stretch 4.8x);
r40 fixed that but left chest-side vertices on mixed stations (torso min edge 0.26); r41 blends trunk-weighted vertices toward
the twist-free station.

## r42 — forearm-only helper variant (comparison evidence, metrics-only)

r42 = r38 + forearm helpers only (`--segments forearm`, declaration `repair_preparation/r42_forearm_twist_declared`). Metrics-only against
P2B1: 0 regressions / 7 improvements but the same 5 development failures (shoulder minima at press_top / pull-up, press_top_rhythm p99,
push-up hand). r41 (both segments): 2 development failures / 36 improvements / 16 regressions (arm-region stretch up to 3.2, still inside the
5.0 gate). The upper-arm helpers are what clear the shoulder-minimum failures, so the full rev2 (r41) is kept and its arm-stretch regressions
are left to the weight re-solve (the solver sees the helper bones). Files: `r42_forearm_only_vs_P2B1_metrics_only.json`,
`r41_both_segments_vs_P2B1_metrics_only.json`.
