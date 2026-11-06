# Home Gym PT — Female F12d Work Continuation / Transfer Handover
Date: 2026-11-06 | Status: handover prepared; **F12d is NOT approved or available to Work until actual Blender files are transferred**.

## Trusted source and immutability
- Source repository: anyangle1409-code/animation-software.
- Claude development branch: claude/home-gym-pt-animation-txux66.
- Verified Claude F12d commit: 3bee9e1f1f6f8ca8fe21bcbec0ef892974cb14ca (2026-11-06 16:39 UTC).
- Isolated handover branch: chatgpt/f12d-work-handoff-20261106, created from that exact commit. Work should create **its own separate working branch** from the newest verified source, not modify Claude's active branch.
- **Male 07c** is the approved structural standing base; keep its geometry/rig/checkpoints unchanged.
- **Female F12d** is a WIP **candidate only**. Owner withheld visual approval of the female. Neither character has a final, verified presentation V1 package yet.
- Original source GLBs and all Blender checkpoints contain potentially licensed geometry; DO NOT commit them to a public repository or publish them as public release artifacts. Licensing clearance (original Meshy generation tier, privacy settings, commercial rights) must be documented before publication.

## CRITICAL blocker: actual model is in Claude's temporary session
GitHub contains scripts and test reports, **not the actual female F12d .blend checkpoint or the source textures/model**. Current best checkpoint is reported by Claude as:
- HGPT_Female_F12d_ChestShorts_WIP.blend
- Claude session workspace: hgpt_ws/female/retopo/ (under its temporary scratchpad)
- Reported checksum begins 89df9517…; **obtain and verify the full SHA-256**, not just the prefix.
- Also preserve F11a as rollback, source assets, external textures (packed or separate), baked albedo, ponytail mesh, separate bra/shorts, armature and helpers, scripts/config versions, plus last review renders and JSON reports.
- Do not infer that Work can access the temporary Claude session scratch directory or a downloaded file without an explicit private upload.

## REQUIRED handover from Claude while it still has usage
1. Finish any **already-running write** safely, then stop new modelling.
2. Save F12d checkpoint as a new verified, read-only file; also retain F11a and male 07c. Export an F12d .blend and optionally a GLB for interchange. Use .blend as the editable source of truth.
3. Validate that the .blend reopens in Blender in a fresh session, meshes are present, rig and weights exist, garment meshes are separate, textures are packed or delivered, the scene isn't linked to ephemeral external files, and expected counts match.
4. Write a plaintext HANDOVER.txt or .md with absolute original paths, filename, file sizes, **full SHA-256**, Blender version, asset list, last completed work and blockers, and commands to regenerate the diagnostic renders. Record source asset licence provenance.
5. Package each upload as separate parts **strictly under 30 MB** (prefer <= 24 MB each to allow margin); make self-contained ZIP parts and a small START_HERE package with a reconstruction script, per-part SHA-256 manifest and reconstructed-file SHA-256 checks. Never downsample the geometry or re-encode/replace the model for transport.
6. Upload the parts to a PRIVATE durable location that the user can retrieve and upload to ChatGPT Work, or give the user downloadable parts immediately. A local Claude scratch path is **not** a transfer.
7. Confirm the complete set was downloaded/received, reconstructed and hashes checked in the destination before considering the handover secured. If that is not yet possible, explicitly record **BLOCKED: F12d source unavailable to Work**.
8. Exclude superseded F12b/F12c from required files: Claude reports those trials were deleted for scratch space. Preserve all surviving verified checkpoints.

## Already pushed and available from GitHub
- Progress log and measured F12 results: review-assets/meshy_retopo_20261105/README.md, section "F12 — Female chest and shorts corrections".
- Reports: review-assets/meshy_retopo_20261105/female_f12/ (F12d_Gusset_report.json, chest_test_F12d.json, hip_F12d.json, topology_F12d.json, source_comparison_F12d.json).
- Modelling scripts: scripts/retopology/female/gusset_shorts_f_blender.py, rebuild_shorts_f_blender.py, bra_cups_f_blender.py, and the earlier F10–F11 scripts.
- Render and test scripts: scripts/meshy/female/review_chest_shorts_f_blender.py, chest_sections_f_blender.py, chest_sections_draw.py, make_f12_sheets.py, hip_flexion_clearance_f_blender.py, chest_bra_elevation_test_f_blender.py.
- Female chest motion requirements: docs/FEMALE_CHEST_BRA_MOVEMENT_REQUIREMENTS_20261106.md.
- Confirm newest Claude head first; do not repeat finished F12d fixes.

## F12d current state — verified against GitHub reports
- **Chest:** Female body underlying the bra already has two distinct breast contours with ~30 mm sternum valley. Problem diagnosed in the **source-derived bra**: formerly a nearly flat shelf. F12d bra is eased towards sternum (reported central clearance 3.5 mm) and has two supported cups. One **non-manifold garment edge**, three bra components, and 70 cup vertices > 6 mm from skin (max 9.3 mm). No owner's visual approval.
- **Shorts:** F11a had a pointed tab, slit and spike. F12d replaces crotch with continuous quad gusset and rebuilds garment skin weights. In standing and hip 45/knee 60 tests, reported 0 exposed skin vertices; at hip 90/knee 90 there are **12** exposed skin vertices (down from 23 in F11a). Short corners/hem tips and stepped waistband remain visible. The screenshots show an elongated gusset point in certain views: visual fit still requires review and likely further refinement. A collision test alone is not proof of realistic clothing.
- **Body:** 50,090 vertices, closed all-quad mesh, 52 self-intersecting face pairs in hands/thumb collars. Source proportions within ±0.3% (reported).
- **Raised arms:** Diagnostic was glenohumeral-only (0/45/90/135/170), not full anatomical shoulder rhythm and not complete motion validation. Breast core stretch reported 1.00; check images show persistent shoulder/armpit/strap distortion. Record rather than embarking on a major movement cycle.
- Earlier outstanding: thumb topology/pinch; strap junction knots; triangular/low-fidelity ponytail; bra non-manifold edge; shorts waistband and gusset aesthetics; model face/skin/eyes/hair final presentation not signed off.
- Preserve geometry and rig constraints; don't recreate/reshape entire character or change its approved source proportions.

## Work execution sequence — only after all files have been transferred and verified
1. Verify GitHub read access, exact incoming checkpoint filename, file bytes/hashes, Blender version, and successful open in a fresh Blender session. If .blend missing/invalid, **stop**; do not substitute Meshy source, F11a, images, or script-based guesswork and call it F12d.
2. Create an isolated Work branch from the verified latest commits. Do not write to Claude's branch, main, or the approved male 07c files. Keep any licensed .blend/.glb assets in a private store; scripts/notes/tests may be committed.
3. Run read-only baseline tests and render F12d using the existing scripts; compare all key numbers with GitHub F12d report before editing.
4. Highest-priority **female standing** issues: evaluate clothing anatomy as viewed by user; improve bra's natural two-cup contour, preserve underlying two breast forms, correct shorts coverage and trim/waistband/gusset aesthetics, remove garment intersections and prevent bare skin at hip flexion. No extravagant cleavage or anatomy; realistic athletic character.
5. Repair the thumbs and hand intersections, then strap junctions, ponytail mesh and visible residual defects, while guarding full-body proportions and garment-body separation. Require measurable regressions and aligned same-camera before/after images.
6. Do limited structural pose preflights only to assess garment attachment/clearance. DO NOT launch full exercise animation, prolonged shoulder deformation or male refits.
7. Save each iteration as a separate version, including its .blend, manifest, full hashes, reports, comparison renders and rollback; do not mark Female V1 approved.
8. Stop for user visual approval of **female standing anatomy + clothing**; then plan immutable male/female anatomical and complete-appearance V1 packages, verified GLBs/textures/licence records, and Windows laptop backups.

## User-visible status report requirements
Every status update should specify (A) physical model asset present and hash-verified? (B) GitHub HEAD and independent Work branch, (C) current .blend checkpoint and completed changes, (D) exact passing/failing diagnostic metrics, (E) unresolved visible defects, (F) files and screenshots delivered, (G) whether user visual approval is pending.

## Notes
The 30 MB limit is the user's chat upload ceiling, not a licence limit. Do not claim any F12d .blend has been transported merely because this GitHub handover exists. Never claim ongoing work or automated resumption across account usage resets unless an actual scheduled workflow has been configured and verified.
