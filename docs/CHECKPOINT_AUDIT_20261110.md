# Home Gym PT — Corrected read-only checkpoint audit (10 November 2026)

**Correction:** an earlier draft of this report incorrectly recorded SHA-256 mismatches for the F83a and F23d library copies. Re-running `sha256sum` directly over the materialized source bytes confirms BOTH match their handover records exactly. The earlier mismatch claims were erroneous and are withdrawn. No Blender open/deformation test has yet been performed.

| Asset | SHA-256 checked from actual source file | Expected handover | Result |
|---|---|---|---|
| HGPT_FemaleV1_F83a_ManualChestRebuild_SETUP.blend | `a67ad573aa844199c1eb6bac8d6d0b913a482d95c0111624c737172e2b2bab7a` | same | **MATCH** |
| HGPT_FemaleV1_F23d_ReferenceChestShape_WIP.blend | `3071c5a06bdfd88865c203115a0a24487b5a0e927e303950431c80358510a51f` | same | **MATCH** |
| HGPT_Female_F12d_ChestShorts_WIP.blend | `89df9517421d983e0de812efd2d18a660e19bd6fa0284cdc45945b19affa3b6c` | same | **MATCH** |
| HGPT_Male_Rig_07c_StandingCleanup_WIP_PROXY.blend | `e9448c688d2ae83bc35c18678a353449e226c638298feef1482f123ac74b55a0` | same | **MATCH** |
| HGPT_MaleV1_Option5_StandingApprovalCandidate.blend | `db79984aba305c42c1fe5ebd0cf5d18d2cfd9a611673d502e3475cb18669399a` | no authoritative handover hash supplied | **measured baseline only** |

The files remain separately preserved, not written to or altered. They were checked using the Linux operating system `sha256sum` command on the original materialized bytes. The F83a and F23d names refer to the EXACT current source files from the user's Library. The earlier incorrect male Option5 baseline is also corrected.

### What this establishes and what it does not
- **Establishes:** F83a, F23d, F12d and original male07c are byte-for-byte the versions documented in their handovers. There is no hash-identity discrepancy to investigate before F84.
- **Does not establish:** that Blender 5.2.x can actually open all files, that the F83a locked reference object has unmodified mesh geometry, that its weight maps are valid, or that female V1 is visually approved. Blender/bpy is absent from this audit environment; do not misreport an open test.
- The F83a file is documented as having the locked F23d body, separate working mesh, CHEST_REBUILD_REGION 7,522 vertices, packed front/side reference and cameras. These still need an actual Blender inspection at Claude session start.

### Reset-start minimum verification
1. Open the verified F83a directly in Blender 5.2.x in a read-only fashion; check body objects, text block, packed image, editable-region size, rig and modifiers.
2. Check frozen F23d against its independently verified file and checkpoint. Save work only as a new numbered F84 .blend, never over F83a/F23d.
3. Produce F84 chest patch and compare bare and clothed front/three-quarter/side, then await user's standing appearance approval.
4. Perform the separate generic model/rig read-only audit using the audit tool in `scripts/preflight/v1_character_readonly_audit.py` if available, and existing project-specific test scripts; do not rewrite prior test infrastructure.
5. Preserve audit JSON, images, exact versions and SHA evidence, and continue only after the correct approval gate.

### Related equipment audit
The independent report `HGPT_EQUIPMENT_CHARACTER_COMPATIBILITY_20261109.md` inspected 25 GLBs; several Meshy equipment meshes have scale corrections and the complex machines require separated moving parts/pivots and contact anchors before animated mechanisms. Keep those tasks separate from F84; the first exercise pilot can use a previously scaled dumbbell with verified handles.

**No original checkpoint .blend file was modified during this audit.**
