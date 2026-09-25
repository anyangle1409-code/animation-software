# V15 Work handoff — execution only

Read `V15_DEEP_HAND_REBUILD_PLAN.md` first.

The planning/diagnostic work has been moved out of Work. Work should spend its time only on Blender execution, render review and export.

## Baselines

- Start geometry: **V13e**
- Do not start from V14e.
- Frozen comparison pin: `614033b256d869230ea273522620467401b0bc71`
- Current source integration target at handoff creation: `47187360b5d631d438a6b33b284ad06732e244cb`
- Current source: 28 exercises; recorded suite 868 passed / 1 skipped.
- Keep source integration validation separate from the mesh branch. Do not merge branches.

## First action in Blender

Run:

`HIGH_DETAIL_MESH_WORK/scripts/prepare_v15_deep_hand_blender.py`

Expected result:

`HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.blend`

The preparation script changes **no vertex positions**. It creates diagnostic vertex groups so selection work is already done.

Use:
- `V15_PROTECTED_PUSHUP` — never move these
- `V15_PATCH_BOUNDARY` — anchor/seam boundaries
- `V15_SHARP_FOLD_35` — likely visible faceting
- `V15_REBUILD_CORE` — primary safe rebuild interior
- `V15_INDEX_L/R`, `V15_MIDDLE_L/R`, `V15_RING_L/R`, `V15_PINKY_L/R` — digit ownership

## Blender task

On the diagnostic copy, rebuild the actual shaft/joint surface topology for index/middle/ring/little fingers on both hands.

Do not repeat V14e's approach of only subdividing and smoothing.

Preferred order:
1. index
2. middle
3. ring
4. little
5. mirror/check the opposite hand continuously rather than doing one whole hand first

For each digit:
- preserve exact protected contact positions and skin rows
- preserve fixed anchor rings
- replace the visibly faceted interior patch
- make longitudinal edge flow follow the visible shaft
- use rounded cross-sections
- make joint transitions gradual
- transfer/normalise weights for new vertices
- inspect open hand immediately
- inspect closed fist immediately
- stop if a seam/contact must move to make the shape work

## Candidate naming

Use:
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.blend`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild_BARE.glb`

Do not overwrite V13e or V14e.

## Frozen validation

After export, run the existing hand finish/validation workflow against `614033b`.

The candidate must preserve:
- 682 protected contacts exactly
- bone/equipment matrices
- bare/dressed equivalence
- seams/manifold integrity
- exercise/retarget guards

## Current-source integration validation

In a disposable checkout of current `chatgpt/absolute-retarget-imports`, point `REAL_CHARACTER_GLB` at V15 and run the complete current character-switched gate set.

Also run the existing mesh coordination report comparing:
- V8
- V13e
- V15a

A hand-only rebuild should not materially alter the already-recorded body measurements.

Known existing V8/V13e body items are not reasons to modify this hand candidate:
- arm/chest baseline differences
- incline curl thigh graze
- near-limit bench support compression

## Visual review pack

Generate matched V13e/V15 views:
- open palm
- open back
- thumb/index-web angle
- closed fist palm
- closed fist back
- closed fist side
- curl grip
- push-up contact
- pull-up grip

Do not accept V15 because it has more topology or passes tests. Continue only if the broad segmented finger silhouette is visibly improved.

## Stop

Stop and report rather than compensating if:
- any protected contact moves
- the rebuild needs a grip/exercise/retarget change
- non-hand body changes
- a guard needs loosening
- new nonmanifold/open-edge defects appear
- visual improvement is marginal

No grip refit until this visual gate is passed.
