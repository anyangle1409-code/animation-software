# R56 ORIGINAL_v1 shoulder per-control feasibility (20 October 2026)

**Scope:** read-only key-level certificate. No Blender model, skeleton, skin weights, S5/S7 shape-key coordinates, topology, app, production asset or existing acceptance threshold is modified.

## Motivation

R55 demonstrated that the previously authorized 26-weight-vertex patch cannot explain the entire moving shoulder defect. Its 1,711 high-excess posterior vertices include 723 with a frozen-arm flag **in at least one original source key**. This is not equivalent to saying that all such vertices are frozen at all angles.

R56 reconciles *three different concepts*: the exact seven source-key edit masks, the historical per-source frozen-arm flags, and R52's independent 72-control temporal support. The distinction matters because the latter uses a union-derived mask for intermediate controls but retains original 110/166 zero constraints.

## Invariants

- Root source R52: run 39215634074, SHA256 source `2a6c01cf7eacd3d1ceb47ae9f131f76dd0487fce5d3518d5cd1df65bc059fa8d`, dense solution `b3a6c404a944753facde5a92db8bc4547a1ca756960b6b82df2875f5e4eb804f`.
- R55 native-derived hotspot certificate: run 39408787280. The original 1,796 back-vertex region, 40.644618 mm unchanged-motion excess and S7-off R41/R52 identity must be reproduced in this stage.
- Source keys 110,120,130,136,145,156,166 degrees. Dense ghost 95 and source 110/166 nodes remain zero. No permission change; original R47 mask and `allowed_dense` algorithm are used unmodified.
- Checks reject any response whose saved R52 deltas violate the original permission masks or 45 mm cap.
- Original R47 overall outline approval is a **marked-pose-only owner decision**. It does not certify full motion, folds, contacts, normals or anatomy.

## Deliverable

Machine-readable certificate reports per-source permission and frozen status at each key for worst motion hotspot 19057, early outward vertex 20913 and old edge vertices 18081,21057,18057,21044, as well as R55's 40 highest-excess points. For each selected point it records all 72 current dense permissions and actual R52 increment magnitudes. Counts per key cover the actual original posterior region, and detailed flags cover 118/119-degree motion nodes.

**Interpretation:** intermediate dense union support does **not** silently override source-key protection. Before a candidate can be created, identify whether a proposed motion correction needs any source-frozen material at adjacent original key(s) and whether its effect on other frames/contact/surface remains admissible.

## Decision policy

- If the effective correction can fit wholly within existing per-key controls and unchanged 45 mm material envelope, author a reversible **S7-only** local candidate in a separate owner-review study; keep original contact/orientation/motion/crease/benchmarks and visual review. The feasibility audit itself is not a repair.
- If the required geometry is source-frozen or a weight/rig/helper change is needed outside prior authority, stop and record the exact exception needed. Previous one-off 26-vertex weight experiment does **not** automatically authorize a larger patch.
- Preserve original 1.82 m height, skeleton-first policy, R47 preferred arm-to-body contour and newer arm/elbow detail. No third-party assets; anatomy illustrations are references only.

Keep this PR draft, stacked on R55. No merge, deploy or production model-save.


## Verified real-source result (20 October 2026)

Cloud run https://github.com/anyangle1409-code/animation-software/actions/runs/39409903836 — SUCCESS, all **5 focused unit tests pass**, both original R52 source and dense-solution hashes verified. This is only an editing-scope certificate.

For the original 1,796-vertex posterior region:
- Source 110° and lockout 166°: **0** R47 editable source vertices; dense nodes 95°,110°,166° remain zero.
- Source 120°,130°,136°,145°,156°: **1,776** R47 editable source vertices at each key, with 20 outside that specific authorised back subset.
- In the older `frozen_arm` source array, 120° marks 744 posterior vertices and 110° marks 755. These flags and later `r47_allowed` are **distinct**; R47's owner-approved source permissions can overlap older flags. We do NOT infer a new blanket right to alter all weights, geometry or source-locked controls.
- Across the top 40 worst R55 motion hotspots, **40/40** have the *existing* R52 dense controls 118°/119° allowed. All 40 have an old frozen-arm flag at 110° or 120°. That does not mean the dense R52 mask was automatically rewritten or that surrounding motion is safe.
- Worst vertex **19057**: source 110° R47 disallowed / frozen-arm flagged; source120° R47 allowed / older frozen-arm flagged. The exact existing 118° and119° dense controls are allowed, but the historical lockout remains zero.
- Vertex **20913**: source110° R47 disallowed / not old-frozen; source120° R47 allowed / not old-frozen; 118°/119° dense allowed.
- R52 161-pose movement excess **40.644618 mm**, S7-muted R41/R52 identity **0.0 mm**, unchanged from R55. No geometry, anatomy or exercise benchmark was revalidated by this certificate.

**Decision:** an S7-only *unsaved, local temporal study* in the pre-existing dense allowance is supportable. Protect source110/166, ghost95, non-S7, skeleton/Basis/weights, topology, anchors, distal arm, 45 mm source/dense cap and original acceptance thresholds. Study design must avoid broad global S5/S7 amplitude changes (R54 rejected) and never repeat 26-vertex averaging (R53 rejected). If an actual correction needs more scope, request owner authorization separately. Any R57 result requires full native Blender movement/area/contact/crease/13 benchmark evidence and matched images before owner visual decision.
