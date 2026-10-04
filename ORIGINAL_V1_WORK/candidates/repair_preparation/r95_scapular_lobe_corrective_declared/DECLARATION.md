# r95 - scapular-rotation lobe corrective (third shape-key pair) - declaration before any solve

Machine-readable declaration: scapular_lobe_mask_declared_before_solve.json (items 1-12 below, with the measured table by pose and elevation) and lobe_limit_zone_declared_before_solve.json. Fallback r93 (immutable). The r94 local-weight approach is not revisited.

1. Region: 336 left-owned + mirror = 672 vertices (lateral/back upper torso below and beside the scapula, torso/shoulder labels, y > -0.03) = the 181-vertex lobe zone of r94 dilated by 3 rings for continuity.
2. Surfaces: latissimus/lateral ribcage/infrascapular skin; the shoulder-label skin directly over the scapula is only in the taper ring.
3. Thorax reference: trunk-rigid surface (trunk bones only, weights renormalised); offset along the trunk-transported rest normal.
4. Current outward displacement by pose/elevation (r93, lobe zone, max/p95/median cm): see the JSON table; e.g. press_bottom 3.83/3.64/1.37 (u 23.6), press_top@0.5 5.11/4.82/2.20 (u 37.6), press_top@0.75 6.84/6.15/2.67 (u 56.3), press_top 7.95/7.36/2.86 (u 74.9), pullup_hang 7.60/7.00/2.84 (u 68.3), rhythm 9.34/8.58/2.92 (u 93.6), pullup_top 3.82/3.07/0.99 (u 16.1), squat/push-up/row <= 1.6.
5. Scapular rotation u: same table; driver_candidates_vs_lobe_offset.txt (correlation of lobe offset with u 0.99, with theta 0.93).
6. Driver: u = angle of R_spine_03^T R_scapula; a = smoothstep((u - u0)/(u1 - u0)).
7. Zero activation: u <= 15 deg. 8. Transition: 15-75 deg. 9. Maximum activation 1.0 at u >= 75 deg.
10. Geometric limit: outward offset of the lobe-zone vertices from the trunk-rigid surface <= 0.045 m (probe 1) or 0.035 m (probe 2), hinge 1e7; all r93 solve arguments (hold guards, barriers, clavicle-top shape limits, smoothness) kept; dent limit 0.06 m relative to the uncorrected pose (the intended pull-back is about 5 cm).
11. Hypothesis and 12. stop conditions: see the JSON.