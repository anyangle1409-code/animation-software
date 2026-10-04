# r89 - flexion corrective re-solved with a mesh-volume floor (declaration before any solve)

Retained fallback: r87 (SHA 019891ddcc7d9d49486a2f89917d09129a43e53bb0b45402b7f8e685ee6e84cc). Skeleton (67 bones), weights, abduction keys, frozen P3a pose-definition hash untouched.

Target: squat_bottom volume deviation 0.0511 vs P3B1 0.0438 (strict limit 0.0488, i.e. volume ratio >= 0.9512; r87 = 0.9489).

Cause analysis (measured, `vol_split.py` and the volume history): squat volume ratio P3B1 0.9562; r41..r76 0.9551-0.9563 (inside tolerance); r80 0.9539; r81 0.9500 (dilated weight smoothing: -4.1e-4 m^3, shoulder-region triangles -9.7e-4, arm +2.3e-4, torso +3.3e-4); r87 0.9489 (the flexion key: a further -0.0011, about -0.9e-4 m^3). So 0.0050 of the gap is inherited from the weights and 0.0011 was added by the flexion key. Recovering +0.0023 over r87 puts the deviation under the limit.

Driver and mask: unchanged from r86/r87 (flexion key pair, activation smoothstep((theta-45)/75)*(1-lam); same 1491-vertex mask, file in this folder). The weights are not touched.

Edit: the flexion corrective is re-solved from the same dump with all r87 arguments plus a mesh-volume floor term `--w-vol --vol-floor` (total mesh volume in every pose where the key is active may not fall below floor x rest volume; only the squat arc activates the key). Probes: P1 floor 0.9525, P2 floor 0.9560 (= P3B1 level). Hypothesis: the compressed deltoid skin can be re-inflated by a few millimetres in the flexion field without breaking the compression floors, stretch bounds or fold/area barriers, recovering the volume the weight smoothing took. Screen metrics-only first; formalise only if strictly preferable to r87 (volume regression gone, squat arm/shoulder/p01 kept, nothing new regresses, SI <= P3B1).