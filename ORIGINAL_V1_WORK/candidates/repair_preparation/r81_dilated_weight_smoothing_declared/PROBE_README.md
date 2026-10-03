# Probe evidence for r81 (dilated-zone weight smoothing, metrics only, r68 base; not candidates)

Zone: r80's 528-vertex collision zone dilated by 2 rings = 834 vertices (417 left-owned), declared before any edit (`weight_smoothing_zone_declared_before_edit.json`).

Self-intersecting face pairs (P3B1 / r68 base / r80-zone k=12 / dilated k=12 / dilated k=30):
- press_top 95 / 153 / 126 / 124 / 58
- press_top_rhythm 54 / 168 / 114 / 116 / 72
- pullup_hang 4 / 126 / 40 / 40 / 0
- pullup_hang_rhythm 0 / 134 / 64 / 64 / 0
- squat_bottom 108 / 138 / 100 / 100 / 82

Development gate: dilated k=12 fails 5 checks and dilated k=30 fails 2 (shoulder region minimum edge ratio 0.123 / 0.131 in press_top and press_top_rhythm, gate 0.15); r68 base has 0 failures. These are compressions that the corrective refit (hinge floor 0.45) is expected to recover.

Decision: build r81 from the dilated k=30 recipe (smoothing 30 iterations, lam 0.5) + a re-fitted corrective.
