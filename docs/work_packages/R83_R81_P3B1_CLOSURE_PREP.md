# r83 preparation — r81 strict-P3B1 closure

Status: PREPARATION ONLY. No model, weights, corrective, gates, baseline, or Phase 4 state changed.

Base branch/commit:
- claude/original-v1-blender-o2-20260929
- 0a37c483c02fc485bd9852d09ff16887f9f6b197
- retained candidate: r81

## Evidence-derived blocker split

r81 has 0 development acceptance failures but 12 strict severity regressions vs immutable P3B1.

Attribution from committed r81 evidence:
- INHERITED_FROM_WEIGHTS: 7
- ADDED_BY_CORRECTIVE: 3
- INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE: 1
- OUTSIDE_3A_POSES: 1

### Weight-inherited targets
1. press_bottom torso region_min_ratio: 0.526 vs 0.698
2. press_top arm region_min_ratio: 0.702 vs 0.780
3. pullup_bar arm region_min_ratio: 0.688 vs 0.865
4. pullup_hang arm region_min_ratio: 0.688 vs 0.865
5. pullup_hang_rhythm arm region_min_ratio: 0.727 vs 0.838
6. pullup_top torso region_min_ratio: 0.654 vs 0.693
7. squat_bottom shoulder region_min_ratio: 0.182 vs 0.244

### Corrective-added targets
1. press_top_rhythm arm region_min_ratio: 0.621 vs 0.679
2. squat_bottom volume_deviation_from_1: 0.0500 vs 0.0438
3. squat_bottom edge_ratio_p01: 0.579 vs 0.613

### Mixed target
- squat_bottom arm region_min_ratio: 0.383 vs 0.597

### Separate/outside-3A target
- pushup_bottom self_intersecting_face_pairs: 164 vs 158 (delta +6; tolerance +5)

## r82 lesson

Do NOT continue by increasing smoothing strength/iterations globally or across the whole shoulder-only zone.
r82 drove shoulder self-intersections to zero but increased strict regressions to 17 and materially worsened arm max/min ratios in press and pull-up poses. It is refused evidence, not a continuation baseline.

## Proposed r83 strategy

r83 should be a constrained, attribution-aware experiment from r81, not from r82.

1. Freeze r81 as the immutable parent.
2. Before any edit, derive and commit explicit permitted masks for:
   - A: weight-inherited minimum-ratio vertices/edges in arm/torso/shoulder;
   - B: corrective-added press_top_rhythm + squat extrema;
   - C: mixed squat arm extrema.
3. Exclude already-successful shoulder-top intersection surfaces from broad smoothing. Preserve r81's intersection gains as hard regression checks.
4. Prefer local weight restoration/blending toward the P3B1/r81-parent-side weights at the exact minimum-ratio neighborhoods rather than additional smoothing.
5. Refit/limit the corrective only after the weight-side probe, with explicit penalties/checks for the three corrective-added regressions.
6. Keep pushup_bottom +6 intersection as a separate diagnostic/work item; do not distort 3A shoulder weights to fix an outside-3A pose.
7. Run focused probes first:
   - press_bottom
   - press_top
   - press_top_rhythm
   - pullup_bar / pullup_hang / pullup_hang_rhythm
   - pullup_top
   - squat_bottom
   - pushup_bottom as regression sentinel
8. Reject immediately if:
   - any r81 development gate becomes a failure;
   - shoulder-top self-intersections materially rise beyond r81;
   - strict P3B1 regression count exceeds 12 without a documented Pareto improvement that justifies research retention.
9. Only a candidate improving the strict comparison should proceed to the full 15-pose evidence package.

## Important interpretation

The remaining r81 blocker is dominated by *minimum edge/region ratio* regressions, not by the original shoulder-top collision count. The next experiment therefore needs local anti-collapse/restoration behavior. More smoothing is contraindicated by r82.

This document authorises no Blender/model edit. It exists to reduce rediscovery when Blender execution resumes.
