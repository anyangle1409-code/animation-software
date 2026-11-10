# Home Gym PT — Read-only stored checkpoint audit (2026-11-10)

Read-only bytes copied from ChatGPT Library into an isolated analysis container, SHA-256 calculated directly from each byte stream. The source Library files were not changed.

| Asset | Byte size | Current observed SHA-256 | Handover expected SHA-256 | Result |
|---|---:|---|---|---|
| HGPT_FemaleV1_F83a_ManualChestRebuild_SETUP.blend | 158,522,643 | 5b3b6a079352977a1a0b80697bd2fb4e96935b1f1b77a440dae5d8a468b28bed | a67ad573aa844199c1eb6bac8d6d0b913a482d95c0111624c737172e2b2bab7a | MISMATCH — investigate |
| HGPT_FemaleV1_F23d_ReferenceChestShape_WIP.blend | 149,283,644 | 2760af9636891971c142548e7d2ca8b0ee6d6662aebde8eab09dd2c5e3c6b497 | 3071c5a06bdfd88865c203115a0a24487b5a0e927e303950431c80358510a51f | MISMATCH — investigate |
| HGPT_MaleV1_Option5_StandingApprovalCandidate.blend | 70,169,105 | 73b902f16a4d10f5177028dc95127fa2aef0c9e8332e9d648f0b962eb61f6830 | no supplied authoritative expected SHA | CURRENT BASELINE ONLY |
| HGPT_Female_F12d_ChestShorts_WIP.blend | 151,227,275 | 89df9517421d983e0de812efd2d18a660e19bd6fa0284cdc45945b19affa3b6c | 89df9517421d983e0de812efd2d18a660e19bd6fa0284cdc45945b19affa3b6c | MATCH |
| HGPT_Male_Rig_07c_StandingCleanup_WIP_PROXY.blend | 18,444,779 | e9448c688d2ae83bc35c18678a353449e226c638298feef1482f123ac74b55a0 | e9448c688d2ae83bc35c18678a353449e226c638298feef1482f123ac74b55a0 | MATCH |

All five stored .blend copies start with `BLENDER17-01v0502`, a valid Blender file-header VERSION_1 form (17-byte header). This is NOT a malformed old-format header. Current Blender source supports both 12- and 17-byte headers. The F83a file also contains string occurrences of:
- `HGPT_Female_Body_F23d_REFERENCE_LOCKED`
- `HGPT_Female_Body_ChestRebuild_WORKING`
- `CHEST_REBUILD_REGION`
- `HGPT_FemaleChest_REFERENCE_FRONT_AND_SIDE`
- `READ_ME_FEMALE_CHEST_REBUILD`

Caution: name/string presence alone does NOT prove the file opens or the embedded geometry is intact. Blender/bpy is not installed in the audit container, so no Blender open/mesh/render verification was performed here. SHA mismatch can reflect an out-of-sync handover or altered asset bytes; do not assume either explanation before inspection. DO NOT rename these files to match the old hashes or declare approval.

At reset start in Blender 5.2.x:
1. Identify the exact source copies you can access. Calculate their SHA-256, sizes and header; record in the new session ledger.
2. Open the ACTUAL F83a in Blender read-only / save a working copy, check the five named objects/region/text and the packed front+side reference, compare F23d locked body against actual F23d separately.
3. Test original vs current hash discrepancy and locate any alternative original F83a matching the handover hash; DO NOT silently substitute F11a, F12d or unverified reconstruction.
4. If Blender opens and the locked body matches an independently verified F23d, establish a new verified baseline with an explicit mismatch explanation, then work on a copy (F84). If not, stop geometry changes and return an exact blocker report.
5. Preserve every version and owners' independent appearance/movement approvals.

Additional 2026-11-09 equipment read-only audit (ChatGPT Library: HGPT_EQUIPMENT_CHARACTER_COMPATIBILITY_20261109.md): 25/25 checked GLBs imported; Meshy freeweights/macines needed metre-scale corrections because some exports normalize to 1.9m; several machines are single connected mesh and not animation-ready without separate mechanically moving parts, pivots, grip anchors and collision proxies. Do not spend female chest/reset budget on machine separation; first proof uses the already size-corrected dumbbell and verified handle/hand frames.
