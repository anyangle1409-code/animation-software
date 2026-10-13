# W1/W2: reference-constrained shoulder/thorax guide correction and original-mesh deformation — provisional

- **Branch:** `claude/functional-original-shoulder-correction-20261013`.
- **Base:** stacked on the reviewed PR110 head `26bf25f04158c9fa372a6e96399f744d8564837b`, whose exact-head CI `native-coupled-motion` passed.
- **Preserved:** PR110's coupled 0/90/160 runtime motion, absolute humeral shaft direction, F-SIDE-001, and the reviewed bilateral clavicle semantics (posterior rotation = local shaft +Y; elevation = same-sign local +X; retraction = opposite-sign local Z). A native test proves the clavicle/scapula pose matrices are bit-identical to PR110.
- **Untouched:**
  - the 206-bone source, which stays at rest and does not drive the 17,946-vertex male;
  - the source blend (SHA-256 `670a37bf…cbbe56`), every medical/source byte, Lane G code and GLBs, and Claude's C3 foot candidate.

**Scope:** provisional diagnostic only. There is **no anatomy, motion, deformation, GLB, clinical or production approval**.

## 1. Independent comparison with qualified references (before correction)

The current PR109/PR110 guides were measured on the native original scene.

| Element | Reference | Current guide | Finding |
|---|---|---|---|
| Scapula size | Lee 2024 raw 3-D landmarks, 45 males, direct stature regression at 182 cm (`canonical_scapula_measured_landmark_model_v1.json`): superior→inferior angle 167.1 ± 10.8 mm, exterior acromion→inferior angle 182.5 ± 10.0 mm, medial spine→glenoid 111.4 ± 3.9 mm | 231.6 / 253.2 / 154.3 mm | **Oversized ×1.389 (+6 SD).** The cause is the similarity fit of the Lee-sized c004 outline (record: 166.7 mm) onto the a003 `anat_scapula` control stick, which is 39% longer than the record's glenoid→inferior-angle segment. |
| Rib shape | Holcombe 2017 population-mean in-plane shape (Xpk, Ypk, φ_pia, Bd) per level; Holcombe 2016 distal log-spiral (exact, already implemented) | Straight a003 chord plus an X-only sin² bow of 90–150 mm | **Coil-like.** Ribs 6–12 have 82–122 of 430 tube vertices **outside the original skin** at rest. |
| Rib span | Holcombe Sx population mean ± SD | a003 chords | Ribs 2–6 are 13–34 mm longer than the mean (up to +2.5 SD); ribs 7–10 are within 1 SD. Rib 11's chord (102.5 mm against 154 mm) and its posterior-pointing anterior end look like a003 skeleton issues. **Recorded only; frozen endpoints are kept.** |
| Clavicle motion | Ludewig et al. 2009 (PMID 19181982) directions; ≤ 31° posterior rotation at 120° | PR110 (reviewed) | Unchanged; the non-exceedance test still passes. |
| Humeral contribution | Ludewig 2009 reports increasing humeral external rotation with elevation (direction only) | No axial channel; the shortest-arc swing sets the twist implicitly | Missing anatomical-frame axial rotation. |

## 2. Corrections (authored guides on frozen anchors)

All corrections live in `scripts/anatomy_fit/functional_shoulder_correction.py` (pure) and `scripts/build_functional_shoulder_correction_blender.py`.

**Ribs.** The frozen a003 head/tail are kept.
- The distal segment is the exact Holcombe 2016 spiral using the level's Holcombe 2017 Xpk/Ypk/Bd.
- The proximal segment is an **authored C1 cubic bridge**, constrained only by the published φ_pia start angle and the published peak. Holcombe's own proximal branch selection remains blocked (`rib_inplane_derivation_holcombe2016_v1.json`) and is not used.
- The plane orientation is authored as the chord plus the outward lateral direction. The Holcombe pump-handle/lateral-swing/bucket-handle convention is **not mapped**.
- **Result:** 0 of 24 rib guides are outside the skin at rest (previously 7 levels per side).

**Scapula.**
- It is now a rigid fit at scale 1. The c004 Lee-consistent landmarks keep their size, and their glenoid end sits exactly on the a003 scapula head.
- The fitted outline is rotated about the glenoid (bounded grid, ±25°), so the medial-border landmarks (LM3–LM7) sit at an **authored 12 mm** clearance outside the rib guides. Result: yaw 13° and tilt −6°, mirrored; clearance went from 17–40 mm before to 9.0–13.6 mm after, RMS 2.0 mm.
- All ten Lee distances are now within 0.7 mm of the 182 cm predictions; for example, superior→inferior is 166.7 mm (prediction 167.1).
- The outline stays the coarse 13-landmark PR109 fan, and there is no contact solver.

**Humeral axial rotation.**
- **Frame:** the angle about the humeral shaft, from the side-specific elevation-plane normal to the elbow-flexion (epicondylar proxy) axis. The runtime upper-arm local X is the mediolateral elbow axis at rest.
- **Rest values:** −130° (left) and +130° (right), which are mirrored.
- **Profile:** an authored external rotation, smoothstep 0→35° over 0–160°. The direction follows the reported healthy pattern; the magnitude is a **hypothesis, not a cohort fit**.
- **Realized:** exactly the target (the native test holds it to 1e-4°). The shaft direction still equals PR110's absolute target (1e-5).

## 3. Original-mesh shoulder/axilla deformation (0 / 90 / 160 deg)

- **Region:** 7,406 faces with weight > 0.05 in the upper-arm, clavicle or scapula groups.
- **Reference:** the evaluated rest at 0°.
- **Volume:** the exact closed-mesh signed volume. The mesh is manifold with no boundary, and only the shoulders and arms move.
- **Self-intersection:** BVH triangle overlap pairs that share no vertex.
- **Thresholds:** the same engineering thresholds as Work's PR106/PR107: an area ratio < 0.1 counts as collapse, > 2 as stretch.

| Pose | Collapse < 0.1 | Compressed < 0.5 | Stretched > 2 | Min / max area ratio | Body volume Δ | Self-intersecting pairs (faces) |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 1 / 1 | 0 % | 0 |
| 90, this branch | 0 | 98 | 310 | 0.188 / 3.54 | **+1.82 %** | 0 |
| 90, PR110 pose | 0 | 98 | 312 | 0.188 / 3.54 | +1.78 % | 0 |
| 160, this branch | **42** | 600 | 400 | 0.031 / 5.06 | **−5.01 %** | **444 (344)** |
| 160, PR110 pose | 46 | 618 | 468 | 0.014 / 4.99 | −2.95 % | 314 (280) |
| 160, with the existing corrective keys (diagnostic) | 38 | 574 | 490 | 0.013 / — | −6.20 % | 764 (488) |

**Location at 160° (dominant skin-weight group).**
- Collapse: upper arm 14, scapula 5 and clavicle 2 faces per side.
- Self-intersection: upper arm 121, clavicle 26 and scapula 25 faces per side; that is the deltoid/axilla.

**Skin crossing the guides.** In posed skin the static thorax guides come out through the chest and axilla skin:
- **90°:** ribs 2–3, 15–18 vertices per side.
- **160°:** ribs 2–5, 10–97 per side; ribs 11–12 (flank), about 50 per side; and the scapular glenoid/acromion wedge, 25 per side.

This is chest-wall and flank skin collapsing inward, not rib motion.

**Attribution.**
- The authored axial channel reduces collapse and stretch at 160° against the PR110 pose.
- It increases volume loss (−5.0% against −2.9%) and upper-arm self-intersection (121 against 97 faces per side).
- The legacy `HGPT_SHOULDER_CORR/SCAP` shape keys are present but undriven. Activated by their recorded r93/r95 formulas, they make the coupled pose **worse** (764 self-intersecting pairs at 160°, and new collapse at 90°). They were solved for a different pose model and must not be reused as they are.

**Visible defects** (nine changed-geometry shoulder views: front/side/rear at 0/90/160):
- sharp pinch folds at both shoulder caps at 160°;
- a vertical rear crease medial to each blade;
- the glenoid/acromion part of the blade outline pokes through the lateral shoulder at 160°;
- from the side, ribs read as straight slanted lines because the plane has no bucket-handle tilt;
- the blade outline is still coarse.

## 4. Exact next corrective actions

1. **Deformation:** solve new chest/deltoid/axilla correctives or a weight refit **against this coupled 0/90/160 motion**. Retire the undriven legacy keys for this motion. Targets at 160°: no faces < 0.1, self-intersection in the upper-arm/clavicle zones driven to 0, body volume change within ±2%, and no thorax guide outside the skin.
2. **Ribs:** map the Holcombe 2017 PH/LS/BH orientation convention from the primary text before adding plane tilt. Resolve the proximal branch only from verified notation.
3. **Scapula:** densify the outline from the full 29-landmark Lee set, and add a contact-aware glenoid/acromion envelope.
4. **Humerus:** replace the authored 35° ceiling only with an endpoint-compatible measured trajectory.

## Evidence and tests

- **Tests:** 13 new pure tests and 8 new native Blender 5.2.1 tests pass, and PR110's 6 native tests pass unchanged. The pure plus inherited suite (56 tests, including the rib-spiral and demographic suites) passes.
- **Private local evidence:** nine 900 px PNGs plus a manifest (0/90/160, all changed geometry; PR110/PR109/PR80/PR68 views were not rerendered). Manifest SHA-256 `f79e87286a49b4e068b62d9a2cd60c8ea17228af7f1182ff0cad267cd847a7e2`. Pinned inputs:

  | Input | SHA-256 |
  |---|---|
  | Source blend | `670a37bf…cbbe56` |
  | c004 record | `99500d94…96c1` |
  | Holcombe model | `9c10067f…1b2a` |
  | Lee model | `aa574f68…ec23` |

- **CI:** produces the same nine PNGs and manifest as an artifact. PR68's 20 views, six-control map, seven samples and GLB limitations are untouched.
