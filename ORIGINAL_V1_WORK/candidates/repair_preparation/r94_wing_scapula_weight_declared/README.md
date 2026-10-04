# r94 Step B - local scapula-weight reduction on the lateral/back torso skin: REFUSED (probes only; r93 retained)

Declaration: wing_zone_declared_before_edit.json (181 left-owned + mirror = 362 vertices; torso-region, scapula weight > 0.10, posterior, 1.20 < z < 1.42), with the measured wing and the change rule, committed before any edit. Weights-only numpy screening: numpy_screening_weights_only.txt. Probes (weights from the numpy solution, then the abduction corrective re-solved with all r93 arguments incl. the clavicle-top limits, applied, 15-pose metrics-only test, renders; flexion keys not rebuilt for the screening):

| strength beta | wing max / mean offset in press_top (weights-only; r93 reference 8.0 / 4.4 cm) | new strict P3B1 regressions (excluding the squat items of the screening copy) | self-intersections press_top / rhythm |
|---|---|---|---|
| 0 | 9.7 / 4.8 | - | 30 / 24 (r93) |
| 0.3 | 6.8 / 3.6 | press_top arm 0.731 (0.78), pullup_bar/hang arm 0.814 (0.865), pullup_hang_rhythm arm 0.794 (0.838), pullup_top torso | 42 / 26 |
| 0.5 | 5.9 / 2.8 | press_bottom torso 0.663, press_top arm 0.737, press_top_rhythm p01, pullup_bar p01, pull-up arm 0.824 / 0.815, pullup_top torso 0.663 | 40 / 40 |

Renders (review_images/r94_wing_probes, rear and side): at beta 0.3 the rear silhouette narrows only slightly and the lobe, its ledge and the creases remain; beta 0.5 narrows it more but adds creases and the metric regressions above.

Conclusion: the lateral/back lobe is the scapula-bound skin itself (the worst vertices are 80-100 percent scapula-weighted and the offset follows the accepted scapular rotation of 25-36 degrees); lowering their scapula share by local weight edits moves the cost to the pull-up arm and the press torso minima, which is the trade-off frontier already found with r82/r85. Stop condition met; no candidate built.
What would address it (not authorised, not implemented): a corrective keyed to scapular rotation/elevation that draws the scapula-bound lateral skin back toward the thorax (a third shape-key pair, mirror of the dent-limited abduction corrective but acting on the scapular skin), or a deeper weight re-layout of the scapula/thorax skin; both need declared experiments with the full evidence suite; helper bones and topology are still not indicated.