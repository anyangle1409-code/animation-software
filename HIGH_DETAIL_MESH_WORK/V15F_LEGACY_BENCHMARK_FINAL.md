# V15f legacy benchmark preservation record

V15f is preserved as the final imported-lineage hand benchmark. It is a review
and comparison asset only. It is not approved for production promotion, Phase C
grip fitting, or further imported-lineage geometry work.

## Repository and recovery point

- Branch: `work/v15-deep-hand-rebuild-prep-20260925`
- Geometry commit before final publication: `0d5b1d88b3f4148940fc120e1dec34a0067626c0`
- Final checkpoint: `checkpoints/v15_manual/v15f_deep_hand_rebuild_checkpoint_012.blend`
- Active Blend: `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend`
- Frozen runtime pin: `614033b256d869230ea273522620467401b0bc71`
- Frozen hierarchy: 63 bones, `hgpt_canonical_v3`

## Artifact hashes

- Blend: `7521a4b2b50e2392db86f30edc5e9c0a5f310079a3744c501527daed9737cb26`
- Dressed GLB: `d9ba799b085d127efd9d787a37b97994fc09a3faa7d00da485c02ce16e6f6b29`
- Bare GLB: `287d408b9dff7a3a4913bd00e9c0f770fbba598ad345190e90da438a589aa2a3`
- Exported body: 48,321 vertices / 93,153 triangles

## Completed validation

- Full Blender invariant audit: PASS.
- Frozen `614033b` candidate guards and five-exercise suite: PASS.
- Protected push-up floor contacts: all 682 exact; maximum displacement 0 mm.
- Non-hand body displacement: 0 mm.
- Original skin rows changed: 0.
- Hierarchy, bone names, UV layers, retargeting, equipment and exercise mechanics: unchanged.
- Severe digit folds in the full invariant audit: 3 to 0.
- GLB seam audit folds over 100 degrees: V13e 4, V15f 2.
- Fingertip hole edges: 0.
- Matched open-hand, fist, curl, push-up and pull-up review generation: PASS.
- Visual-change signal: median changed subject 0.7012%, above rejected V14e's 0.1662% calibration.

All eight digit increments passed their ordered numeric and matched visual gates.
The resulting improvement is modest but consistent: the shaft flow is cleaner,
joint volume is retained, and no new pinch or razor crease was found.

## Review boards

- `renders_v15f_deep_hand_rebuild/V15F_V13E_OPEN_HAND_COMPARISON.jpg`
- `renders_v15f_deep_hand_rebuild/V15F_V13E_CLOSED_FIST_COMPARISON.jpg`
- `renders_v15f_deep_hand_rebuild/V15F_V13E_EXERCISE_HAND_COMPARISON.jpg`
- `renders_v15f_deep_hand_rebuild/V15F_DEEP_HAND_REBUILD_DETAILS.jpg`
- `renders_v15f_deep_hand_rebuild/V15F_DEEP_HAND_REBUILD_ANATOMY_AND_EXERCISES.jpg`

## Current-source integration limit

The optional latest-source integration run is not a completed pass. Its full
source suite reached 878 passing tests and one unrelated five-second timeout in
`src/body/neck.test.ts`. The focused production and V8 scans completed; the
V13e high-detail scan was deliberately stopped after running for a long time.
Partial evidence is retained under
`reports/current_source_v15f_deep_hand_rebuild/` and in the two latest-source
console logs. Do not report current-source integration as passing.

This incomplete optional scan does not invalidate the frozen legacy benchmark.
It does mean V15f must not be promoted. The new project direction ends imported
lineage work here and continues on the separate standalone first-party branch.

## Final decision

V15f is complete as a preserved legacy benchmark. Do not refit its grip, promote
it, merge it into the standalone lane, or continue polishing its geometry. The
next action is to switch to `work/standalone-first-party-audit-20260927` in a
separate worktree and follow that branch's standalone handoff.
