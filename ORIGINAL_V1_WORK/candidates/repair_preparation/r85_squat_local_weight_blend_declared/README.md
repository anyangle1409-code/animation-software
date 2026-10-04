# r85 (REFUSED probe, numerical screening only; r83 retained)

Declared before the edit: `squat_subzone_declared_before_edit.json` (382 vertices of the smoothed zone within 0.08 m of the squat worst edges; mirror-closed) with hypothesis and stop condition.
Screening (`r85_screen.py`, exact numpy LBS verified against Blender to 4e-7 m; `screening_output.txt`): a continuous blend of the smoothed weights back toward the r68 weights in that sub-zone, strength a, smooth falloff, top-4 renormalised.

| a | squat arm min | squat shoulder min | squat shoulder max rise vs r83 |
|---|---|---|---|
| 0 (r83) | 0.383 | 0.182 | 0 |
| 0.25 | 0.450 | 0.198 | +0.083 |
| 0.50 | 0.523 | 0.203 | +0.166 |
| 0.75 | 0.521 | 0.216 | +0.250 (and a press_top_rhythm arm min drop 0.026) |
| 1.00 | 0.510 | 0.226 | +0.333 (press_top_rhythm arm min drop 0.049) |

Needed to clear the strict comparator: squat arm >= 0.577 (P3B1 0.597 - 0.02) and squat shoulder >= 0.224 (0.244 - 0.02). No strength reaches both; the arm never exceeds 0.523 (the r68 weights-only value is 0.529), and the shoulder minimum only approaches the threshold at strengths that add a squat shoulder stretch regression (> 0.1 tolerance) and a press regression. Squat volume deviation and p01 are untouched by this sub-zone. So the probe cannot reduce the 7 strict regressions and adds new ones: it is not strictly preferable to r83, so no Blender candidate was built and no full evidence was run. `zcut_screening_output.txt` (height-cut and hard local reverts) shows the same frontier.

Key finding: in squat_bottom the humerothoracic elevation is 125.9 degrees but the corrective's abduction gate is 0 (the arms are flexed forward), so the shoulder corrective is inactive there; the four squat regressions are pure skin weights.