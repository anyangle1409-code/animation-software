# ORIGINAL v1 skeleton-motion lock — rig revision rev2 (twist helpers)

**Status: REOPENED 2026-10-02 (see `ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_REOPEN_20261002.json`) — the skeleton is OPEN again after owner visual review of r41: push-up foot/toes and shoulder/axilla/upper-arm form must be convincing against real-human movement before any lock. The text below is the withdrawn first lock, kept as history.**

Original status: RECORDED 2026-10-02 · machine record `ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_rev2_twist_helpers.json` · not a production approval

## Identity

| | |
|---|---|
| Rig identity | `hgpt_canonical_v4_original`, revision `rev2_twist_helpers` |
| Rig structure hash | `09d02e457813a5fe8b88cae396cb81dc7f911348a33c87a4d016474a0faea3d9` (names, parents, deform flags, rest head/tail/roll; weights/mesh excluded) |
| Previous rig | 63-bone v4, structure hash `19493caa822705224b7cef20cd905c1adb8d90250561ae6242f6e3dfd8359b35` — unchanged, preserved as history |
| Bones | 71 (70 deform + root) = 63 original + 8 helpers; payload `ORIGINAL_V1_WORK/hgpt_canonical_v4_original_rev2.json` |
| Locked candidate | r41, SHA-256 `19a3f9b4581693df103d5740bb0e3b03c4ad39d7f09a9898959894746803a94f` (parent r38 `7369b2d8…`) |
| Stress-pose definition | P2 (P1 preserved; see decision log) |

## What the evidence says (rows of `docs/ORIGINAL_V1_SKELETON_JOINT_VALIDATION_MATRIX.md`)

All 15 rows are LOCKED. In summary: the rig BONES had no defect; the P1 stress poses did (fingers, thumb, wrist, toes, humeral rotation, squat ankle,
push-up floor contact). Eight generic twist helpers were added. Per-row notes are in the lock record and the matrix.

Evidence set (all under `ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/`, hashes pinned in the record): rig structure audit (0 flags), skeleton-motion
audit (0 flags), fixed-axis finger/thumb audit (0 flags; r38 under P1: 84), continuous joint kinematics at 9 fractions × 15 poses with separate swing/twist
interpolation (0 path flags), movement-envelope check (25 110 components, 0 violations, 0 L/R asymmetries; r38 under P1: 412), twist-stress audit, floor-contact audit,
joint-centre fit + first-party anatomical proxy (`proxy_r41/`), skeleton-only and skin+skeleton before/after images (`review_skeleton_r41/`, `review_before_after/`, `skeleton_lock_r38/review_r38_before/`).
References: `docs/ORIGINAL_V1_SKELETON_REFERENCE_EVIDENCE.md`.

## Helper decisions

Added: `upperarm_tw0/tw1_{l,r}`, `forearm_tw0/tw1_{l,r}` — generic axial-twist distribution. Rejected/deferred: thigh twist, shin twist, palm/thumb helpers,
hallux + lesser-toe split (Phase 5F trigger: individually modelled toes), individual rib or chest-expansion bones, extra shoulder/thorax helper. Reasons in the record.

## Dependent regression results

* Full 15-pose evidence on r41 under P2 vs baseline P2B1: 2 development failures (P2B1: 5); 36 material improvements, 16 regressions (arm-region stretch ≤ 3.2 vs gate 5.0, two volume deviations, +6/+28 self-intersections) — left to the weight re-solve; not reclassified.
* Forearm-only variant r42 (comparison): 0 regressions, 5 failures — shows what the upper-arm helpers buy.
* Unit tests: see handoff.

## Runtime implication

The runtime must set the four helper rotations per arm from each arm segment's local rotation: `helper.local = Ry(−(1−f)·twist)` about the bone's own long axis,
`twist` = swing–twist angle of the segment's local rotation about local Y, `f` = 0 (tw0) or 0.5 (tw1). Interpolate joint motion as swing + twist separately, not one quaternion slerp.
The standalone runtime TypeScript payload (`src/rig/canonicalV4Original.ts`) is untouched; updating it to rev2 is a separate, prepared step.
