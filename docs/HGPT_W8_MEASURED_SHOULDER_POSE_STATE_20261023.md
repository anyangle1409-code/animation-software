# Home Gym PT — actual measured W8 shoulder-press activation, 9 frames

**23 October 2026 — first native runtime shape-key/shoulder-cap movement snapshot VERIFIED.**
**Status:** READ-ONLY IN MEMORY, archived reconstruction *NOT ANATOMICALLY APPROVED*. This is measured driver state and unchanged original benchmark deformation, **not a corrected body model**.

## Provenance

- Isolated cloud branch `work/phone-blender-workbench-20261023`.
- [Six-job SUCCESS run 40034242376](https://github.com/anyangle1409-code/animation-software/actions/runs/40034242376): five existing native/analysis jobs plus new `pose-state-w8` job; all passed.
- [W8 pose-state artifact 12535648742](https://github.com/anyangle1409-code/animation-software/actions/runs/40034242376/artifacts/12535648742), independently downloaded; ZIP SHA256 **`7f919b5f5562c655a336cc437ab33cf19be4636d47e534d90061721090a06e58`** matches GitHub artifact digest. JSON: `w8_shoulder_driver_pose_state.json`.
- Input `.blend` SHA256 **`2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`** verified before/after and not saved. Old driver/movement source ref **`025d5f28fa7eba2064fba565b1c9b60119cdd2cb`** independently checked out; native rest signature unchanged. No product/application source affected.
- `scripts/phone_blender/pose_state_probe.py` instruments the **original** `bench.pose_press`, `drives.drive`, `bench.frame_metrics` and frozen rest triangulation, capturing shape-key state **AFTER** `post_pose` at all nine frames. This is not a synthetic interpolation.

## Actual requested vs measured motion

The `humerothoracic_elevation_measured_by_pinned_driver_deg` is the actual measurement method used by the frozen source: vector angle of upper-arm direction relative to thorax down-axis. It is **not** independently certified ISB GH angle. `cap_local_delta_angle_deg_not_absolute` is the shoulder-cap control bone's local quaternion angle, **not** a clinical joint angle.

| Sample | Progress | Authored HT target | L measured HT | R measured HT | L cap local delta | L active S7 corrective |
|---|---:|---:|---:|---:|---:|---|
| 0 | 0% | 90.000° | 87.680° | 87.680° | 33.100° | S7 off |
| 1 | 12.5% | 93.008° | 90.653° | 90.653° | 33.820° | S7 off |
| 2 | 25% | 100.938° | 98.491° | ~98.491° | 35.710° | S7 _110 = 0.232717 |
| 3 | 37.5% | 112.148° | 109.564° | ~109.564° | 38.413° | S7 _110 = 0.970959 |
| 4 | 50% | 125.000° | 122.232° | 122.232° | 41.486° | S7 _120 = 0.7768; _130 = 0.2232 |
| 5 | 62.5% | 137.852° | 134.839° | ~134.839° | 43.677° | S7 _130 = 0.19358; _136 = 0.80642 |
| 6 | 75% | 149.063° | 145.726° | 145.726° | 46.172° | S7 _145 = 0.934006; _156 = 0.065994 |
| 7 | 87.5% | 156.992° | 153.290° | ~153.290° | 48.510° | S7 _145 = 0.246352; _156 = 0.753648 |
| 8 | 100% | 160.000° | **156.103°** | **156.103°** | **49.430°** | **S7 _156 = 0.989697; _166 = 0.010303** |

**Critical contrast with earlier static prediction:** If actual elevation were exactly 160° the S7 activation rule predicts 60% _156 + 40% _166, but the model's current **measured ~156.103°** causes ~99% _156 + 1% _166. Thus static mathematical predictions from the *requested target* cannot substitute for measuring the actual driven pose. Whether the ~3.9° endpoint discrepancy or one specific S7 corrective causes visible armpit/cap distortion **remains unproven**; the model uses project-authored kinematics.

**Both runtime suffix sides are closely symmetric** in this measurement. The `hgpt_cap_fraction` is saved as 0.45, ramp absent and axilla helper absent, as previously verified. The *actual* cap helper local quaternion delta grows ~33.10°→49.43° during the press; that degree measurement is not synonymous with `hgpt_cap_fraction`.

## Exact existing native deformation metrics reproduced

| Sample | Stretched triangles (area >2× rest) | Collapsed triangles (area <0.1× rest) | Nonadjacent intersection pairs |
|---|---:|---:|---:|
| 0 | 1004 | 9 | 11 |
| 4 | 2546 | 116 | 337 |
| 6 | **3509** | **110** | **146** |
| 8 | 1594 | 173 | 441 |

At frame6, the **3509** stretch and **110** collapse counts reproduce the earlier saved read-only native diagnosis. Frame8 still has substantial failures; different failure categories change in different directions. No quality gate has been relaxed, and all surface/movement acceptance remains FAIL or NOT_GRANTED. Numeric counts **are within this unchanged W8 tessellation only**; they do not make a cross-topology W8/V14/R120 ranking.

## Why this matters to a correct generic human model

1. Establish actual bone/skin motion rather than calculating an educational anatomical range and assuming the rig achieves it.
2. Distinguish **pose target**, **project-measured motion**, **driver shape-key activation**, **helper bone movement**, **surface deformation**. These are different variables with different verification standards.
3. Create repeatable causal A/B test candidates: (a) neutral drivers, (b) actual S7 only, (c) original full correctives, (d) optional cap/axilla behaviour. **These are plans only; no source weight/mesh/bone/driver correction was made.** An in-memory controlled experiment would still require explicit scope and unchanged binary input.
4. Continue independent structural/clinical landmark calibration (46 unbound ISB-informed markers) and elbow silhouette/forearm rotation test; clinical population means should never be substituted for measured motion.
5. Include matched front/back/side/three-quarter photo review if an independent later experimental fix is authorized.

## Review and quality gates

- Tooling/code **PASS** (six jobs success; exact source SHA unchanged; nine frames captured).
- Actual authored-driver angle measured at every frame **PASS for evidence existence**, **NOT anatomical joint-axis certification**.
- S1/S5/S7/cap drive observed **PASS for report existence**, **NOT proof of physiologically correct muscle activation or deformation**.
- Preserved W8 source and original production unchanged **PASS**.
- Shoulder press surface stretch/collapse/collision test **FAIL**.
- Native ISB coordinate frame, axilla placement, muscle paths/attachments, foot and elbow acceptance **NOT_GRANTED**.

**Next safe item:** compare measured actual pose samples and S7 key values against shape-key **vector** displacements around the previously verified rear shoulder hot spots; do not change S7 thresholds or add an axilla helper just because current weights are large. For the owner's elbow concern, test forearm rotation and arm contour on body-local moving plane snapshots with independent landmarks, not arbitrary elbow circumference guesses.


## Exact S1–S7 mathematical comparison with measured angle

An independent offline check took `w8_shoulder_driver_pose_state.json` from the verified native-run artifact above and `shoulder_activation_rules.json` from the same run's [W8 static artifact 12535503988](https://github.com/anyangle1409-code/animation-software/actions/runs/40034242376/artifacts/12535503988) (original ZIP SHA256 `41a5f00bed46842a7b4857d35893a653695ca23d24d237234dedaadaae63a822`, independently downloaded and checked against GitHub). Using the **MEASURED** vector elevation, not the authored pose target, the exact pinned S1–S7 piecewise linear hat rules were evaluated for:
- Nine native press frames × both runtime suffix sides × 21 defined S1–S7 keys per side = **378 individual shape-key observations**.
- The maximum absolute difference between reported actual key value and an independent hat calculation was **about `0.000001`** (primarily JSON/angle decimal rounding).
- This is strong evidence that the saved S1–S7 *interpolation equation follows its measured input* consistently. **It does not prove the measured joint axes, underlying muscle shape, skin weights, helper cap or output deforming mesh are anatomically correct.**
- C1 arm/trunk-contact keys use a **different measured shoulder-extension driver** and are explicitly outside this elevation comparison.
- Versioned numeric comparator script `scripts/cloud_body_analysis/verify_pose_driver_contract.py` and regression tests were committed, with an independent seventh job `verify-actual-shoulder-driver-math` added to `.github/workflows/phone-blender-workbench.yml`. [Cloud run 40034863130](https://github.com/anyangle1409-code/animation-software/actions/runs/40034863130) was pending at documentation time, and must complete before the new CI comparator is labelled verified.

**Root-cause implication:** There is no present evidence of a basic S1–S7 linear-hat arithmetic bug. The actionable next comparison is model joint kinematics, helper cap/axilla behaviour and actual signed shape-key displacement plus skin-weight topology in the posterior scapula/shoulder hotspots. Avoid 'fixing' the 95° S7 start or 0.45 cap fraction without controlled causal evidence.


## FINAL VERIFIED: corrected seven-job shoulder driver test

- [Corrected run 40035351859](https://github.com/anyangle1409-code/animation-software/actions/runs/40035351859) completed **SUCCESS across all seven jobs**: W8/V14/R120 preservation inspections, W8 in-memory shoulder press, native pose failure localization, cross-model rest metadata and new verified shape-key/math comparator. No native model was saved or modified.
- [Driver-consistency artifact 12536234494](https://github.com/anyangle1409-code/animation-software/actions/runs/40035351859/artifacts/12536234494) ZIP independently downloaded and SHA256 checked against GitHub: `fddfd366589a6648e3cc188217dc0997f329cc851c2d8ac0ebf2f968ed33f709`. Embedded `w8_driver_math_consistency.json` inspected, result `PINNED_W8_DRIVER_MATH_REPRODUCED_ONLY_HUMAN_MOTION_NOT_APPROVED`.
- **378 actual observed shape-key values** agree with independent piecewise-linear rules using actual measured vector elevation; maximum recorded absolute difference `0.000001`. W8 has **four installed** S1/S3/S5/S7 corrective families, not all seven possible S1–S7 placeholders. S2/S4/S6 are **nominally absent** (zero source keys). C1 arm/trunk contact uses shoulder extension rather than humerothoracic elevation and was not part of the 378-key math comparison.
- Previously failed run40034863130 was a validator assumption error (it required all seven nominal families populated); fixed comparator `f18b70e8`, tests `f353309f`, **full green outcome** above. No underlying Blender source fault is established by this CI test failure.
- **Scope strictly limited:** proof of mathematical driver consistency only. The authored-to-measured angle discrepancy (~2.3°–3.9°), shoulder/axilla surface defects, muscle paths, elbow continuity and native anatomical JCS calibration remain open; original deformation acceptance is **FAIL**.
