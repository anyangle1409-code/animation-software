# Native arm/back isolation result — 19 October 2026

Status: diagnostic complete; requested shape and back-motion repair NOT complete. No model saved.

Run39245688426 completed successfully at11:51:22UTC /12:51:22Europe/London. Source2d1f8bb7a453a4c1e7842091bfa671510fd5a22c. Artifact12184475441 original-v1-arm-back-ablation-20261019 downloaded and SHA256 verified:6c42860db239afb618fd57168e9b787b3b955a071b35d8ecd690478d7b14b054.

All five fresh Blender5.2.1 processes completed161 poses. Five helper/packaging tests passed in CI. Every mode had0.0mm endpoint difference and0.0 maximum matrix-component difference against R41 for the full runtime bone inventory at all161 poses. All protected identity checks passed: bone rest matrices/inventory, Basis, actual polygons, source topology, groups, weights and stored non-S7 coordinates. The source model file hash was verified before/after. This establishes identical skeleton motion between these diagnostic configurations, not a new anatomical certification of the skeleton.

| Diagnostic | Original41-pose excess vs R41, mm |161-pose excess normalized by16, mm |
|---|---:|---:|
| R41 |0|0|
| R41 with S5 values temporarily zero |1.921781|5.929727|
| R41 with S7 values temporarily zero |1.875765|2.077474|
| R41 with S5 and S7 values temporarily zero |1.451839|1.791127|
| Exact existing R52 |0.706690|40.644618|

These are differences of discrete second-difference magnitudes, not physical acceleration in mm/s². The additional normalized guard remains0.5mm. Lower numbers for an ablation do not establish a safe or visually correct surface. Actual native views show pronounced armpit/shoulder folds returning when S5 or S7 is disabled. No ablation is an accepted candidate.

The exact R52 native failure was reproduced: its corrective field creates much larger intermediate motion than the coarse test reveals, while the skeleton follows exactly the same poses. Prior read-only diagnosis localizes the worst point near118degrees/t=.5 and identifies a control-slope change. Both the interpolation/temporal representation and the wrong arm-to-body target require attention. Do not run another unchanged fit, remove protective existing keys as a shortcut, or move the canonical skeleton to compensate for the skin.

Media:
- skeleton_skin_t0800.jpg: native R41/R52 rear and three-quarter with actual endpoint projections through skin, same t=.800; identity checked before affirmative montage generation.
- family_ablation_comparison.jpg: five native skin configurations at t=.5 and t=.8; diagnostics, not proposed models.
The immutable artifact retains all per-mode logs, state/motion arrays, actual render snapshots and complete measured results.

No new geometry safety fit,83-check candidate acceptance run,13-benchmark candidate run or owner visual approval occurred in this diagnostic. Prior R52 failures remain unchanged. The armpit arch and requested back correction remain unresolved.

Next: prepare a small spatial feasibility preview against the owner's original reference, keeping newer arms/elbows. Check the fixed110/166 and anchor boundary for conflict before requesting any scope change. A future geometry attempt needs a newly allocated immutable candidate and native before/after images/video; no R53 has been created by this audit.
