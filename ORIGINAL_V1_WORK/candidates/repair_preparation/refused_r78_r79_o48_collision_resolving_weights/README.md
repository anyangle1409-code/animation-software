# Refused: o48 collision-resolving shoulder weights (r78, r79)

Hypothesis: the shoulder-top self-intersections (clavicle-driven skin crossing upper-arm-driven skin, 5 x 10 x 5 cm per side, median depth 1.5-1.7 cm) can be prevented in weight space with the weight solver's triangle-triangle collision-resolution mode (`--preset o48` = o45 + `prox_mode=tritri`, `tt_resolve=True`, `tt_delta=0.001`, `tt_radius=0.03`, `w_prox=5e6`).

Recipe: r43 + o48 weights (r78, the blended solution `o48_r43_b.npz`) + the wrist band o26 (r79, same as r62's recipe). Parents/recipe otherwise identical to r62 (o45), so r62 is the direct comparison.

Measured in the real Blender pose test (metrics only), self-intersecting face pairs P3B1 / r62 / r79: press_top 95 / 137 / 250; press_top_rhythm 54 / 148 / 298; pullup_hang 4 / 116 / 66; pullup_hang_rhythm 0 / 126 / 84; squat_bottom 108 / 138 / 154. Development gate: 4 failures (press_top and press_top_rhythm self-intersections > 200, and edge_ratio_p99 2.026 and 2.053 > 2.0) versus 1 for r62.

Disposition: REFUSED. The resolution helps the pull-up poses but makes the press poses far worse (the solver's own per-round intersection counts rose to 462 and 530 in press_top / press_top_rhythm instead of falling), so it is not a safe replacement for o45. No evidence run was spent on r78/r79; the candidate manifests are preserved here (moved out of the candidate manifest folder so the status tooling does not treat a refused experiment as an incomplete candidate), the local Blends stay in place so labels r78/r79 stay reserved. Recreate deterministically from `o48_r43_b.npz` applied to r43 (then `o26_r47_b.npz` for r79).
