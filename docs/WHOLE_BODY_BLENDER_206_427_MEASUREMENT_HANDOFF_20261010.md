# HOME GYM PT — Whole-body Blender anatomical evidence gate
10 October 2026 — Independent source-first code branch; no production geometry changes.

## Current scope and purpose

The established project inventory contains 206 conventional adult bone IDs, 427 named joint/contact records, and 46 ancillary non-206 structures such as costal cartilage, wrist TFCC, ligaments, fused subcomponents and accessory sesamoids. A source-verified check identified 59 of the 427 records involving at least one such ancillary structure. Accordingly, a mesh-to-mesh bone-only clearance is NOT a complete cartilage-inclusive joint contact.

The first-party auditor at scripts/anatomy_fit/whole_body_blender_evidence_gate.py accepts a JSON file containing ACTUAL, LOCAL bpy-evaluated bone geometry and per-pose joint measurements. Its role is conservative measurement coverage and provenance control. It never validates named bone anatomy by itself, corrects skeleton proportions, promotes a region to READY, changes the original model, or refits skin.

## Procedure for Work on the laptop

1. Preserve existing Claude and Work branches; create a separate Git worktree using codex/whole-body-blender-evidence-gate-20261010. This branch is separate from Work's laptop CT/Blender verification.
2. Run this read-only template-generation command from the isolated worktree in Windows Command Prompt, with Python 3 installed:

    py -3 scripts/anatomy_fit/whole_body_blender_evidence_gate.py --template-only --out "%USERPROFILE%\HomeGymPT_Private_Original_CT_Review\whole_body_bpy_source_report_TEMPLATE.json"

The resulting template is deliberately EMPTY and its source_was_evaluated_by_bpy field is false. No Blender scene is implied.

3. Only after actual local Blender evaluation, fill a NEW private measurement JSON with the real source bone IDs, actual evaluated mesh hashes, triangle/vertex counts, closed-mesh classification, world-space bounds and pose/frame-specific contact measurements. The report references the exact source commit SHA and real private .blend SHA-256.
4. Verify the original .blend file independently (not just the report claims):

    py -3 scripts/anatomy_fit/whole_body_blender_evidence_gate.py --input "%USERPROFILE%\HomeGymPT_Private_Original_CT_Review\whole_body_bpy_MEASURED.json" --scene-file "%USERPROFILE%\HomeGymPT_Private_Original_CT_Review\ACTUAL_SKELETON_REVIEW.blend" --out "%USERPROFILE%\HomeGymPT_Private_Original_CT_Review\whole_body_bpy_audited_v1.json"

The CT-only Blender display file is NOT a replacement for an actual anatomical skeleton .blend. If it contains display planes rather than correctly tagged 3D bone surfaces, coverage should properly remain incomplete.

## JSON measurement contract and limitations

The generated template contains the exact schema and hashes of the SOURCE inventory JSON encoded as sorted/minified JSON. It requires:
- provenance.git_commit_sha: exact 40-character Git commit.
- provenance.blender_scene_sha256: SHA-256 of the actual read-only .blend file, recalculated during the audit.
- provenance.world_unit: "metres"; provenance.anatomical_label_basis: "source_anatomical_bone_id"; provenance.scene_was_evaluated_by_bpy: true ONLY after Blender genuinely ran.
- bone_surfaces entries for source IDs (not automatically mapped via runtime *_l or *_r suffix; the r95 side mapping has been documented as reversed). Each observation contains real Blender object name, mesh buffer SHA-256, vertex count, triangle count, bounds in metres, watertight mesh test, and an explicit surface_kind: blender_evaluated_mesh, reference_mesh or simplified_proxy. Expert identity flags stay false.
- poses entries with frame number, unique pose ID, movement family and zero or more original 427-articulation-indexed per-frame measurements.
- separation methods: mesh_bvh_unsigned for unsigned nearest mesh distance, control_stick_distance for proxy distances, mesh_bvh_signed ONLY for independently defensible inside/outside signed methods on actual closed corresponding 3D bone surfaces. Ordinary unsigned BVH proximity is not evidence of a negative signed penetration.
- anatomical_identity_approved and canonical_promotion_allowed MUST be false.

The report lists *every* unobserved bone, unobserved articulation, untested movement family, negative source contacts requiring review and reports without qualified closed-bone surfaces. It automatically preserves the 12-region 0 READY / 9 PARTIAL / 3 BLOCKED readiness and the 11 original anatomical blockers. Even reported data with 206/206 bones, 427/427 contacts and every pose family would NOT prove the character is anatomically correct; independent anatomical identification, primary-source evidence and Blender visual/physical comparison are still needed.

This branch tests the auditor against actual current 206+427 inventory files and adversarial/synthetic bpy report fixtures in CI. No real laptop Blender evaluation is claimed and NO geometry or medical source files are uploaded to GitHub.
