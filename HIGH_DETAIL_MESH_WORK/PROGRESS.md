# Candidate progress

2026-09-22. User authorised this Windows workspace as the equivalent of the Linux path.

Source branch chatgpt/absolute-retarget-imports, pinned snapshot f9cca7c34880a2c5e30b63a42c762d7fd99205e8 (archive, not a production checkout). Playbook and handoff reviewed, including historical rejected rig experiments; current mesh-only instruction takes precedence. All 63 manifest entries pass byte-size and SHA-256 verification. Blender 5.2.1 LTS launches.

Frozen references are under reference/anyangle1409-code-animation-software-f9cca7c/HOME_GYM_PT_GPT_MESH_HANDOFF/characters. Bare: 2303476 bytes, b08844339fb66e54a290eb9687fdc48296d087e4cbbb83981041a03d8501cc7a. Dressed: 2417316 bytes, fe30c1dadb1dca442b79155cf3bb662e7b22b4f6f48ee806258fde798e34a71b. Original v8 production binaries are not supplied; the playbook designates CORNER_FINAL as the frozen mesh reference.

## Pipeline

1. Reproduce sagittal measurements with copied, unchanged production source and supplied harness.
2. Model candidate shoulder surface using posed-space measurements mapped back through the unchanged skin transforms. Preserve hand geometry/topology/weights and all rig data.
3. Refine body surface with candidate-only topology, preserving UVs and accepted rig/grip metadata. Aim for 50–100k body triangles without claiming subdivision alone constitutes new anatomy.
4. Save editable Blender checkpoints and separate GLB. Verify raw node matrices, hierarchy, inverse binds, animation data and metadata against frozen source.
5. Run five exercise comparisons with current correctives and equipment transforms. Save matched renders and measurements. Report inherited regressions separately.

No production source, bundled.ts, frozen reference, exercise or rig edit is authorised or planned. No merge/promotion.

Reference-board photograph is not included; use the supplied diagnosis images and explicit numeric targets for this first review candidate, not an identity reconstruction. Candidate validation source is a disposable copy under validation; reference hashes are recorded for final integrity checks.

## Modelling and validation milestones
- Reproduced supplied sagittal baseline exactly: joint (214.9, 1412.1, -21.9) mm; deltoid apex 7.8 mm above, z +4.8 mm.
- Initial curved subdivision introduced a 3.7 mm runtime root offset via foot contacts. Rejected; feet and hands now preserve original topology. Source has two influence sets: originals retain both byte-for-byte; new vertices use the runtime's four-influence convention. Reported weight truncation is limited to new vertices.
- 59,128-triangle candidate at gain 0.75 reached 30.1–30.2 mm above, apex z -66.1. All original hand vertices, 160 bone matrices and equipment matrices matched baseline exactly at Bottom/Mid/Peak/Return across five exercises. Loops close. This numeric pass did not constitute visual acceptance.
- Visual inspection exposed ridges at shoulder ownership boundaries and interpolation cross-terms in new skinning vertices. Corrected midpoint rest placement through inverse runtime skin transforms; local anatomical smoothing now blends across ownership boundaries. Checkpoints retained before each change.
- Full unchanged code suite run: 290 passed / 8 failed / 1 skipped, exactly the handoff count. Run used one worker and 30-second test timeout to avoid machine-load timeouts; no assertions changed. Dependencies installed in candidate validation copy using package ranges (versions recorded in validation/pnpm-lock.yaml).
- Playbook's historical 22 unreachable push-up targets are 16 in the current validateClip report; full suite still has the same eight failures. No exercise mechanics retuned.

## First review candidate saved
- Final gain 0.90 and shoulder smoothing: 31.9 mm height, apex z -69.5 mm, joint unchanged.
- Five exercise render sets and overview inspected; shoulder transition improved. This is a review milestone, not production readiness.
- Final integrity: 400 reference files unchanged; copied source unchanged; raw rig/metadata and original binary preserved. Both deliverables saved and hashed in reports/final_integrity.json.
- Scope and remaining anatomy/topology/texture limitations recorded in REVIEW.md. No production files modified.

## V2 investigation
Claude independent review supplied by user: runnable guards passed; bare equivalence pending. Correspondence check on original vertices confirms real cap reshaping: mean z -32.315 mm in fixed baseline cap selection; upper shaft -8.458 mm, lower shaft +0.067 mm. Do not attribute the entire band change to vertex density. V2 trial reduces rearward sculpt coefficient from 0.040 to 0.012 m, with rig and height uplift unchanged. V1 preserved.

V2 review milestone: cap original-vertex mean backward motion reduced 32.315 to 10.727 mm. Height 31.9 mm; apex -47.8 mm. Bare variant created; six focused tests clean, 26 samples per exercise. V1/reference/production unchanged; see REVIEW_V2.md and final_integrity_v2.json.

## V3 candidate checkpoint
Weight audit showed v2's 20.82% maximum discarded influence occurs at neck/jaw midpoints; shoulder maximum is 3.87%. A 5% ceiling was verified red on v2, then the v3 builder skipped only the unsafe midpoint edges. V3 has 57,721 triangles and maximum new-vertex loss 4.98%. Shoulder sculpt and original vertices/weights are unchanged. Six focused tests passed cleanly over 26 frames per exercise; bare/dressed, grip, clearance and sagittal checks pass. Integrity report confirms 400 source files and all v2 deliverables unchanged, zero degenerate body triangles and no edges shared by more than two faces. Overhead armpit fold is visible in the frozen reference too; no speculative corrective added. See REVIEW_V3.md.

