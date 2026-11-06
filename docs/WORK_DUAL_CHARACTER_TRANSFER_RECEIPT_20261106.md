# HGPT dual-character transfer receipt — 2026-11-06

Status: Model ZIP uploads inspected and hashed in ChatGPT file container; original male and latest female F12d are recoverable. Female F11a rollback **COMPLETE — part06of07 received, all seven parts reconstructed and final SHA-256 verified**. Blender 5.2.x fresh-open checks still needed in Work. This is a receipt, not approval of Female V1 or a declaration that Work already has the assets.

## Male 07c — RECEIVED / HASH VERIFIED
- Uploaded: `HGPT_Male07c_package.zip`, 15,103,690 bytes; ZIP integrity passed (no corrupt entries).
- Embedded structural standing checkpoint: `HGPT_Male_Rig_07c_StandingCleanup_WIP_PROXY.blend`, **18,444,779 bytes**.
- SHA-256 independently verified: `e9448c688d2ae83bc35c18678a353449e226c638298feef1482f123ac74b55a0`.
- Embedded geometry-only source GLB `meshy_male_source.glb`: 5,536,916 bytes; SHA-256 `9a033de91403300ac6d6ae000a19fa3356cbd706c1715f3d40eee1004e3fa85d`.
- Blender file was extracted byte-identically to local `HGPT_Male_Rig_07c_StandingCleanup_WIP_PROXY.blend`.
- Claude baseline open report: Blender 5.2.1 LTS, `MESHY_BODY` 56,677 vertices, 66 vertex groups, 14 corrective shape keys and normalized weights; `MESHY_RIG` 81 bones (66 deforming).
- **Critical limitation**: 07c is geometry/rig **PROXY** with no UVs, skin materials, or packed textures. The enclosed GLB is also geometry-only. The original `HGPT_Meshy_Male_Pro_1.82m_Clean_Unrigged.blend` (expected SHA-256 `b41518437550a6aa57df65c80c05fbc7955053619d94efa83f6587f54efe4e9f`) was not part of this Male07c ZIP. Work must not pretend male complete-appearance V1 is ready.
- Owner-approved male **standing structural appearance** only. Keep 07c immutable.

## Female F12d — RECEIVED / REASSEMBLED / HASH VERIFIED IN PREVIOUS TURN
- `HGPT_Female_F12d_ChestShorts_WIP.blend`: **151,227,275 bytes**.
- SHA-256 `89df9517421d983e0de812efd2d18a660e19bd6fa0284cdc45945b19affa3b6c`.
- All eight F12d transfer ZIPs available in this ChatGPT conversation; 7 model parts reassembled exactly. See `docs/WORK_F12D_TRANSFER_RECEIPT_20261106.md`.
- Female F12d remains **NOT APPROVED** for structural V1, clothing nor appearance. Main outstanding issues include shorts gusset and fabric/body clearance, bra construction/strap attachments, thumbs/hands and ponytail. Female exercise animation still paused.

## Female F11a rollback — COMPLETE / HASH VERIFIED
- Received all eight required ZIPs: `HGPT_F11a_START_HERE.zip` plus **parts 01 through 07**, including the initially missing part06.
- Independently checked every ZIP file's exact length and SHA-256 against the supplied `MANIFEST.json`, and then each extracted part's exact byte length and SHA-256; **all seven passed**.
- Independently reassembled the full checkpoint as `/mnt/data/HGPT_Female_F11a_ChestGroin_WIP.blend`, **151,331,378 bytes**; SHA-256 **`eafbc941aa2c92f99ceba9858e2cdc7aa9e562e882268f69324129a9a46c0573`**, an exact match.
- ZIP reconstruction succeeded without changing F12d, Male 07c or original part ZIPs. This is a **verified rollback**, not an owner-approved standing V1.
- Fresh open in Blender 5.2.x still needs to be performed in Work; this ChatGPT container lacks Blender.
- The START_HERE `MANIFEST.json` uses the property `f12d_blend` despite referring to F11a; this naming typo does not affect stored expected F11a file hashes.

## Immediate Work execution gate
1. Access the exact male and female F12d assets through user-provided private attachments or files. GitHub docs don't contain licensed geometry.
2. Independently compare file SHA-256 and open both in Blender **5.2.x**; compare object counts/bones/packed textures against Claude baselines.
3. Store untouched reference copies and hashes. Work only on copies under its own branch, never on Claude's branch or approved male checkpoint. Keep licensed assets private.
4. Male lane: verify structural 07c and package as an immutable approved standing reference; identify missing source for materials/UVs and reserve full presentation V1 for later separate owner approval. **Do not** refit male skeleton or start male exercises.
5. Female lane: continue F12d **standing model corrections** and produce review renders; no comprehensive animation/deformation projects or production merges. Owner alone grants Female V1 approval.
6. F11a rollback transfer is complete; independently open F11a in Blender 5.2.x and maintain it read-only as a rollback from the current F12d candidate.
7. Never archive/delete source attempts before having two independently verified durable backups; record commercial licence provenance for the original Meshy generation conditions.

## Source GitHub context
- Claude F12d transfer commit `8056f71ddc42415fa266766974a4cd2f119b10b9`, source branch `claude/home-gym-pt-animation-txux66`.
- Work handover branch `chatgpt/f12d-work-handoff-20261106`.
- Primary handover: `docs/WORK_F12D_CONTINUATION_20261106.md`.
- Existing combined checklist: `docs/WORK_MALE_07C_AND_FEMALE_F12D_CHECKPOINT_PLAN_20261106.md`.

## Verification limits
No independent Blender 5.2.x open was performed in the ChatGPT container (binary unavailable). A binary header and SHA-256 check is not a rig validation. Screenshots/reports are evidence from Claude's tests, not a replacement for Work re-running validation.
