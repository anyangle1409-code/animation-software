# Phone / Cloud Work → Laptop Blender Handoff

Use this file when starting Work from a phone or cloud environment before the laptop is available.

## Shared branch

Work only on:

`codex-high-detail-candidate-v11-hand-cleanup-20260924`

This branch starts from the prepared V10 state at `f68516cbbe755833f1872793a71ff027ef087373`.

## What phone/cloud Work SHOULD do now

Without Blender, do all useful preparation that does not alter the actual mesh:

1. Read:
   - `WORK_MASTER_HANDOFF.md`
   - `V11_HAND_CLEANUP_PLAN.md`
   - `REVIEW_V10_HAND_ANATOMY.md`
   - `CURRENT_STATE.md`

2. Audit the V10 reports and matched renders and turn the visible problems into a precise V11 edit checklist:
   - fingertip cap faceting
   - ring-like DIP/PIP/MCP banding
   - thumb-index web seam
   - stepped wrist transition

3. Inspect the existing V10 Blender/Python build and correction scripts and prepare any candidate-only script changes needed for V11.
   - Reuse V10 topology where possible.
   - Do not execute Blender-dependent modelling in the cloud.
   - Do not alter accepted runtime/rig/exercise code.

4. Prepare exact validation commands for V11 using the existing runtime source `614033b` and frozen `hgpt_canonical_v3`.

5. Prepare matched V10/V11 review-board definitions/cameras so the laptop run can render:
   - open palm
   - back of open hand
   - thumb-index web
   - closed fist palm/back/side
   - curl grip
   - push-up contact
   - pull-up grip

6. Commit and push all prep to this same V11 branch.

## What phone/cloud Work MUST NOT do

Do not:
- edit the `.blend` file without Blender
- claim visual V11 geometry is complete
- modify the frozen 63-bone hierarchy
- refit grips
- change exercise mechanics
- move equipment
- enable palm cupping or scapular rhythm
- promote production assets
- overwrite V8, V9 or V10

## Laptop continuation

When the laptop is available, Desktop Work should:

1. Fetch/checkout this exact V11 branch.
2. Read this file plus `V11_HAND_CLEANUP_PLAN.md`.
3. Run `RESUME_WORK.bat`.
4. Open/use the V10 editable Blend as the starting geometry.
5. Execute the prepared V11 Blender cleanup.
6. Export separate V11 dressed/bare GLBs.
7. Run all prepared guards and review renders.
8. Commit/push the V11 result to the same branch.
9. Stop for visual review before any grip refit.

## Continuity rule

The phone/cloud session and laptop session must share progress only through committed/pushed GitHub changes on this branch. Do not rely on uncommitted local files or an open Blender session for handoff.
