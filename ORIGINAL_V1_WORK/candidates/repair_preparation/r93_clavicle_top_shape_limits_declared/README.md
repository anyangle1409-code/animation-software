# r93 Step A - clavicle-top shape limits: REFUSED (metrics-only probes, no candidate built; r92 retained)

Declaration: clavicle_top_zone_declared_before_solve.json (380 vertices) + the measured knob/web signature, committed before any solve. Probes (all r92 solve arguments incl. the 0.025 m dent limit, plus zone-bound geometric hinges at weight 1e6): **A1** area cap 1.6 x rest area; **A2** area cap 1.6 + slide limit 1.5 cm + bulge limit 1.0 cm.

| press_top, clavicle-top zone | weights-only | r92 | A1 | A2 |
|---|---|---|---|---|
| max triangle area / rest | 1.60 | 3.16 | 1.53 | 1.54 |
| triangles above 2 x rest | 0 | 3 | 0 | 0 |
| max outward bulge vs uncorrected (cm) | - | 1.69 | 2.05 | 0.97 |
| max / mean tangential slide (cm) | - | 2.63 / 0.58 | 2.74 / 0.61 | 2.01 / 0.51 |
| development failures | - | 0 | 0 | 0 |
| shoulder SI press_top / rhythm / hang | - | 32 / 36 / 0 | 34 / 36 / 0 | 34 / 38 / 0 (P3B1 95 / 54 / 4) |
| new strict P3B1 regression versus r92 | - | - | pull-up arm minimum 0.859 -> 0.842 (limit 0.845) | press_bottom torso 0.676, press_top arm 0.755, pull-up arm 0.835 ... |

Renders (review_images/r93_clavicle_top_probes, front and rear): the front clavicle tabs do NOT go away - the area cap leaves them as they are (A1) and the bulge/slide limits turn the rounded lumps into sharper horn-like points (A2); the rear trapezius drape (a cape-like skin span from the neck to the raised arms) is present in the weights-only, r92 and A1 states and is not changed by the cap. So the numerical extremes are clamped without removing the visible artefacts, and the strict-regression set gets worse: the criterion 'visibly improves without moving the defect elsewhere' is not met; r92 retained.

What this shows about the cause: the tabs and the drape are not produced by the corrective alone. They live in the skin between the clavicle-driven and upper-arm-driven sheets at the neck/arm junction (clavicle-end skin rotating up with the elevated clavicle; a wide neck-to-arm span in the rear), i.e. in the skin weights / sheet layout, which Step A (a corrective constraint) cannot remove. Fixing that needs a clavicle/upper-arm/neck weight change at the junction (outside Step A and Step B as authorised) or a topology change.