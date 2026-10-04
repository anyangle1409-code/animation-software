# r91 wrist-weight blend - screening result (declaration: wrist_patch_declared_before_edit.json, committed before any edit)

Fallback: r90 (immutable). Patch: 87 left-owned vertices (+ mirror) within 3 cm of the pair centroid. Edit: W = top4((1 - lambda) W_r90 + lambda W_r47) on the patch.

| lambda | push-up hand min (gate 0.15; P3B1 0.119; r90 0.240) | push-up self-intersections (P3B1 158, tolerance 5; r90 164) |
|---|---|---|
| 0 (r90) | 0.240 | 164 |
| 0.10 | 0.233 | 164 |
| 0.15 | 0.230 | 162 |
| **0.20 (chosen)** | **0.226** | **162** |
| 0.25 | 0.222 | 162 |
| 0.50 | 0.182 | 162 |
| 0.60 | 0.167 | 162 |
| 0.70 | 0.153 | 162 |
| 0.75 | 0.146 (fails the 0.15 gate) | - |
| 1.00 (= r47 weights) | 0.119 | 158 |

Reading: the trade-off is real and monotonic (full reversion restores 158 pairs only by restoring the 0.119 hand minimum, a development failure), but a small blend already removes one pair per side, bringing the count to 162, which is within the comparator tolerance (rise <= 5 over P3B1's 158) while the hand minimum stays at 0.226. Two of the six extra pairs are removed; the other four need the full reversion and are deliberately kept: they are the price of the hand-minimum fix. Chosen lambda 0.20 sits inside the 0.15-0.70 plateau, away from the 0.10/0.15 edge.