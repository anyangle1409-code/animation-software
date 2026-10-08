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
