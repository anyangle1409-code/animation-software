# Work anatomical evidence inspection — 2026-10-08

Continue only on `codex/whole-body-biomechanics-audit-20261007` in `anyangle1409-code/animation-software`. Fetch and read live HEAD first. Preserve all newer commits; never reset, revert, force-push or work on main. The owner authorizes autonomous inspection and verified fixes. Follow the live tracker and skeleton-first policy.

## What exists

Blender 5.2.1 LTS bpy runs in Work, without the desktop app. There is **no new complete corrected canonical skeleton yet**. a003 remains a diagnostic mesh-fit baseline. New work is source-bound target evidence and synthetic Blender checks. Do not describe old a003 or sparse fixtures as the corrected skeleton.

| Evidence | Scope | Main limitation |
|---|---|---|
| `canonical_scapula_measured_landmark_model_v1.json` | 29 measured landmarks; raw 125-subject workbook; separate male/healthy male direct stature regressions | Relative envelope only; no absolute SC/AC/GH or thorax pose |
| `canonical_clavicle_endpoint_crosscheck_v1.json` | Articular-centre chord definition distinguished from extremal chord and centreline | Exact stature-matched canonical length and SC placement remain open |
| `canonical_lumbar_superior_endplate_frames_p1.json` | Six proper upper-endplate frames from existing provisional P1 | Inferior endplates/body wedge/disc-only rotations and centres remain open |
| `rib_distal_source_mean_curves_v1.json` | 12 supported distal population-mean segments, source in-plane coordinates | Proximal branch Eq 2.18, true head/tubercle and thorax mapping remain open |
| `audit/runs/work_bpy_preflight_20261008_001/` | 22 bpy smoke checks; 58 scapular points through save/reload; full Python baseline log | Synthetic checks, not anatomical acceptance |
| `audit/runs/work_bpy_baseline_recheck_20261008_001/` | Fresh a003 135-test per-test metrics and hashes; 24 source distal-curve roundtrip | Unchanged baseline; two mirror pairs are SOLVER_TEST, not PASS |

All anatomy paths in this table are under `ORIGINAL_V1_WORK/anatomy/`. `inspection_manifest.json` binds key inputs/scripts by SHA256. Existing full baseline movement samples remain at `audit/runs/isolated_bone_only_014/`.

## Independent review priorities

1. Recompute scapular report from the raw workbook. Verify subject-ID joins, 29 XYZ points, mm/cm units and incorrect A1 sheet dimension metadata. Do not treat bilateral or repeated observations as independent people.
2. Check LM5 medial spine-border intersection versus LM14 root of spine; LM25 exterior versus LM26 interior acromial angle. Never switch landmarks to force population agreement. Verify independent anterior-rim sign and proper frame determinant.
3. Recheck 2022 scapular source: d1 is tubercle-to-tubercle rather than articular rim; d6/d7 are projected reference-line distances, not direct chords. Refine d8 semantics from the original figure before numerical use.
4. Resolve articular-centre clavicle chord versus extremal-point chord and true curved length. No averaging or same-subject ratio may be inferred from separate populations. Li 2012 PMID22340551 may provide bilateral separation, but full table/figure/endpoints are required.
5. Reinspect original 2022 lumbar Figure 5C: segmental angles are superior-to-superior, incorporating upper vertebral body wedge plus disc. Never assign the entire angle to the disc then also wedge the body. P1 is a scaled cross-cohort provisional family.
6. Independently recover rib proximal feasibility Eq 2.18. Michigan thesis handle and legacy bitstreams returned 403; the newer item URL also returned 403. Do not select a visually plausible tangent branch. Distal tests cover only Eqs 2.2–2.7. A curve reconstructed from mean parameters is not a pointwise population mean curve, and per-level means do not form one measured individual ribcage.
7. Verify carpal projected angles with `python scripts/validate_canonical_carpal_axes.py`; unit/mirror tests alone can accept all-proximal stubs. Treat the two 121-wrist reports as potentially shared cohort evidence, not independent replication.
8. Inspect freshly evaluated a003 movement metrics: 135 integrity passes, 41 mirror passes, two SOLVER_TEST exceptions. A passing command/JCS integrity test is not proof of contact geometry or complete natural motion.
9. Continue other independent Gate 6 source/coordinate tasks and Gates 8/9 followers where justified. No production mesh/weights/drivers and no Phase 10 acceptance until gates permit them.

## Reproduce checks

Run from repository root; use available Python with NumPy. Tests do not need bpy:

```bash
python -m unittest discover -s scripts -p 'test_canonical*.py'
python -m unittest discover -s scripts -p test_scapula_landmark_model.py
python -m unittest discover -s scripts -p test_rib_demographic_model.py
python -m unittest discover -s scripts -p test_rib_spiral_reconstruction.py
python scripts/validate_canonical_target_selection.py
python scripts/validate_complete_anatomical_atlas.py
python scripts/anatomy_fit/scapula_landmark_model.py --height-cm 182.00002908706665 --out /tmp/scapula_recomputed.json
python scripts/anatomy_fit/lumbar_endplate_orientations.py
python scripts/anatomy_fit/build_rib_distal_source_curves.py --out /tmp/rib_distal_recomputed.json
python scripts/anatomy_fit/build_forearm_target_report.py --out /tmp/forearm_recomputed.json
```

In this Work environment bpy Python is `/tmp/hgpt-bpy/bin/python`; on the laptop use your verified bpy interpreter or adapt to `blender --background --python SCRIPT -- ARGS`. Use fresh output paths; never overwrite an anatomical revision.

```bash
/tmp/hgpt-bpy/bin/python scripts/anatomy_fit/check_scapula_landmarks_blender.py --scratch-blend /tmp/claude_scapula_check_001.blend --out /tmp/claude_scapula_check_001.json
/tmp/hgpt-bpy/bin/python scripts/anatomy_fit/check_rib_distal_curves_blender.py --scratch-blend /tmp/claude_rib_distal_check_001.blend --out /tmp/claude_rib_distal_check_001.json
/tmp/hgpt-bpy/bin/python scripts/anatomy_fit/run_isolated_tests_blender.py --source-blend ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend --record ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json --out-blend /tmp/claude_a003_recheck_001.blend --out-dir /tmp/claude_a003_recheck_001
```

The last command saves a new baseline test file and verifies the source hash is unchanged. Fixture scripts clear only their fresh process scene and load their own synthetic outputs; they do not open a003.

## Known suite discrepancies

Latest full Python baseline before the distal additions: 685 tests, five failures and four errors in existing production/recovery fixtures. Details are retained in `audit/runs/work_bpy_preflight_20261008_001/python_suite_685_tests.txt`. Do not report the full project green or edit production controls to hide these. Skeleton-focused checks pass, and the target validator explicitly keeps `freeze_ready=false`.

## Acceptance boundary

Resolve essential numeric targets before generating the next immutable canonical revision. Then verify all 206 bones, articulation exceptions, joint-centre separation, source definitions, bilateral signs, contact mechanics and isolated movement coverage. Render the actual new skeleton in six views, with old-mesh overlays, old/new comparison and anatomical close-ups only once it exists. Keep provenance/hashes and failed evidence, update both tracker and findings, commit and push coherent verified progress frequently.

## Latest lumbar continuation

Review canonical_lumbar_wedge_evidence_v1.json, canonical_lumbar_body_disc_frames_p1.json and canonical_lumbar_ct_source_review_v1.json. Five inferior orientations are provisional only. Check posterior-positive wedge signs independently, SE/SD distinction, cross-cohort closure, CT source count inconsistency and unresolved width plane. No absolute centres or new canonical master exist. Run scripts/test_canonical_lumbar_wedge_decomposition.py and the local bpy fixture command from audit/runs/work_bpy_lumbar_orientation_20261008_001/README.md.

Independent edge-height review now in canonical_lumbar_edge_height_crosscheck_v1.json. Recheck Table 4 L1 posterior printed SD against its observed range; usable SD is deliberately null. Run scripts/test_anatomical_source_statistics.py. Do not convert supine edge-gap means into standing centre spacing.

Review latest lumbar source-separated orientation sensitivity and independent Been2007 standing body-wedge evidence. Check canonical_source_identity_review_v1.json before counting evidence: four duplicate-publication groups; clavicle Daruwalla legacy ID corrected to Bernat attribution. No final numerical anatomy is implied. New bpy report: audit/runs/work_bpy_lumbar_sensitivity_20261008_001/verification.json.

Measured glenoid rim orientation now exists in canonical_glenoid_rim_frame_v1.json. Review raw LM15–18 definitions, source-frame angle semantics, plane residual, left first-tangent reversal and explicit null GH centre. Retained isotropic-plane false-pass mutation exposed and corrected a fitter weakness. Seven tests in scripts/test_canonical_glenoid_rim_frame.py; bpy evidence in audit/runs/work_bpy_glenoid_rim_20261008_001/.

Latest contact check: canonical_endplate_clearance_sensitivity_v1.json is a synthetic planar sweep, not anatomy. Verify continuous ellipse minimum and witness; centre/cardinal gaps can falsely pass. Wang2012 cranial/caudal are DISC-relative. Shoulder invalid-input mutation failures retained in audit/runs/work_endplate_clearance_20261008_001/. Run scripts/test_canonical_endplate_clearance.py and scripts/test_shoulder_target_invalid_geometry.py.

Latest hyoid review: check primary Abdelkader2025 Table 1/Figure 1 for the corrected BB-prime minor-axis versus CC-prime AP-thickness mapping. Previously `body_AP_length=11.32` was wrong; corrected local X/Y/Z extents are 24.3/6.99/11.32 mm. Body tilt and whole-bone coordinates remain unresolved. Run scripts/test_canonical_hyoid_geometry.py; limited bpy dimension fixture and retained pre-fix failure are in audit/runs/work_hyoid_axis_review_20261008_001/. Current spec/readiness/selection descriptions were reconciled with already-existing provisional work, without promoting any gate or hyoid evidence grade.

Latest gate hardening: inspect retained pre-fix failures and synthetic freeze-fixture mutations in audit/runs/work_target_gate_mutations_20261008_001/. Missing/unknown grades and nonboolean gate flags now reject; malformed shoulder comparisons report failure. 129 focused tests pass. New full suite: 740 tests with the same five failures/four errors by name as the old 685-test checkpoint, with traces and comparison retained. Li2012 linked primary full text returns HTTP402; exact bilateral SC anchor remains unavailable. All anatomical freeze/contact dependencies remain open.

## Laptop task (owner request, 8 October): SC anchor for CP1a

On the owner's laptop (SimTK and publisher sites reachable there), obtain either:
- the MoBL-ARMS (Saul 2015; https://simtk.org/home/upexdyn) or Seth thoracoscapular (https://simtk.org/home/scapulothoracic) `.osim` files and read the sternoclavicular joint locations in the thorax frame; or
- the full text of Li 2012 (PMID 22340551), for the bilateral clavicle distance and its exact endpoints.

Record the source, endpoints, population and stature context before any CP1a use. See `docs/CLAUDE_INDEPENDENT_REVIEW_20261008.md` (SC-anchor search) for what is already excluded.
