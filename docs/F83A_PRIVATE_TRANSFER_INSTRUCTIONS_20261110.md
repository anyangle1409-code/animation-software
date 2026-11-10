# F83a model-transfer receipt and instructions — 2026-11-10

The verified F83a Blender checkpoint was split into eight **byte-range** archives and one small START_HERE archive for direct PRIVATE delivery to Claude. No geometry or metadata in the .blend was altered. Reassembly was verified against the original source hash.

**Do NOT look for the .blend or the split ZIP archives in this public repository.** Transfer these binaries separately to Claude's code execution workspace, or make them available in an authorized private storage location.

### Expected files in the same directory
- `HGPT_F83a_START_HERE.zip` (contains this procedure, MANIFEST.json, reassemble_f83a.py)
- `HGPT_F83a_blend_part01of08.zip`
- `HGPT_F83a_blend_part02of08.zip`
- `HGPT_F83a_blend_part03of08.zip`
- `HGPT_F83a_blend_part04of08.zip`
- `HGPT_F83a_blend_part05of08.zip`
- `HGPT_F83a_blend_part06of08.zip`
- `HGPT_F83a_blend_part07of08.zip`
- `HGPT_F83a_blend_part08of08.zip`

### Reconstruction
1. Verify all nine ZIP names are present in the **same directory**. No part can be omitted.
2. Extract only `HGPT_F83a_START_HERE.zip` into that directory. Leave eight numbered ZIP files **zipped**.
3. Run `python3 reassemble_f83a.py` inside that directory. It checks each ZIP SHA-256, embedded chunk SHA-256, assembled byte size and complete file SHA-256; it refuses to overwrite an existing .blend.
4. Expected file:
   - `HGPT_FemaleV1_F83a_ManualChestRebuild_SETUP.blend`
   - 158,522,643 bytes
   - SHA-256 `a67ad573aa844199c1eb6bac8d6d0b913a482d95c0111624c737172e2b2bab7a`
5. Open in Blender 5.2.x and inspect embedded `READ_ME_FEMALE_CHEST_REBUILD` and the working and locked meshes. Use a NEW F84 output; F83a is a source-only checkpoint.
6. If **any** file is missing or checksum fails, STOP and request the missing piece by name. Do not fake, procedurally recreate or fall back to an earlier female model.

### Optional extra source checkpoints
- Parent `HGPT_FemaleV1_F23d_ReferenceChestShape_WIP.blend` (149,283,644 bytes, SHA-256 `3071c5a06bdfd88865c203115a0a24487b5a0e927e303950431c80358510a51f`) is useful for independent source comparison/recovery. F83a already contains an embedded locked F23d body; do not block routine F84 modelling for the parent if the locked comparison can be verified.
- Male source check `HGPT_MaleV1_Option5_StandingApprovalCandidate.blend` (70,169,105 bytes) is for later male rig/animation preflight, not required to resculpt female chest.

### Storage and privacy
`animation-software` is a public GitHub repo; Meshy-derived licensed Blender assets must not be added there. GitHub's ordinary 100MB single-file limit also prevents F83a as a normal commit. Git LFS in a separately private repo or private release assets may be options but require separate authorized setup and storage/quota checks.

### Smallest initial assignment
Verify/reassemble F83a, inspect meshes and packed reference, manually create F84, provide review renders; wait for owner appearance approval before full exercise motion.
