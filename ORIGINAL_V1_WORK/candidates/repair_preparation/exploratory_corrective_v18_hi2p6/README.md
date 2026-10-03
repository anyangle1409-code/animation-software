# Exploratory corrective solve v18 (stretch bound 2.6) - NOT a candidate

Solved numerically only (no Blend, no candidate number) on the r68 base dump with the r69 corrective barriers (fold floor 0.3, rest-relative face-area floor 0.35, roughness tolerance 0.2, contact guard) and a much tighter stretch bound: `--hi 2.6 --p99-tail 1.8` (candidates r69-r76 use `--hi 3.6 --p99-tail 1.95`). Initialised from the r69 solution (corr_v17).

Purpose: test whether the over-stretched pectoral/axilla skin (torso edge ratios about 3.1-3.3 where physiological skin stretch is about 1.5-1.6) can be redistributed by the corrective alone.

Predicted torso edge maximum (the solver's own exact LBS model) versus the r69 solution: press_bottom 2.85 (r69 about 2.7), press_top 2.85 (r69 3.09), pullup_hang 2.61 (r69 3.11). Minimum edge ratio 0.43-0.50 (r69 0.45-0.51). max |D| 0.083 m. The bound is only partly met (soft hinge, 5 competing barriers).

Disposition: about a 10 percent stretch improvement is not enough to change the visual reading of the overhead shoulder, and applying it would discard the local r72-r76 improvements and require repeating the whole guarded local pipeline. Kept as evidence that the corrective alone cannot reach physiological stretch in the axilla web: the remaining options are a local topology/weight refinement of the axilla web and anterior shoulder (declared mask, new candidate) or an owner decision. No weights, thresholds or baselines were touched.
