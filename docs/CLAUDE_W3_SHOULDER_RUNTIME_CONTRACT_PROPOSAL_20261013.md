# W3 proposal: shoulder-top deformation needs a runtime-contract decision (Claude, 13 Oct 2026)

**Status: PROPOSAL. Nothing is implemented.** It needs an owner decision, and Lane G must agree because it consumes the 67-joint contract (GPU palette, GLB, PR68's six-control map).

## Evidence that the current contract cannot fix the shoulder top

All measurements are on the unchanged original male with the reviewed PR110/PR111 coupled motion. "Pairs" means self-intersecting face pairs in the shoulder region.

| Attempt | Branch / PR | Outcome at 120–160° |
|---|---|---|
| Uncorrected | #111 | 160°: 42 collapsed faces, 444 pairs, volume −5.0% |
| Pose-space correctives (7 keys, damped and capped) | #112 | volume −1.5%; pairs not reduced (512 at 160°); crease wedges |
| Skin-weight diffusion | #112 diagnostic | 160° pairs unchanged |
| Weights-only LBS-conditioning refit (4 variants) | M1 branch, `d94ad0cd` | conditioning and collapse improve; pairs rise sharply at 110–145° |
| Shoulder press benchmark | #113 | worst benchmark: 48 collapsed faces, 462 pairs |

**Cause.** At 145–160° the shoulder-top skin blends bones whose rotations differ by 120–180°. Linear-blend skinning then collapses it (smallest singular value 0.0024). Correctives and weights only move the defect around.

## Options for the owner

**A. Shoulder-top helper deformer(s)** — recommended to trial first.
- Add one bone per side, for example `deltoid_helper_l/r`, parented to the scapula and driven at about half the humeral elevation.
- Move the fold-zone weights onto it.
- Cost: 67 → 69 joints. The GPU palette, GLB, the PR68 six-control map and the Lane G parsers must accept the extra joints, which are driven and never animated directly.

**B. Dual-quaternion or other skinning for the shoulder region.**
- Cost: the first-party engine's LBS shader changes. Work PR107 already rejected standalone volume-preserving skinning.

**C. Keep 67 joints and accept the defect.**
- Limit the shoulder press to 120° in the app until a later rebuild.

## Recommendation

1. Approve a review-only trial of **A** on a separate copy. Lane G's existing 67-joint path stays untouched until the trial passes the same 5° sweep metrics.
2. Use **C** as the interim app limit.

Claude will not change the runtime contract without that decision.

## Addendum, 14 Oct: in-memory feasibility data for option A

This addendum is measurement only. It is not the trial requested above, and no asset changed. Details are in `docs/CLAUDE_W3A_HELPER_DEFORMER_FEASIBILITY_20261014.md` on `claude/movement-benchmarks-20261013` (draft PR #113).

- **Conditioning is fixed.** A half-motion helper per side (67 → 69 joints) lifts zone conditioning: σmin goes from 0.004 to 0.12–0.19, and vertices below 0.1 from 100 to 0. Collapse drops 5–10× where the drive is defined (e.g. 140°: 40 → 4).
- **The drive is not defined overhead.** With the arms-down rest, the humerus turns about 177° relative to the scapula by 140°, and its twist is ill-defined near overhead.
  - A **half-rotation** drive flips past 180° (volume +3.1 → −7.1% at 145°).
  - A **half-swing** drive re-creates folds (630 pairs at 140°).
  - Both inflate the region at 90° (+1.8 → +5.2%).
- **What option A therefore needs:** a mid-elevation reference frame, a two-stage helper, or a stateful twist. Options B and C are unaffected. The owner + Lane G decision is still required.
