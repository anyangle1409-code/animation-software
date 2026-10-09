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

Review latest lumbar source-separated orientation sensitivity and independent Been2007 standing body-wedge evidence. Check canonical_source_identity_review_v1.json before counting evidence: five duplicate-publication groups (fifth found via PMCID, 8 October Claude fix); clavicle Daruwalla legacy ID corrected to Bernat attribution. No final numerical anatomy is implied. New bpy report: audit/runs/work_bpy_lumbar_sensitivity_20261008_001/verification.json.

Measured glenoid rim orientation now exists in canonical_glenoid_rim_frame_v1.json. Review raw LM15–18 definitions, source-frame angle semantics, plane residual, left first-tangent reversal and explicit null GH centre. Retained isotropic-plane false-pass mutation exposed and corrected a fitter weakness. Seven tests in scripts/test_canonical_glenoid_rim_frame.py; bpy evidence in audit/runs/work_bpy_glenoid_rim_20261008_001/.

Latest contact check: canonical_endplate_clearance_sensitivity_v1.json is a synthetic planar sweep, not anatomy. Verify continuous ellipse minimum and witness; centre/cardinal gaps can falsely pass. Wang2012 cranial/caudal are DISC-relative. Shoulder invalid-input mutation failures retained in audit/runs/work_endplate_clearance_20261008_001/. Run scripts/test_canonical_endplate_clearance.py and scripts/test_shoulder_target_invalid_geometry.py.

Latest hyoid review: check primary Abdelkader2025 Table 1/Figure 1 for the corrected BB-prime minor-axis versus CC-prime AP-thickness mapping. Previously `body_AP_length=11.32` was wrong; corrected local X/Y/Z extents are 24.3/6.99/11.32 mm. Body tilt and whole-bone coordinates remain unresolved. Run scripts/test_canonical_hyoid_geometry.py; limited bpy dimension fixture and retained pre-fix failure are in audit/runs/work_hyoid_axis_review_20261008_001/. Current spec/readiness/selection descriptions were reconciled with already-existing provisional work, without promoting any gate or hyoid evidence grade.

Latest gate hardening: inspect retained pre-fix failures and synthetic freeze-fixture mutations in audit/runs/work_target_gate_mutations_20261008_001/. Missing/unknown grades and nonboolean gate flags now reject; malformed shoulder comparisons report failure. 129 focused tests pass. New full suite: 740 tests with the same five failures/four errors by name as the old 685-test checkpoint, with traces and comparison retained. Li2012 linked primary full text returns HTTP402; exact bilateral SC anchor remains unavailable. All anatomical freeze/contact dependencies remain open.

## Laptop task (owner request, 8 October): SC anchor for CP1a

On the owner's laptop (SimTK and publisher sites reachable there), obtain either:
- the MoBL-ARMS (Saul 2015; https://simtk.org/home/upexdyn) or Seth thoracoscapular (https://simtk.org/home/scapulothoracic) `.osim` files and read the sternoclavicular joint locations in the thorax frame; or
- the full text of Li 2012 (PMID 22340551), for the bilateral clavicle distance and its exact endpoints.

Record the source, endpoints, population and stature context before any CP1a use. See `docs/CLAUDE_INDEPENDENT_REVIEW_20261008.md` (SC-anchor search) for what is already excluded.

Also on the laptop, these are population datasets for the BLOCKED regions; none is reachable from the cloud session:
- **Carpus:** the Open Source Carpal Database (Brown/Crisco; 90 subjects, 120 wrists, CT bone surfaces plus kinematics), https://simtk.org/projects/carpal-database.
- **Tarsus:** Zenodo record 3464747 (MRI-derived meshes of the talus, calcaneus, navicular, cuboid, cuneiforms and first metatarsal).
- **Ribs:** RibSeg v2 rib centrelines (660 CTs); code at github.com/M3DV/RibSeg, data linked from there.

**Source rechecks:**
- the ZHANG_2018 talus length/width definitions (PMC6057431);
- the Canovas 2004 "capitate axis" normaliser. **Resolved 8 October:** it is the capitate's first principal axis of inertia, and the review has the details.

Both are explained in the review doc's open-data section.

## Owner decision and data fixes (8 October, Claude)

**Owner decision:** the skeleton follows normal 1.82 m adult male proportions, and the mesh is refitted to it. This is recorded in the policy doc and in `owner_decisions`.

**Consequences now in readiness:**
- the forearm (EJC–WJC is −8.9% against de Leva) and femur (HJC–KJC is −6.5%) need endpoint-defined 1.82 m targets;
- a new `humerus` region (PARTIAL) is added;
- the ribs region now carries a sternum blocker.

**Data fixes (owner-approved):**
- the Zhang talus "length" is moved to `excluded_partial_measure_references_mm`;
- the C2 0.66 mm dispersion is nulled as an SD and kept as `printed_dispersion`;
- the India mandible record is quarantined;
- the Rausch ulna endpoint definition is recorded;
- the Qiu clavicle SD is marked per-bone.

No target value was selected or promoted. Please verify the C2 dispersion against the source when it is reachable.

**1.82 m limb-length proposal (Claude, for review):** see `canonical_limb_length_proposal_182_v1.json`.
- **Forearm:** robustly short (target about 283–293 mm EJC–WJC, against a003's 256 mm).
- **Thigh:** contested between methods (ANSUR 419–427 mm against de Leva 441 mm). Resolve the HJC endpoint relation first.
- **Upper arm and shank:** consistent with a003.

This corrects the earlier "thigh 6.5% short" note. The proposal does not select any target.

## Shoulder stage pickup (8 October, Claude)

- **Open on the laptop (read-only):** `ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_proposal_c001/HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_proposal_c001.blend`. This is an audit candidate, not canonical. Collection `SHOULDER_PROPOSAL_SCAPULA_LANDMARKS` holds the 29 measured scapula landmarks per side.
- **Look first:** `review/sheets/sheet_before_after_shoulder_{left,right}.jpg`.
- **Known defect to confirm by eye:** shoulder too high against ANSUR (lateral acromion +63 mm). GH/AC sit at the a003 skin top because the mesh is not refitted.
- **Verify:** `python3 scripts/test_shoulder_proposal_c001.py` (15 tests) and `audit/shoulder_vertical_relation_audit_v1.json`. The v1 single-offset hypothesis is withdrawn.
- **Next shoulder step:** find a source pairing skin acromiale/cervicale/suprasternale with bone (or get an owner decision on which vertical anchor governs) before any absolute shoulder height is chosen. The standing chest-angle disagreement remains unresolved.

## Shoulder c002 pickup (ANSUR living height; 8 October, Claude)

- **Open read-only:** `ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_proposal_c002_ansur_height/HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_proposal_c002_ansur_height.blend`. It is an audit candidate, with SC closure FAIL.
- **Look first:** `review/sheets/sheet_c001_vs_c002_shoulder_{left,right}.jpg` and the side views. The SC sits below the top of the retained sternum.
- **Verify on the laptop:** the ANSUR II acromion landmark definition (Hotzman et al. 2011, NATICK/TR-11/017, landmark section). It was unreachable from the cloud.
- **Blocked on an owner decision:** (a) lower the thorax with the girdle, (b) lower clavicle elevation on evidence, or (c) a skin-acromiale-to-bone source. Run `python3 scripts/test_shoulder_proposal_c002.py`.

### Next priority after the shoulder: spine thoracic distribution blocked on source access (8 October, Claude)

- **Sequence status:**
  - Item 1 (shoulder): blocked on the c002 owner decision.
  - Item 2 (C2–S1 stack): next unblocked by dependency. Lumbar provisional frames exist (GPT). The thoracic per-level distribution of the selected 43.7° T1–T12 kyphosis (Hasegawa male, SD 9°) is the open step.
- **Why it can't be closed from the repo:**
  - `canonical_proportion_sources_v1.json` (THORACIC_BODY_DISC_2011, PMC3171774) stores per-level *disc* anterior/posterior heights.
  - It stores only *average* body heights: no per-level anterior/posterior split and no AP depth.
  - Vertebral-body wedging carries nearly all thoracic kyphosis, and no per-level standing segmental table is committed.
  - Rule kept: do not distribute 43.7° uniformly.
- **Network:** literature hosts are denied by this cloud environment's network policy (PMC, PubMed, Crossref, Springer, Europe PMC, DTIC, archive.org, Zenodo, MDPI, PLOS).
- **Laptop acquisition list:**
  - PMC3171774: full per-level body anterior/posterior and depth table;
  - Eur Spine J 2025, doi 10.1007/s00586-025-09392-w (disc vs body contribution in healthy volunteers): Table 6 segmental alignment;
  - Eur Spine J 2021, doi 10.1007/s00586-020-06670-7 (normative thoracic sagittal curve);
  - Bernhardt & Bridwell 1989, Spine 14:717, doi 10.1097/00007632-198907000-00012 (segmental T1–S1);
  - for c002: the ANSUR II Measurer's Handbook (NATICK/TR-11/017, DTIC ADA548497), acromion landmark section.
- **Remaining sequence items** are BLOCKED or need sources/decisions: ribs (proximal equation, sternum), radius/ulna corridors (GPT-preserved blockers), carpus, tarsus, pelvis/os coxae and head envelopes. No further target can be closed defensibly from the cloud without new sources or owner decisions.

### ANSUR acromion correspondence audit: no defensible c003 (8 October, Claude)

- **Definition (primary, owner-verified):** ANSUR II Measurer's Handbook, Hotzman et al. 2011, NATICK/TR-11/017, [DTIC ADA548497](https://apps.dtic.mil/sti/tr/pdf/ADA548497.pdf), §5.2.1 and §6.4.2.
  - The acromion landmark is a **palpated bony point**: the intersection of the acromion's lateral border with the line from the trapezius point, over the clavicle point, toward the shoulder tip.
  - Acromial height is floor to that drawn right acromion point.
  - **No skin offset.** (The thorax review's "skin landmarks" label is corrected for the acromion in the audit; the hashed file is not edited.)
- **Mapping decision** (`audit/shoulder_ansur_acromion_correspondence_v1.json`, `205f787e` and later):
  - The ANSUR point is the Lee LM25–LM27 lateral-border point crossed by the trapezius–clavicle line. Two bracketing line constructions put it at **t 0.08–0.38 from LM25**, 9–13 mm below LM27 (which c002 used).
  - LM27 alone (an extremal point) and LM25 alone (the posterior border end) are brackets, not the landmark.
  - The a003/r95 skin acromion is an authored-mesh point: reported only.
  - Limitation: the trapezius/clavicle point definitions are not in the repo, so the crossing is bracketed rather than exact.
- **Feasibility** (SC closed on the retained a003 notch, sternum not lowered, height met exactly; minimum joint departure of clavicle elevation and the three scapular angles from Matsumura male standing means, as independent z):
  - **Absolute ANSUR acromial height 1497.7 mm: INFEASIBLE** for every mapping and both pitches. The clavicle would need −6.6° to −13.7° (max |z| 3.65–5.42; χ² ≥ 15.2). **No c003 created.**
  - ANSUR's own within-subject relation (acromion = suprasternale + 3.1 mm) applied to the a003 notch closes for bony pitch with the LM25 or clavicle-axis mappings: clavicle 1.6° / 1.1°, all |z| ≤ 1.72. The living pitch never closes (|z| ≥ 3.1).
  - Reported, not applied: the a003 notch sits 24.7 mm above ANSUR suprasternale (z +2.1), and that trunk/acromion inconsistency is the root of the conflict. **Owner decision needed:** the absolute acromial target vs the retained a003 sternum height.
- **Evidence** (`audit/shoulder_ansur_acromion_evidence/`): 8 labelled shoulder close-ups (both sides; front/side/rear/overhead) and 2 two-shoulder views, a required-elevation chart and a contact sheet, with a sha256 manifest.
  - The views show LM25/LM27, the crossings, both lines, the target and notch planes, and red (absolute) and green (within-subject) ghost girdles.
  - Rendered read-only on the c001 blend; c001/c002 unchanged.
- **Tests:**
  - `scripts/test_shoulder_ansur_acromion_audit.py` (9): reproduction, definition, crossings between LM25/LM27, independent crossing check, infeasibility with height actually met, no c003, within-subject reported not applied, pose consistency, c001/c002 hashes, evidence manifest.
- **Thoracic stack:** `canonical_thoracic_qualitative_constraints_v1.json` records PMID 41047402 (all bodies kyphotic; upper/middle discs kyphotic, lower lordotic; bodies 99.4% of TK) and PMID 31513104 (T7 ≈ horizontal; T1 most anterior, L1 most posterior tilt) as **qualitative sign/pattern constraints only**.
  - No per-level angles; the stack is not solved.
  - Committed cadaveric disc heights agree in sign (anterior > posterior from T7/T8 to T11/T12).
  - Tests: `scripts/test_thoracic_qualitative_constraints.py` (3).

### Phase 9 movement and follower verification on the shoulder proposal c001 (8 October, Claude)

- **Why this item:** the Phase 8–9 items still open in the tracker lack accessible sources. Verifying the existing solver and followers on the corrected girdle geometry (not only a003's) was unblocked.
- **Run 002** (`audit/runs/isolated_bone_only_c001_shoulder_proposal_002/`, README inside): **135/135 integrity PASS; 41/43 mirror PASS.** The two remaining pairs are the side-specific hip-rotation pairs, matching a003 run 014 exactly. The c001 blend is unchanged; the run input is a derived record copy (c001 itself not edited).
- **Defect found and fixed:**
  - Run 001 dropped three thumb CMC pairs from the Blender mirror comparison (38/43), because the runner required *exact* left/right command equality and c001's mirrored geometry carries about 1e-14° float noise.
  - Fix: `isolated_tests.commands_match` (relative tolerance 1e-9).
  - Regression: `scripts/test_isolated_mirror_comparability.py` (5 tests).
  - The a003 recheck (`isolated_bone_only_a003_mirror_fix_recheck_001`) is unchanged at 41/2.
- **Clips** (`…_002/clips/`): labelled a003-vs-c001 GIFs and keyframe sheets of the solver-keyed shoulder-complex scapular-plane elevation (scapulothoracic rhythm plus clavicle followers; both sides) and GH elevation, front and rear.
- **Gate 9 stays NOT PASSED:** coverage gaps (full opposition, rib–sternum coupling, midfoot) still lack sources. Phase 10 has not started.

### c003: coupled upper-thorax and shoulder reconciliation to ANSUR (8 October, Claude)

- **Decision** (`SHOULDER_THORAX_ANSUR_COUPLED_C003`, made on the user's behalf from the audit evidence): for this audit candidate, the coherent ANSUR relations govern over the inherited a003 notch. a003, c001, c002 and production stay immutable.
- **Candidate** `r95_a003_shoulder_thorax_c003_ansur_coupled` (`audit/candidates/shoulder_thorax_c003_ansur_coupled/`, README inside):
  - **Sternum:** moved rigidly z −24.67 / y +14.66 mm. The posterior part comes from the pump-handle coupling that minimises costal-cartilage deformation.
  - **Ribs:** ribs 1–7 rotate 8–19° about their heads (cartilage ≤ 4.4 mm change); ribs 8–10 follow through the interchondral joints (≤ 0.22 mm).
  - **Girdle:** solved on the new notch (bony pitch, clavicle-axis border landmark).
  - **Arms:** translated rigidly with GH.
  - **Untouched:** spine, skull, pelvis and legs (121 bones identical).
- **All 10 acceptance checks PASS:**
  - IJ 1494.5 and acromion 1497.7 exact; within-subject z 0.007; ANSUR cervicale − IJ = 80.7 (living relation);
  - SC closure exact; clavicle 1.1° (z −1.72), every |z| ≤ 1.72;
  - rib/axial continuity, unrelated bones, stature, joint closure, stick-axis collisions and mirror.
  - Also: CP2 identical to a003; round trip PASS; isolated suite 135/135 and 41/43 mirror.
- **Evidence:** 58 review JPEGs including a003/c001/c002/c003 four-way sheets (body, both shoulders and axillae, overhead, poses), plus a003-vs-c003 movement clips.
- **Tests:** `scripts/test_shoulder_thorax_c003.py` (16; geometry re-derived independently).
- **Still open** (c003 is **not canonical**):
  - sternum length and inclination (REOPEN);
  - rib geometry (BLOCKED);
  - notch-to-spine depth (unsourced; 84.4 → 69.8 mm);
  - notch one vertebral level below the supine T2–T3;
  - clavicle elevation at the low end of the source;
  - mapping bracket +4.5 mm;
  - thorax pitch sensitivity;
  - mesh refit and forearm length.

### Arm chain under the ANSUR shoulder (8 October, Claude; audit only)

- **What:** `audit/arm_chain_ansur_audit_v1.json` (script `arm_chain_ansur_audit.py`; 4 tests) compares a003, c001, c002 and c003 against ANSUR at 1.82 m, recomputed from the raw CSV: acromial height 1497.7, radiale height 1149.5, wrist (stylion) height 880.7, acromion–radiale 348.2, radiale–stylion 278.1 mm.
- **Proxies** (labelled): radiale = elbow centre − 15 mm (project convention, unsourced); stylion = radiocarpal marker.
- **c003 results:**
  - acromion exact;
  - acromion–radiale proxy 328.9 mm (z −1.82);
  - radiale height z +1.17; wrist height z +2.19;
  - forearm z −3.44, a003's and unchanged by any shoulder candidate.
- **Reading:** with the shoulder on ANSUR, the a003 arm hung from the bony GH places the elbow about 19 mm high. Causes are unresolved (a003 GH–EJC length vs bony GH depth; the unsourced 15 mm convention). No arm target was selected.
- **No collision:** the shallow GH depth below the ANSUR acromion point (26.5 mm) is due to the point lying near LM25 (the low posterolateral corner). Every acromion landmark clears the 24 mm head sphere by 17–25 mm, and the glenoid rim sits 0–6 mm outside it.
- **Next arm step** (source-blocked from the cloud): matched radial/ulnar landmarks (GPT's forearm requirements), then an endpoint-defined humerus/forearm solve on top of c003.

### Phase 9 gap closed for implementation: rib–sternum coupled inspiration (8 October, Claude)

- **Solver:** `scripts/anatomy_fit/rib_sternum_coupling.py`.
  - Ribs 1–7 take a pump-handle rotation at the 4.6° TEST AMPLITUDE (Beyer 2014, as the isolated rib tests); ribs 8–10 follow through the interchondral joints.
  - The sternum's rigid sagittal motion is solved for least costal-cartilage deformation, so no new magnitude is introduced.
- **Runs:** `audit/runs/rib_sternum_coupling_{a003,c003}_001/` (plan → Blender key and capture → compare via `rib_sternum_coupling_run.py`).
  - **Integrity PASS on both:** bone ends ≤ 5e-7 m from the solver; costovertebral drift 1.4e-7 m; mirrored displacement ≤ 2e-6 m.
  - **Sternum at peak:** rises 9.2–10.3 mm and moves anteriorly 1.7–3.5 mm (tilt −1.8°), the textbook pump handle, which emerged from the solve.
  - **Cartilage change:** 15.8 mm (sternum fixed) → 4.7–4.8 mm.
- **Clips:** a003 vs c003 thorax close-ups at true scale, front and side.
- **Fixes along the way:**
  - The run's mirror check now compares mirrored *displacements* (the a003 rest ribs carry an inherited 0.04 mm asymmetry).
  - The clip tools gained optional framing and caption arguments (defaults unchanged).
- **Tests:** `scripts/test_rib_sternum_coupling.py` (6).
- **Gate 9 stays NOT PASSED:**
  - not modelled: bucket-handle and long-axis components, cartilage elasticity, the shoulder's response to breathing, per-level amplitudes;
  - still untested: full opposition and the midfoot.

## Remaining queue after c003, arm-chain and rib–sternum work (8 October, Claude)

Every item below needs a source (literature hosts are denied from the cloud) or a decision. Nothing in it can be closed defensibly from the repository alone.

| Item | Needs | Where recorded |
|---|---|---|
| Thoracic per-level kyphosis | Per-level tables: PMC3171774 body anterior/posterior heights and depths; PMID 41047402 Table 6; Bernhardt & Bridwell 1989 | spine blockers; `canonical_thoracic_qualitative_constraints_v1.json` |
| Ribs (proximal curves, true geometry) | Holcombe Eq 2.18 convention; 3D rib head/tubercle/anterior coordinates | ribs blockers |
| Sternum length and inclination | Selthofer 2006 full text; stature-matched sternum source | sternum review (REOPEN) |
| Radius/ulna/wrist | Matched radial/ulnar articular and surface landmarks (`canonical_forearm_landmark_requirements_v1.json`) | forearm blockers |
| Elbow height under the ANSUR shoulder | Humerus endpoint geometry, or a sourced radiale–EJC offset (arm-chain audit: acromion–radiale z −1.82 on c003) | humerus blockers |
| Carpus, hand M2–M4 | Carpal centroids in one wrist frame | carpus/hand blockers |
| Femur HJC–KJC | Decision or source on the HJC–trochanterion relation | lower-limb blockers |
| Pelvis os coxae, SI, pubis | Landmark-rich os coxae source | pelvis blockers |
| Head and face envelopes | Cranial/facial/mandible landmark sources | head blockers |
| Gate 9 gaps | Full-opposition pronation magnitude; midfoot (TMT, naviculocuneiform, calcaneocuboid) values | Phase 9 |
| Phase 10 | Gates 6 and 9 first; authored exercise definitions | Phase 10 |
| Shoulder before canonical | Sternum REOPEN, ribs BLOCKED, notch-to-spine depth source, standing vs supine notch level, mapping bracket (+4.5 mm), pitch sensitivity | shoulder blockers; c003 README |

**Laptop first steps:**
1. Open the c003 blend read-only and review `review/sheets/sheet_four_way_*.jpg` and the clips.
2. Fetch the sources in the table.
3. Verify the remaining ANSUR II landmark definitions (radiale, stylion, suprasternale, cervicale) in the handbook, as was done for the acromion.

### ANSUR endpoint correspondence (arm chain) and review-pack index (9 October, Claude)

- **Primary handbook not retrievable:** Hotzman et al. 2011, NATICK/TR-11/017, https://apps.dtic.mil/sti/tr/pdf/ADA548497.pdf. Four routes were tried (DTIC ×2, archive.org, Wayback); all were denied by the cloud network policy, so no PDF hash exists.
- **Definitions** for §5.2.5 cervicale, §5.2.33 radiale, §5.2.36 stylion, §5.2.39 suprasternale and §6.4.68 radiale–stylion are recorded as **owner-supplied, not independently verified**, with the URL and the retrieval attempts.
- **Audit** (`audit/ansur_endpoint_correspondence_v1.json`, `ansur_endpoint_correspondence_audit.py`; 5 tests):

| Landmark | Class | Reason |
|---|---|---|
| Suprasternale | **DEFENSIBLE** | Bony notch point; height only |
| Acromion | **BRACKETED** | Line construction bracketed |
| Cervicale | **UNRESOLVED** | No C7 spinous landmark in the model |
| Radiale | **UNRESOLVED** | Model point is the humeroradial articular centre, not the lateral radial-head rim |
| Stylion | **UNRESOLVED** | The a003 radius "styloid" tail sits exactly at the radiocarpal wrist-centre height |
| Radiale–stylion length | **UNRESOLVED** | Both endpoints unresolved; EJC/WJC substitutes are not used as the measurement |

- **Robust across a 0–15 mm exploratory offset bracket** (not a sourced range): on c003 the wrist is high (z ≥ +1.49) and the upper-arm drop is short (z ≤ −1.82).
- **Correction:** the earlier arm-chain "forearm z −3.44" depended on the unsourced 15 mm convention. Across the bracket it ranges from −3.44 to −0.66, so it is withdrawn as a standalone finding. GPT's separate direct radius report uses a different proxy and is not affected.
- **Decision:** no humerus/forearm target selected; c003 unchanged.
- **Review pack:** `audit/REVIEW_PACK_INDEX.md` and `review_pack_index_v1.json` (`build_review_pack_index.py`; 3 tests).
  - 258 files across 7 evidence sets: c001, c002, c003, the acromion audit and three movement-clip sets.
  - Every sha256 is re-verified (0 failures).
  - Required coverage is all present: full body 56, left shoulder 35, right shoulder 35, axilla 16, overhead 28, comparisons 123, poses 33, clips 14.
  - Includes GitHub links and a "Start here" list.

### Dynamic collision scan over the isolated movement runs (9 October, Claude; mechanical, no new numbers)

- **What:** `scripts/anatomy_fit/movement_collision_scan.py` rebuilds every bone axis at every frame of the committed Phase 9 samples (each bone takes the recorded world delta of its nearest commanded ancestor) for **a003 run 014** and **c003 run 001**, 135 tests each.
- **Criterion:** central axes closer than 1 mm count as interpenetration. This is a conservative mechanical bound (every adult bone's radius far exceeds 0.5 mm), not an anatomical tolerance. Parent/child pairs and pairs already in contact at rest are excluded.
- **Result (identical on a003 and c003):** the only new crossings are **tibia_left × tibia_right** in `hip_abduction_adduction_left/right`.
  - The adduction sweep is an unsourced TEST AMPLITUDE of 20°.
  - The moving tibia's axis reaches 0.57 mm of the other tibia's at **13.45°** and stays within 1 mm to 20° and back (13 frames). The whole leg swings through the stance leg.
  - Real bone contact begins earlier, by an unquantified margin.
- **Reading:** a test-design defect inherited from the suite (adduction is measured clinically with the other limb moved aside), not a skeleton defect. The test is not changed here: any clearance pose or amplitude would need a source or decision.
- **Information only (above the bound):** fibulae 1.16 mm (same tests); hallux vs the opposite first metatarsal 1.4–1.7 mm (hip rotation); on c003 only, the thumb against the femur at 1.49 mm (forearm rotation at elbow 0°).
- **Evidence:**
  - `audit/movement_collision_scan/{a003_isolated_014,c003_isolated_001}.json`;
  - front clip and keyframes (a003 vs c003) in `audit/movement_collision_scan/clips/`, added to `REVIEW_PACK_INDEX.md`;
  - tests: `scripts/test_movement_collision_scan.py` (3).
- **Gate 9:** stays NOT PASSED. The hip adduction test needs a contralateral-clearance design (source or decision) before it can count as anatomical evidence.

### Joint attachment (closure) invariant over all isolated sweeps (9 October, Claude; mechanical, no new numbers)

- **What:** `scripts/anatomy_fit/joint_attachment_scan.py` checks every articulation in the project inventory that has two participant bones (368) across every sampled frame of all 135 isolated tests, on a003 run 014 and c003 run 001.
  - Each participant carries its own copy of the rest joint centre, moved by its nearest commanded ancestor's world delta. The opening is the largest distance between the copies.
  - Openings under 1e-6 m count as zero; larger ones are reported, not tolerance-graded. The runner had no attachment check.
- **Centre-preserving joints** (ball-and-socket, hinge, pivot; the TMJ excluded because it translates by design): only talocalcaneonavicular 1.98 mm, proximal radioulnar 1.93 mm and talocrural 0.73 mm open, identically on both. These are consistent with markers lying slightly off the rotation axis (for a pivot, the marker may be the sliding contact point). Shoulder SC, AC and GH stay closed through the scapulothoracic-rhythm tests.
- **Defect found (shared by a003 and c003; not fixed): midfoot column split.**
  - The follower tree has a lateral column (talus → calcaneus → cuboid → metatarsals 4–5) and a medial column (talus → navicular → cuneiforms → metatarsals 1–3).
  - `subtalar_inversion_eversion` commands only the calcaneus, so the columns separate at every bridging joint: lateral cuneiform–cuboid 36.6 mm, tarsometatarsal 4 36.8 mm, intermetatarsal 3–4 37.0 mm, cuboid–navicular 15.9 mm. The talonavicular sweep does the same at about 5 mm.
  - This quantifies the tracker's existing "midfoot untested / no defensible values" gap. A fix needs a sourced transverse-tarsal and midfoot coupling.
- **Sliding joints** (plane, glide, syndesmosis, tracking, the TMJ): their openings measure sliding, not dislocation (facets ≤ 4.6 mm; interosseous membrane 17.7 mm; patellar tracking 29.6 mm). Listed, not graded.
- **Only candidate-specific difference:** the scapulothoracic glide point (190.6 mm on a003 → 89.8 mm on c003), a functional sliding point that follows c003's smaller scapula.
- **Evidence:** `audit/joint_attachment_scan/{a003_isolated_014,c003_isolated_001}.json`; foot close-up clips (front and side, a003 vs c003) in `audit/joint_attachment_scan/clips/`, indexed in `REVIEW_PACK_INDEX.md`.
- **Tests:** `scripts/test_joint_attachment_scan.py` (5).
- **Gate 9:** stays NOT PASSED; the midfoot coupling is source-blocked.

### Reference-frame continuity over all isolated sweeps (9 October, Claude; mechanical): CLEAN on a003 and c003

- **What:** `scripts/anatomy_fit/frame_continuity_scan.py` covers all 135 sweeps (9,575 frames) of a003 run 014 and c003 run 001. It checks:
  - contiguous frames, a constant time step and finite values;
  - every recorded world delta is a proper rigid transform (float32 bound 1e-5; a negative determinant would be a sign flip);
  - each bone's rotation between consecutive frames stays within the summed change of the commanded angular channels (small-angle-accurate `atan2` angle);
  - no measured-angle jump over 90° per frame (plane of elevation excluded below 1° elevation);
  - identity deltas at both ends.
- **Result: no issues on either model.**
  - Worst orthonormality 2.1e-6 and worst |det − 1| 1.1e-6 (float32); worst rotation-step excess 3.6e-5°; largest measured jump 14°/frame; rest error 0.
  - The only a003/c003 difference is trivial (largest jump 14.05° vs 13.91°).
- **Correction in the method:** a first pass flagged 1,211 "issues", which were artefacts of `acos` at small angles and a float64 bound applied to float32 matrices. Both were fixed before recording, and the reasoning is in the script.
- **Tests:** `scripts/test_frame_continuity_scan.py` (8). Six mutation tests inject a reflection, a NaN, a frame gap, a 30° rotation jump, a non-rest end state and a 360° wrap, and each must be detected.

### State restoration of the isolated runner, including failure paths (9 October, Claude): CLEAN on a003 and c003

- **What:** `scripts/anatomy_fit/state_restoration_audit_blender.py` drives the unmodified `run_isolated_tests_blender.py` in Blender under four scenarios:
  - normal completion;
  - a RuntimeError injected at the 200th measurement (mid-sweep, frame 208);
  - a KeyboardInterrupt at the same point;
  - a RuntimeError during authoring.
- **Captured each time:** source sha256 before and after; which outputs exist; the live frame and subframe; and full state snapshots (frame, subframe, active object, selection, mode, frame range, fps, armature pose bases, every constraint and driver) of the re-opened source and the saved test blend.
- **Results (identical on both models):**
  - The source file and its re-opened state are unchanged in every scenario.
  - The session frame is restored to 1/0.0 after both failures and the interrupt.
  - Failed or interrupted runs write no report or samples, so there is no partial evidence; an authoring failure saves nothing.
  - On normal completion the report's `frame_restored` is true and its test-blend hashes match the file.
  - The saved test blend differs from the source only in the keyed action and the frame range. Constraints, drivers, active object, selection, mode, frame and pose bases at frame 1 are identical (pose bases checked to 2.2e-16).
- **Recorded behaviour, not a defect:** a failed or interrupted measurement leaves the authored, unmeasured test blend at the output path, with no report. The runner refuses to reuse output paths, so it cannot be mistaken for a pass.
- **Method fix:** the first snapshot digest hashed rounded strings, where −0.0 and 0.0 differ; it now normalises them.
- **Evidence:** `audit/state_restoration_audit/{a003,c003}.json`; `scripts/test_state_restoration_audit.py` (1 test over both results).

### Mirror parity of every moved bone, including followers and carried descendants (9 October, Claude): CLEAN on a003 and c003

- **What:** `scripts/anatomy_fit/mirror_parity_scan.py`. The isolated runner's mirror check covers commanded bones only; this one, for every bilateral test pair with matching commands and at every frame, compares:
  - every moved bone's world transform, reflected;
  - mirrored rest-to-frame displacements of both bone ends;
  - the displaced joint-centre copies of all 153 sided articulations;
  - left vs right joint openings.
- **Result:** 41 pairs compared; the 2 hip-rotation pairs are skipped as side-specific by source.
  - **Transforms mirror exactly** (worst 1.3e-6, float32); **openings match** (worst 1.9e-7 m); **0 failures**.
  - 10 lower-limb pairs show mirrored-displacement differences of ≤ 0.71 mm (joint centres ≤ 0.53 mm). These are classified **REST_ASYMMETRY_ONLY**: the transforms mirror exactly and every mismatch lies within 2 × the bone's inherited rest asymmetry (the most a rotation can amplify an offset); unexplained remainder 0.
  - The rest asymmetry is an a003 mesh-fit inheritance confined to toe phalanges (≤ 0.38 mm) and ribs (≤ 0.04 mm). The worst bone is the distal phalanx of the big toe (the 5th toe in the subtalar test).
  - a003 and c003 are identical apart from float noise.
- **Tests:** `scripts/test_mirror_parity_scan.py` (4). Mutations inject a 0.5° asymmetry into the patella follower and a 0.2° asymmetry into a commanded elbow bone; both must FAIL and not be excused as rest asymmetry.
