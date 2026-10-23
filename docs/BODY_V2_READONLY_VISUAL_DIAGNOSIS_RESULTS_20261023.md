# BODY_V2 read-only visual diagnosis results — 2026-10-23

## Literal status

W8/v13s, v14, and R120 are reconstructions. They are not the unavailable original Claude-session `.blend` files. This diagnostic run did not save or modify any `.blend`. It opened hash-pinned reconstruction copies with Blender 5.2.0 LTS, posed them in memory, and exported reports, geometry snapshots, and flat-shaded diagnostic renders.

Run: [39937882229](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229)  
Branch: `work/body-v2-readonly-visual-diagnosis-20261023`  
Commit: `4f3e6b9ef5adf9b506bc790ba184b4c0370d20bc`

| Model | Visual artifact | ZIP SHA256, computed = GitHub | Source `.blend` SHA256 | Source/static guards | Full nine-frame reproduction | Grip | Archive/anatomy |
|---|---:|---|---|---|---|---|---|
| W8 | [12495910312](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229/artifacts/12495910312) | `3be4322ba67da8b3827c96c0afdb58ffa8adb998cf8d1814aab0978a9e68d63e` | `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c` | PASS | PASS, zero differences | FAIL | Archive FAIL; anatomy NOT_GRANTED |
| v14 | [12494932817](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229/artifacts/12494932817) | `5f11a9441cf5bb1d29ba3fae72c945f59c9109a26023cea15508d3310cb774e0` | `5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91` | PASS | PASS, zero differences | FAIL | Archive FAIL; anatomy NOT_GRANTED |
| R120 | [12495970648](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229/artifacts/12495970648) | `cf26902334a90cb3928821d797fcc88e27340a7837911a0e080b6973b5017a2f` | `fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb` | PASS | PASS, zero differences | FAIL | No archive equivalence; anatomy NOT_GRANTED; experimental only |

The source/static guard covers source and immutable-copy hashes, basis coordinates, all shape-key coordinates and names, polygon loop topology, vertex-group index/name mapping, weights, and rig-rest signature. Every guard remained unchanged after every measured path.

## Reproduced movement failures

Counts below reproduce the prior native reports exactly. They are thresholds applied to the frozen rest triangulation, not anatomical severity scores and not a valid cross-model quality ranking.

### Shoulder press

| Model | Sample 0: collapse / stretch / intersection pairs | Sample 6, t=0.75 | Sample 8, t=1.0 |
|---|---:|---:|---:|
| W8 | 9 / 1,004 / 11 | 110 / 3,509 / 146 | 173 / 1,594 / 441 |
| v14 | 9 / 1,278 / 49 | 115 / 4,261 / 320 | 149 / 2,200 / 586 |
| R120 | 111 / 2,627 / 715 | 329 / 9,171 / 678 | 227 / 6,366 / 969 |

Flagged triangles are concentrated in vertex-weight regions labelled shoulder caps, clavicles, neck, upper arms, upper spine and scapulae. The labels identify dominant weights; they do not establish anatomical causation. The fixed-camera overlays visibly concentrate yellow stretch flags around the posterior shoulder/upper-back region. Hidden and back-facing flagged triangles are not all visible in any single render.

### Squat

| Model | Sample 0, t=0 | Sample 7, t=0.875 | Sample 8, t=1.0 |
|---|---:|---:|---:|
| W8 | 0 / 0 / 2,687 | 34 / 885 / 1,593 | 26 / 973 / 1,939 |
| v14 | 0 / 0 / 3,036 | 211 / 1,238 / 1,508 | 189 / 1,324 / 1,644 |
| R120 | 0 / 0 / 3,750 | 244 / 3,363 / 1,753 | 247 / 3,585 / 1,876 |

At deep squat, collapse/intersection localization is dominated by thigh and shin weighted regions; stretch localization is dominated by hip-crease, pelvis, thigh and lower-spine weighted regions. The side overlays visibly show some hip-crease/lower-torso stretch flags, but the rendered surface alone does not expose every collision pair.

The sample-0 intersection result is a neutral benchmark condition. Claude's pinned archived W8 report already records 2,238 rest intersections but zero in its chosen standing evaluation. Therefore the neutral count does not by itself prove that reconstruction introduced a new defect, and subtracting archive and reconstruction counts would be invalid because triangle correspondence and evaluation conditions are not established.

## Grip localization

The solver tested 263 configurations for runtime suffix `l` and stopped before evaluating suffix `r` because the first hand never passed both guards.

| Model | Trials | Trials at pair limit (`pairs <= 5`) | Hand-collapse result at those trials | Result |
|---|---:|---:|---|---|
| W8 | 263 | 1 | 24 | FAIL |
| v14 | 263 | 1 | 24 | FAIL |
| R120 | 263 | 3 | 23, 23, 24 | FAIL |

All other trials short-circuited before the hand-collapse check because the pair count exceeded five. The four-view grip images show the actual last rejected left-hand trial before post-pose correction. They are not an accepted grip, the closest trial, or proof that no solution exists outside the finite search grid.

## Visual comparison

- W8 and v14 are very similar in the fixed-camera flat diagnostic views. v14 has visibly smoother lower-body surfaces than W8 in several views but retains the known two-vertex archive discrepancy and fails the measured movement gates.
- R120 has broader smooth surface regions in the as-loaded views, while its recorded press and squat flag counts cover more triangles. It remains an experimental candidate and is not a replacement for W8/v14.
- The diagnostic renders use flat Workbench shading and display-only meshes. They are not realistic skin renders and must not be used as anatomical approval.

## Existing blockers retained

- W8 archive equivalence: offset-array maximum `3.59286 mm` versus `0.01 mm` guard; proportion maximum `0.837573 mm`.
- v14 archive equivalence: `238,065` vertices versus `238,067` archived.
- One skeleton, 12 W8 and 10 v14 JSON discrepancies remain.
- Production 67-bone bridge is incompatible with the recovered 77-bone authoring rigs.
- Anatomical left/right evidence is geometric only; reviewed landmark bindings are not approved.
- Source-content acceptance, anatomical approval and muscle attachment remain BLOCKED.

## Deliverables

Each GitHub artifact contains `diagnosis.json`, per-frame triangle JSON, geometry NPZ snapshots, the native log, and front/back/side/three-quarter plain and overlay PNGs. It deliberately excludes the immutable `.blend` copy. The model artifacts remain separately preserved and hash-verified.

Generated contact sheets in this evidence package are mechanical layouts of the native PNGs only; no image content was synthesized or retouched.
