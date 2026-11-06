# Home Gym PT — Dual-character standing model preservation plan (2026-11-06)

## Scope
Preserve and verify the approved Male 07c standing structural base alongside continued correction of unapproved Female F12d. **Do not confuse standing base approval with final presentation V1, full animation signoff or licensing clearance.** No public assets, no merging, no destructive writes.

## Male 07c — critical source transfer still required
- Expected filename: `HGPT_Male_Rig_07c_StandingCleanup_WIP_PROXY.blend`
- Claude path: `./hgpt_ws/manual_retopology/rig/HGPT_Male_Rig_07c_StandingCleanup_WIP_PROXY.blend`
- Full SHA-256 as recorded in Claude's female F12d transfer MANIFEST:
  `e9448c688d2ae83bc35c18678a353449e226c638298feef1482f123ac74b55a0`
- Claude has stated ~18 MB. Verify actual bytes; if <30 MB, deliver as one ZIP, otherwise 24 MB max ZIP chunks with manifest, reconstruction and SHA-256 verification scripts.
- The male file was NOT among the eight female F12d ZIPs. It is currently unverified in the ChatGPT file-transfer environment. The manifest's hash identifies what to expect but is not proof of possession.
- Clarify whether this `WIP_PROXY` contains the complete needed source body, 07c rig, packed materials and external dependencies; do not silently treat a proxy-only checkpoint as the eventual fully textured V1.
- Source geometry, original Meshy reference and all reference textures must remain private. Check licensing evidence separately.

## Female F12d — actual transfer verified
- Actual reconstructed F12d `.blend`: 151,227,275 bytes and SHA-256 `89df9517421d983e0de812efd2d18a660e19bd6fa0284cdc45945b19affa3b6c`.
- All 8 ZIPs were transferred and tested in a previous ChatGPT turn. See `docs/WORK_F12D_TRANSFER_RECEIPT_20261106.md`.
- Blender 5.2.x fresh-open verification is still required at Work.
- Female standing approval is withheld pending bra, shorts/gusset, and other visible issues. F12d is not a final V1.

## Work sequence
1. Open Female F12d in Blender 5.2.x, verify exact hash, armature, garments, textures and source dependency state. Continue female standing model corrections on a separate Work branch only.
2. Obtain male 07c file from an independent, private Claude export or user-owned file. Verify full hash and fresh-open in Blender 5.2.x. Do not substitute the earlier Male Meshy GLB for 07c.
3. Create separate immutable reference copies (not relabel existing proxies as fully approved V1):
   - `HGPT_Male_V1_StructuralStanding_07c_REFERENCE.blend` only after verified owner-approved standing base is reproducible.
   - `HGPT_Female_F12d_WIP_REFERENCE.blend`; rename to Female V1 only after owner explicitly approves the female standing appearance, anatomy and skeleton.
4. Record for each: original path, source GitHub branch and commit, actual file SHA-256, Blender version, meshes and counts, materials, textures/packing, rig skeleton naming and bind pose, evaluation and user visual approval status.
5. Keep separately recoverable originals and rollback states; never modify the owner-approved male 07c file or any Claude checkpoints. Deformation tests may be planned but full exercise development remains paused.
6. Once female standing is approved, create anatomy standing V1 packages for both; finish appearance V1 only after user separately approves skin/hair/eyes/clothes; then create immutable backups for user's Windows laptop (with a second backup drive) and archive but do not delete prior attempts.
7. User must be shown paired front/back/side/three-quarter evidence, remaining defects, licence provenance and success/failure check results. The user alone approves the female.

## Immediate Claude request (short)
Export the exact current Male 07c Blender checkpoint with full SHA-256 and independent reopen proof; include a mini transfer guide, package each ZIP <=24 MB preferred / <30 MB mandatory and include materials/proxy dependencies required to reload. Prioritize exporting before Claude allowance resets. Do not perform any new male modelling or alter approved source. Optionally export F11a rollback after Male 07c is secured.

## Safety
Creating a GitHub text handover does not upload any licensed model geometry. Work must independently demonstrate possession and verification before claiming the male asset has been transferred.
