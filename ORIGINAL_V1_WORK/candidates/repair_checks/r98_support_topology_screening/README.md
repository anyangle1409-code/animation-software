# r98 support topology and rest-shape screening

All variants are rebuilt from the r95 working reconstruction with r97's mechanics, which are not modified. Shape keys are held at 0 (weights-only). Scripts are in `scripts/r98/` and the numbers are in `screening_results.json`.

## Support topology: tested and not adopted

The candidate rings came from the edge-ring walk through the left axillary apex (`scripts/r98/rings.py`):
- the torso row through the apex: a closed 64-edge ring;
- the arm-root ring: a closed 40-edge ring, mirrored.

Each was split once with bmesh. The result stayed all-quad and mirror-exact, and the weights were re-solved rather than interpolated.

| Variant | Subset self-intersections | Max edge ratio |
|---|---:|---:|
| r97 | 834 | 4.41 |
| rings only (+144 vertices) | 946 | 6.59 |
| opening only | 504 | 4.37 |
| opening + both rings | 608 | 6.51 |
| opening + arm-root ring (+80) | 554 | 4.54 |
| opening + torso row (+64) | 536 | 4.38 |

Each ring family made both self-intersections and stretch worse, whether used alone or on top of the rest-shape repair. This confirms the r96 finding: adding density does not change the deformation field. **The minimum justified edge flow is therefore none**, and r98 adds no vertices. The declaration permitted rings; it did not require them.

## Rest shape: adopted

Diagnosis:
- At rest the arm's inner wall lies about 2 cm from the chest and back wall.
- The two walls meet at a sharp V apex near z = 1.41 m.
- Of r97's protected-zone self-intersections, 1332 of 1536 are between these two walls. They occur with external rotation, horizontal adduction and arm-behind-torso at low and mid elevation.

The repair opens the slit by moving the trunk wall 8 mm and the arm's inner wall 6 mm along their normals, with a smooth falloff within 5 cm. The V apex is Laplacian-rounded. The displacement is capped at 11.5 mm and measures 10.7 mm, against a declared cap of 12 mm.

## Re-skin: localized

- **Global re-solve (o4).** The harmonic solve is global, so changing the apex geometry moved deltoid-top weights. The repo pose test then regressed pull-up hang rhythm (0 → 6) on the acromion top.
- **r97 weights unchanged (o4r).** Squat regressed (82 → 100).
- **Adopted: localized re-skin.** The re-solved weights are used only within 2 rings of the edited vertices, blended over 3 rings into r97's weights. Non-declared bone weights stay exactly r95's.

One pipeline error was found and corrected. The first pose tests of o and o3 ran before the r95 corrective driver configs had been removed, so the old correctives were active. Every number above comes from a rerun without them.
