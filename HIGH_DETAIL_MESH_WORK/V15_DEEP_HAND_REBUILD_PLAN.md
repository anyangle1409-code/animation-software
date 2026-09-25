# V15 deep hand rebuild plan

## Purpose

Reduce ChatGPT Work's Blender time to execution, visual inspection and export.

This branch is preparation only. It does **not** promote a mesh, change production assets, alter exercise mechanics, change the frozen rig, or merge source/runtime work into the mesh branch.

## Fixed state

- Body/knee geometry baseline: **V8**
- Hand geometry starting point: **V13e**
- V14e: **experimental/rejected visual checkpoint; do not use as the geometry baseline**
- Frozen canonical hierarchy: `hgpt_canonical_v3`, 63 bones, structural freeze `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`
- Historical reproducibility/runtime comparison pin: `614033b256d869230ea273522620467401b0bc71`
- Current source integration target when this plan was prepared: `chatgpt/absolute-retarget-imports` at `47187360b5d631d438a6b33b284ad06732e244cb`
- Current source state: 28 exercises; recorded suite **868 passed / 1 skipped**
- No grip refit until the hand geometry is visibly accepted.

## Why V14e failed

V14e split 2,737 long finger-body edges, added 5,474 triangles and applied constrained relaxation. It passed the technical guards, but the posed hand moved by less than a millimetre and the broad segmented/faceted shaft silhouette remained.

Therefore the next candidate must **replace or redirect the actual finger shaft / knuckle / joint surface topology**, rather than only adding loops or smoothing the inherited surface.

## Scope for V15

Start from:

`HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.blend`

Work only on index, middle, ring and little fingers on both hands.

### Change

- finger shaft cross-section and longitudinal flow
- MCP/PIP/DIP surface transitions where present in the mesh
- the unwelded/local patch topology that causes angular segmentation
- local connection/bridge topology needed to make the shaft surface continuous
- existing V13e distal caps may be retained unless a rebuilt shaft requires a cleaner transition

### Preserve exactly

- **all original V8-source vertex records and their `v8_source_id` values**; rebuild by rewiring/retriangulating and adding vertices, not deleting original source vertices
- all 682 protected original push-up contact vertices and their skin rows
- non-hand body geometry
- thumb, palm and wrist for this candidate unless a tiny bridge is unavoidable at the digit root
- frozen 63-bone hierarchy
- bone matrices and equipment matrices
- UV/material identity outside rebuilt local patches
- current exercise mechanics, grips, contacts, retargeting and production references
- scapular rhythm OFF
- palm/thumb exercise motion OFF

## Geometry method

The next pass should be a **local patch rebuild**, not another subdivision/smoothing pass.

For each digit:

1. Identify the surface patch owned by that digit from deform weights.
2. Identify and pin:
   - protected push-up vertices;
   - patch/seam boundaries that must remain fixed;
   - a transition ring around protected/boundary anchors.
3. Find the broad faceted shaft/joint region.
4. Remove/rebuild **faces and edge flow**, but retain every original source vertex. Do not delete a vertex carrying a positive `v8_source_id`.
5. Reconnect/retriangulate the retained vertices and add new vertices only where the shaft/joint surface needs more control.
6. Reconstruct longitudinal loops so cross-sections are rounded and joint transitions are gradual.
7. Bridge back to the fixed anchors without moving protected vertices.
8. Interpolate UVs and bone weights onto every new vertex; normalise bone weights.
9. Preserve left/right symmetry.
10. Check open hand before any posed review.
11. Only then check fist/curl/push-up/pull-up.

Do not force the topology to follow bone tails; V13e proved the visible finger surface ends 9–20 mm before some frozen bone tails. Use the actual mesh surface as the geometric reference.

## Diagnostic preparation

Run:

`scripts/prepare_v15_deep_hand_blender.py`

It creates a no-geometry-change diagnostic copy:

`HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.blend`

and adds selection groups:

- `V15_PROTECTED_PUSHUP`
- `V15_PATCH_BOUNDARY`
- `V15_SHARP_FOLD_35`
- `V15_REBUILD_CORE`
- per-digit groups `V15_INDEX_L`, etc.

The script must report **0 mm geometry displacement** because it only prepares selections.

## Visual acceptance

A V15 candidate is not accepted merely because it passes guards.

It must show a clear improvement over V13e in matched views:

### Open hand
- finger shafts read as rounded anatomical forms rather than broad planar segments
- no abrupt angular band at joint transitions
- no new seam/open edge
- fingertip-to-shaft transition remains smooth

### Closed fist
- no obvious stepped/segmented silhouette
- PIP/DIP bends do not pinch into sharp wedges
- neighbouring digits remain separate and plausible

### Curl and pull-up grips
- finger body silhouette follows the handle/bar more naturally
- do **not** judge final contact/wrap yet; grip offsets remain frozen until Phase C

### Push-up
- protected floor contact is unchanged
- no new floor penetration or visible collapse around pinned vertices

If the visual change is again marginal, reject the candidate even if every test passes.

## Two separate validation lanes

### Lane A — frozen comparison

Use runtime `614033b` exactly for reproducibility.

Require:
- protected 682-contact guard exact
- five focused mesh/retarget guards
- bare/dressed equivalence
- bind and posed seam audit
- sampled exercise comparison
- zero unexplained bone/equipment matrix change

### Lane B — current-source integration

Use a disposable checkout of the latest `chatgpt/absolute-retarget-imports` HEAD. At preparation time that is `47187360...`.

Do not merge the source branch into this mesh branch.

Run every gate that switches character through `REAL_CHARACTER_GLB`, including:
- full exercise library
- arm/trunk self-collision
- equipment clearance
- floor contacts
- feet/lunge/split-squat contact gates
- hand roll
- palm mapping
- unmapped-bone/importer diagnostics
- mesh coordination report

Known current body-shape differences for V8/V13e are not hand blockers: arm-to-chest baseline gaps, the incline-curl thigh graze, and near-limit bench compression. A hand-only V15 should not materially change those body measurements.

## Stop conditions

Stop and report instead of compensating if:
- any protected push-up vertex or its skin row moves
- a fix needs an exercise, grip, equipment or retarget change
- a validation threshold would need loosening
- non-hand body geometry changes
- a canonical bone change appears necessary
- new open edges/nonmanifold geometry appear
- bare/dressed posed equivalence breaks
- the visual improvement is too small to justify the added topology

## Output

For the candidate report, record:
- exact source and candidate filenames
- vertex/triangle delta
- maximum moved original vertex
- protected-contact max move
- boundary-anchor max move
- new-vertex weight loss
- nonmanifold / degenerate count
- frozen comparison results
- current-source full-library results
- matched V13e/V15 review boards
- explicit visual verdict: improved enough to proceed, or reject


## Post-edit automation

After the V15 Blend is edited and saved, do **not** manually rediscover export/test commands.

Run:

`RUN_V15_POST_EDIT_ALL.bat`

It performs, in order:

1. Blender invariant audit against V13e.
2. Dressed V15 GLB export using the established stable-ID hand packer.
3. Bare variant creation.
4. Frozen `614033b` structural/hand/exercise validation.
5. True matched V13e-vs-V15 open/fist/curl/push-up/pull-up renders and boards.
6. Disposable latest-source integration validation against the newest fetched `chatgpt/absolute-retarget-imports`.
7. Cleanup of the detached validation worktree.

The export step refuses to overwrite an existing V15 GLB. Preserve failed/rejected attempts rather than replacing them.
