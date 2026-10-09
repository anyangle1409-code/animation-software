# COMPLETE HUMAN SKELETON — LIVE BUILD TRACKER
Project: Home Gym PT / HomeGymPT_Male_ORIGINAL_v1
Branch: codex/whole-body-biomechanics-audit-20261007
Started: 2026-10-07

## Status key
- ✅ COMPLETE — finished and checked
- 🟡 IN PROGRESS — actively being worked
- ⬜ NOT STARTED — not yet begun
- ⛔ BLOCKED — cannot complete until a dependency is available
- 🔁 REOPEN — previously accepted work that must be revalidated

## MASTER GOAL
Create a complete adult-human anatomical reference skeleton, account for every conventional bone and articulation, define sourced movement mechanics for the whole body, validate the complete skeleton in Blender, then derive an efficient runtime rig for the app.

---

## PHASE 0 — SAFETY / PROJECT ISOLATION
- [x] ✅ Create isolated whole-body biomechanics audit branch.
- [x] ✅ Preserve current production/recovery candidate; no destructive edits.
- [x] ✅ Reopen old skeleton “LOCKED” assumptions under stricter biomechanics standard.
- [x] ✅ Write complete anatomical skeleton build plan.
- [x] ✅ Write whole-body movement-atlas specification.
- [x] ✅ Add static whole-body pre-Blender audit.
- [x] ✅ Add dedicated shoulder-complex audit and multi-source verification.
Gate 0: ✅ PASSED

## PHASE 1 — COMPLETE ADULT BONE INVENTORY
- [x] ✅ Create machine-readable conventional adult bone inventory.
- [x] ✅ Verify total conventional count = 206 (206 unique IDs; 80 axial + 126 appendicular).
- [x] ✅ Classify every bone: axial/appendicular, region, side, paired/unpaired.
- [x] ✅ Mark fused adult structures explicitly (e.g. sacrum, coccyx, hip bones).
- [x] ✅ Add anatomical aliases needed by Blender/code; all 206 now have stable `anat_<id>` names plus explicit current-rig mappings.
- [x] ✅ Check unique IDs and left/right pairing: 206 unique IDs, zero duplicates, zero pairing failures; regional totals match the conventional 206 breakdown.
Gate 1: ✅ PASSED — 206 entries, 206 unique IDs, 80 axial + 126 appendicular, no duplicate IDs or left/right pairing failures.

## PHASE 2 — COMPLETE ARTICULATION / JOINT INVENTORY
- [x] ✅ Map every mechanically relevant articulation between the bones.
- [x] ✅ Classify joint type: synovial/fibrous/cartilaginous/functional.
- [x] ✅ Mark joints with effectively zero adult exercise-motion DOF.
- [x] ✅ Mark joints requiring active/follower mechanics.
- [x] ✅ Explicitly cover skull/TMJ, spine, ribs, SI, shoulder, elbow, forearm, wrist, hand, hip, knee, tib-fib, ankle, foot and toes.
- [x] ✅ Check for zero unclassified articulations.
Gate 2: ✅ PASSED — 427 named articulation/contact complexes, 24 classified families; all 206 bones accounted for (hyoid explicitly has no osseous articulation). See `ORIGINAL_V1_WORK/anatomy/gate2_verification.json` and `docs/ANATOMICAL_ATLAS_EVIDENCE_AND_LIMITATIONS_20261007.md`. Inventory acceptance only; no joint motion is locked.

## PHASE 3 — ANATOMICAL LANDMARK / JOINT-FRAME ATLAS
- [x] ✅ Define landmarks for skull/cervical spine.
- [x] ✅ Define thoracic/lumbar/sacral and rib-cage landmarks.
- [x] ✅ Define SC/AC/scapula/GH landmarks.
- [x] ✅ Define elbow/radius/ulna/wrist landmarks.
- [x] ✅ Define hand/thumb/finger landmarks.
- [x] ✅ Define pelvis/hip landmarks.
- [x] ✅ Define femoral condyle/patella/tibial landmarks.
- [x] ✅ Define malleoli/talus/calcaneus/forefoot/toe landmarks.
- [x] ✅ Adopt consistent joint coordinate conventions.
Gate 3: ✅ PASSED — 30 sourced semantic frame definitions, 206 bone-frame assignments, 427 joint-frame assignments. Numerical character fitting remains Phase 6. Frame mathematics and degeneracy tests pass; current-rig anatomical axis adapter is explicitly deferred until character orientation is measured.

## PHASE 4 — WHOLE-BODY MOVEMENT / ROM EVIDENCE ATLAS
For every moving articulation record: axes, DOF, active/passive ROM, coupling, translations, posture/load dependence, movement-plane dependence, source, confidence.
- [x] ✅ TMJ / skull.
- [x] ✅ C0-C1 / C1-C2 / C2-C7 cervical spine.
- [x] ✅ Thoracic spine.
- [x] ✅ Lumbar spine.
- [x] ✅ Sacroiliac / pelvis.
- [x] ✅ Shoulder complex: SC / AC / scapulothoracic / GH.
- [x] ✅ Elbow.
- [x] ✅ Proximal + distal radioulnar / forearm.
- [x] ✅ Wrist / carpal functional stages.
- [x] ✅ Thumb.
- [x] ✅ Fingers / metacarpals.
- [x] ✅ Hip including rotation at different flexion angles.
- [x] ✅ Knee including translation / screw-home.
- [x] ✅ Patellofemoral tracking.
- [x] ✅ Tibiofibular mechanics.
- [x] ✅ Talocrural ankle.
- [x] ✅ Subtalar / hindfoot.
- [x] ✅ Midfoot / forefoot.
- [x] ✅ Hallux / lesser toes.
Gate 4: ✅ PASSED — reference evidence compilation: 44 mechanics profiles, 427 assignments, 62 contextual observations and 86 registered sources across the programme. Active/passive evidence availability and study limitations remain explicit; no numerical production envelope or character motion is accepted. See `gate4_verification.json`.

## PHASE 5 — CURRENT RIG VS ANATOMICAL MASTER GAP ANALYSIS
- [x] ✅ Shoulder gap analysis.
- [x] ✅ Neck/spine gap analysis.
- [x] ✅ Elbow/forearm gap analysis.
- [x] ✅ Wrist/hand/thumb/fingers gap analysis.
- [x] ✅ Pelvis/hip gap analysis.
- [x] ✅ Knee/patella gap analysis.
- [x] ✅ Ankle/foot/toe gap analysis.
- [x] ✅ Produce one final “real anatomy vs current rig vs required change” matrix.
- [ ] 🔁 REOPEN — current-rig side binding. Measured r95 geometry faces −Y with +Z up, so the character’s anatomical left is +X; runtime `*_l` bones lie on −X (anatomical right). Hand chirality and facing were independently verified (F-SIDE-001). The static matrix’s name-based `*_left → *_l` mapping must be read as anatomical-left ↔ runtime `*_r` until the owner decides runtime naming.
Gate 5: ✅ PASSED — source-pinned static comparison: 206 bone rows, 427 articulation rows, 44 mechanics-profile rows. See `current_rig_anatomical_gap_matrix.json` and `docs/COMPLETE_SKELETON_FINDINGS_AND_VERIFICATION_20261007.md`. Local-character motion remains unverified.

## PHASE 6 — CHARACTER-SPECIFIC FITTING
- [x] ✅ Prerequisite: Blender toolchain verified live (Blender 5.2.1 LTS `bpy` module). 22/22 smoke checks; three adapter defects fixed with regression tests (TOOL-001..003). Evidence: `ORIGINAL_V1_WORK/anatomy/blender_toolchain_verification_20261007.json`.
- [x] ✅ Prerequisite: isolated audit copy `ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a001.blend` (sha256 `0655dae1…`) from the pinned r95 BARE export (sha256 `c4b8e388…`, r95 dev-freeze candidate `8a39a22d…`); 1 BU = 1 m.
- [x] ✅ Fit complete skeleton to HomeGymPT_Male_ORIGINAL_v1 proportions. All 206 placed (`character_fit_r95_a002.json`); per-bone class and confidence recorded. 115 proportional placements are low confidence.
- [x] ✅ Place joint centres from character landmarks. Hip: 4 regressions. GH: 3 methods. Knee: 2. Ankle: 2. Elbow and wrist: ISB section centres. 427 markers.
- [ ] 🟡 Verify bilateral symmetry and segment lengths. Symmetry PASS (0.38 mm). Stature-equation check still recorded FAIL, but the same chain run on 4,082 ANSUR II men shows a method bias (femur −6.4 cm, humerus −9.7 cm). The character's femur and humerus fall at the 26th and 20th percentiles of real men, while HJC, KJC, elbow and GH depth match independent ANSUR / open-model references within 2–10 mm. The forearm and hand are genuinely short on the authored body (z −2.2): a character-specific limitation, not a fit error. See the findings section “F-PROP-001 / F-GH-001 / F-HJC-001 investigation”. No a004; a003 retained as the audit baseline.
- [x] ✅ Verify no distinct anatomical joint centres are accidentally collapsed. AC–GH 41.8 mm, talocrural–subtalar 31 mm; no two of the 427 markers are within 0.1 mm.
- [x] ✅ Record skeleton-first owner policy: canonical anatomy is the source of truth and production mesh/skin must be refit around it. Evidence: `docs/SKELETON_FIRST_PRODUCTION_POLICY_20261008.md`.
- [x] ✅ Create machine-readable provisional skeleton-first proportion target record, separating corroborated joint-centre anchors from reopened distal-arm/hand/foot proportions and from surface-only diagnostics. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_skeleton_proportion_targets_v1.json`; regression tests: `scripts/test_skeleton_first_proportions.py`.
- [x] ✅ Build a complete a003 rebuild-gap inventory. Result: 206 bones total; only 13 moderate-confidence placements and 193 low-confidence placements (115 proportional, 40 low-confidence surface-landmark, 38 surface-station). Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_skeleton_rebuild_gap_v1.json`. Low confidence means “not freeze-ready”, not automatically anatomically wrong.
- [x] ✅ Define measurement semantics so surface, joint-centre, osteometric, radiographic-relative and control-stick lengths cannot be compared as if equivalent. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_measurement_definitions_v1.json`.
- [x] ✅ Hand skeleton-first audit. A003 metacarpals 2/3 are ~2.4–2.5 SD short versus a 50-male radiographic sample and ~9–12 mm short versus an independent 2025 CT mean; M4 is also short, while most phalanges remain within 2 SD. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_hand_proportion_audit_v1.json`.
- [x] ✅ Foot skeleton-first audit, then corrected with stature-aware evidence. The surface foot is definitely too long (~305 mm vs stature-conditioned ~280 mm; z≈+2.77), but the earlier claim that all metatarsals are themselves definitely oversized was withdrawn: stature-aware Spanish/Portuguese equations predict M1/M2 lengths close to a003 at 1.82 m. Internal foot-length distribution is therefore REOPEN, not pre-shortened. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_foot_proportion_audit_v1.json`.
- [x] ✅ Forearm skeleton-first audit. The radius remains a real retargeting candidate: the stature-conditioned ANSUR component chain implies radiale–stylion ≈278 mm at 1.82 m while the current a003 osteometric proxy is ≈247 mm. The ulna is less clearly short and must not be lengthened by the same amount without endpoint-matched evidence. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_forearm_proportion_audit_v1.json`.
- [x] ✅ Carpal rebuild specification. Current carpal sticks are schematic (six of eight are exactly 11 mm); CT evidence requires bone-specific size hierarchy, centroids and neutral-axis corridors. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_carpal_geometry_plan_v1.json`.
- [x] ✅ Tarsal geometry audit. Current tarsal sticks are control/reference segments, not whole-bone geometry (e.g. ~19 mm calcaneus stick vs ~75 mm male CT axial calcaneus; ~52 mm cuboid stick vs ~34 mm dry-bone cuboid length). Canonical foot work must separate bone envelopes, centroids and contact centres from control-stick length. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_tarsal_geometry_audit_v1.json`.
- [x] ✅ Spine geometry audit. A003 collapses adjacent vertebral bodies onto shared endpoints (0 mm disc gaps) and stretches lumbar body sticks to ~38–45 mm versus ~23–24 mm CT middle-body heights. Canonical spine must separate true vertebral body geometry from non-bone disc spacing. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_spine_geometry_audit_v1.json`.
- [x] ✅ Curved rib rebuild specification. A003 ribs are straight chords, which caused F-RIB-001 and a degenerate rib-neck axis. Keep 24 rib bones in the 206 count, but add non-bone curved centrelines/contact landmarks and source-backed rib-level geometry. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_rib_geometry_plan_v1.json`.
- [x] ✅ Shoulder-girdle audit. A003 SC→AC straight clavicle span ≈223 mm versus adult male true/centreline clavicle means roughly 150–167 mm: the clavicle proportion defect is directly confirmed. The a003 GH→inferior-angle scapular span ≈212 mm is also strongly suspicious against published 3D scapular height/width scale, but an audit correction removed an invalid height-only invariant; exact scapular shortening is not frozen until a landmark-compatible 3D envelope is built. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_shoulder_girdle_audit_v1.json`.
- [x] ✅ Pelvis/sacrum audit. Sacral reference length ≈103 mm is provisionally plausible versus adult male ~108 ±10 mm, while the os coxae remain too schematic/low-confidence for freeze. HJC is retained provisionally. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_pelvis_geometry_audit_v1.json`.
- [x] ✅ Lower-limb long-bone audit. Femur/tibia anchors remain provisionally credible; patella size (~44 mm) is inside adult male corridors; fibula needs endpoint-defined refinement but does not show a gross length defect. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_lower_limb_long_bone_audit_v1.json`.
- [x] ✅ Craniofacial/hyoid audit. The 206-bone head topology is complete but the cranial/facial bones are mostly schematic low-confidence reference sticks. Current TMJ inter-centre breadth ≈114.9 mm is provisionally plausible against an adult male 3D-CT corridor, while mandible, hyoid and fixed cranial/facial geometry still need landmark-rich reference envelopes. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_head_neck_geometry_audit_v1.json`.
- [ ] 🟡 Replace remaining mesh-driven placements with independently sourced canonical targets. Priority now: canonical radius/ulna endpoints and wrist centre → carpal centroids/axes → reconcile foot length across tarsals/metatarsals/toes using stature-aware definitions → rebuild thoracic/spinal/rib landmark coordinates → skull/craniofacial reference geometry. Exact canonical values are not frozen yet.
Gate 6: ⛔ NOT PASSED. The femur/humerus conflict is explained as stature-equation method bias, with independent corroboration of HJC, KJC, elbow and GH. OWNER DECISION 2026-10-08: short forearm/hand and long feet are not accepted final styling. The anatomical skeleton is the source of truth; production mesh/skin will later be refit around validated skeletal proportions. a003 remains an audit baseline only. Gate 6 remains open until the canonical target skeleton is independently proportioned and the 193 low-confidence placements are either re-targeted or explicitly justified.
- [x] ✅ Add evidence-convergence gate to prevent one-source overclaims. Two audit corrections are explicitly preserved: scapular GH→inferior span cannot be judged from vertical height alone; metatarsals cannot be blanket-shortened from one population mean. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_evidence_convergence_v1.json`.
- [x] ✅ Add stature-conditioned global landmark scaffold (including biacromial breadth ≈425.2±16.2 mm at 1.82 m). A003 bi-AC joint breadth ≈481.4 mm is already wider than the expected **outer acromial** breadth, independently confirming excessive shoulder-girdle width. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_global_landmark_targets_v1.json`, shoulder audit.
- [x] ✅ Add gated pre-Blender target-selection state and validator. `canonical_target_selection_v1.json` remains `freeze_ready=false`; a new skeleton-first Blender candidate must not be created simply to show progress. A live connector-side preflight of the selection/convergence/corridor/spec files passes with zero schema/state errors. Validator: `scripts/validate_canonical_target_selection.py`.
- [x] ✅ Transcribe the complete Holcombe 2017 rib demographic model (Tables A1/A2) for all 12 levels and add a source-scale evaluator/tests. Height and male sex are known; age and weight remain explicit unresolved inputs rather than invented defaults. Evidence: `ORIGINAL_V1_WORK/anatomy/rib_demographic_model_holcombe2017_v1.json`, `scripts/anatomy_fit/rib_demographic_model.py`, `scripts/test_rib_demographic_model.py`.
- [x] ✅ Build a level-by-level spine body/disc evidence stack. C3–L5 body heights and C2/3–L5/S1 disc gaps are now separated by measurement definition; the full direct-anatomical thoracic disc table is recorded. C2 body height and the 3D sagittal/endplate sequence remain open. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_spine_level_stack_v1.json`.
- [x] ✅ Advance carpal geometry independently of the mesh: seven neutral carpal axes are mapped into the HGPT world basis and all eight carpals now have adult-male 3D envelope constraints. Centroids/contact centres and pisiform axis remain blocked. Evidence: `ORIGINAL_V1_WORK/anatomy/canonical_carpal_axis_targets_v1.json`, `canonical_carpal_envelopes_v1.json`.
- [x] ✅ Advance shoulder-girdle target selection without fitting back to r95. Stature-conditioned outer biacromial breadth, endpoint-compatible clavicle length and neutral-standing clavicle orientation are now mapped explicitly into the HGPT basis (anatomical left +X, posterior +Y, up +Z). A 50/60/70 mm SC-width sweep is retained only as transparent geometry exploration, **not** as target evidence; absolute SC/AC coordinates remain open. Evidence: `canonical_shoulder_target_constraints_v1.json`, `canonical_shoulder_feasible_family_v1.json`, `canonical_shoulder_frame_mapping_v1.json`; tests added.
- [x] ✅ Replace the earlier ambiguous scapular-height comparison with a matched-landmark check. A003 AA→TS is ≈227 mm versus male 3D-CT posterolateral-acromion→medial-spine midpoint 113.0±6.6 mm (range 90–129); a second cadaveric spine/acromion measure is also far smaller. Transverse scapular geometry is now a confirmed rebuild defect, while exact superior-inferior length remains open. Evidence: `canonical_scapula_landmark_audit_v1.json`.
- [x] ✅ Recheck and correct the shoulder landmark source itself. The 2026 cadaver paper does **not** report a direct lateral-acromion→AC distance; it reports lateral-STSL→lateral-acromion (77±10 mm) and lateral-STSL→AC (45±6 mm). The earlier 34±8 mm direct-offset transcription/inference was withdrawn from constraints, helpers, tests and target selection. This does not change the independent a003-width/clavicle failures. Absolute AC placement remains blocked pending a verified SC/manubrial or landmark-compatible scapula solve.
- [x] ✅ Sternum target was also cross-checked rather than accepted from the first comparison. Unconditioned male CT manubrium+body means (~152–159 mm) initially made a003 (~203 mm vertical / ~213 mm chord) look too long, but stature-linked sternum studies from several populations materially change the picture at 1.82 m. Because those equations predict stature from sternum and the meta-analytic correlation is only moderate, the sternum is now **C / REOPEN_STATURE_METHOD_CONFLICT**: rebuild the landmarks, but do not preselect shortening or lengthening. Evidence: `canonical_sternum_geometry_audit_v1.json`.
- [x] ✅ Add a non-Blender direct ANSUR radius-target report builder. It will compute the actual stature-conditioned radiale–stylion regression/residual corridor from the committed 4,082-man dataset and compare it to a003 without inferring ulna length from radius. Evidence: `scripts/anatomy_fit/build_forearm_target_report.py`, `scripts/test_forearm_target_report.py`.

- [x] ✅ Reconcile target preflight with the newer full-text direct AC distance. Independent full-text recheck confirms 34±8 mm; only a 3D bound is accepted. Mutation tests reject missing full-text provenance, a wrong landmark value, transverse equality and non-finite shoulder measurements. Canonical subset: 39 tests passing; atlas inventory/semantic/source validators pass. Gate 6 remains open.

## PHASE 7 — BUILD HGPT_ANATOMICAL_MASTER
- [x] ✅ Create complete anatomical armature/reference collection. `HGPT_ANATOMICAL_MASTER` in `HGPT_ANATOMICAL_REFERENCE`, audit file a002 (`f172720b…`).
- [x] ✅ Represent every conventional adult bone. Independent capture: coverage 206/206 and identity PASS.
- [x] ✅ Tag each bone ACTIVE / FOLLOWER / FIXED / REFERENCE (92 / 87 / 26 / 1), as Blender custom properties.
- [x] ✅ Add required non-deforming anatomical landmarks/joint frames: 427 joint markers and 51 landmarks, round trip ≤ 2.9e-7 m.
- [x] ✅ Validate hierarchy, naming and symmetry. 201 articular parents, 3 explicit carriers, 2 roots; no cycles; symmetry PASS.
Gate 7: 🟡 STRUCTURE VERIFIED. Not passed for placement while Gate 6 is not passed.

## PHASE 8 — JOINT SOLVERS
Shared conventions: ISB JCS solver and measurement (`scripts/anatomy_fit/joint_solver.py`, `isolated_tests.py`).
- [ ] 🟡 Spine / cervical solvers. Segmental Z-X-Y about disc markers at every level C3/4–T12/L1 plus L2–S1; C1/C2 axial; C0–C1 flexion/extension (sourced 17.9° total, conflicting reports recorded); cervical C3/4–C6/7 from asymptomatic controls (Anderst 2013). Ribs 1–7: pump-handle component only (F-RIB-001: straight-rib axis degenerate). Moving centres of rotation, per-level coupling, ribs 8–12, C2/3, C7/T1 and L1/L2 values are not implemented (no accessible source).
- [ ] 🟡 Shoulder-complex solver. GH swing–twist plus sourced ST rhythm (0.43/°; McClure end values), clavicular posterior rotation (31°) and retraction (15°). SC elevation (bound only) and plane dependence are not applied.
- [ ] 🟡 Elbow / forearm solver. Flexion about the trochlea–capitulum axis; pronation about the radial-head → ulnar-head axis. Carrying-angle obliquity is not measurable on this surface.
- [ ] 🟡 Wrist / hand / thumb / finger solver. Two-stage wrist (stage split UNVERIFIED: sources conflict); digit MCP/PIP/DIP; MCP abduction (finger spreading, clinical 25°); thumb MCP/IP; thumb CMC radial abduction and anteposition; opposition components (TMC palmar abduction 37° sourced, pronation TEST AMPLITUDE). Full opposition (TMC/MCP/IP flexion), individual carpals and the pronation magnitude are unresolved.
- [ ] 🟡 Hip / pelvis solver. Hip 3-DOF JCS; SI nutation ±0.85° (sourced 1.7° total). Pubic symphysis and pelvic-ring compliance are not implemented.
- [ ] 🟡 Knee / patella solver. Flexion with the screw-home coupling (3.6°) and a sourced patellar follower (0.66 × knee flexion vs the femur). The patellar translation path is unsourced (rotation about the fitted knee axis). Tibiofibular: distal fibular follower (1.04 mm lateral, 1.03 mm posterior over the 60° ankle arc); fibular rotation and proximal motion unquantified.
- [ ] 🟡 Ankle / hindfoot / forefoot / toe solver. Talocrural axis (obliquity not measurable) with a distal fibular follower; subtalar Inman axis; talonavicular dorsi/plantarflexion (sourced 7.39° gait range); hallux MTP. First TMT, naviculocuneiform, calcaneocuboid and lesser toes unresolved (no defensible accessible values).
Gate 8: ⛔ NOT PASSED (follower/contact mechanics incomplete; several couplings lack accessible source magnitudes).

## PHASE 9 — ISOLATED BONE-ONLY MOVEMENT TESTS
Current run `audit/runs/isolated_bone_only_014` on fit a003: 135 tests (70 earlier + 65 newly sourced), all PASS, none unmeasured. 41/43 mirror pairs pass on reflected transforms of every commanded bone (followers included); 2 side-specific pairs are covered by the solver mirror test. Three independent reviews found and fixed sign defects and check gaps. Every spec has an absolute world-direction assertion, verified by sign mutation. The distal-marker gate is a primary-channel lever arm of at least 10 mm. Runs 008, 010, 011 and 013 are kept as the runs that exposed gate weaknesses.
- [x] ✅ Neutral → intermediate → near-limit sweeps, for the implemented joints. Source-context amplitudes are attached; amplitudes without a joint-specific source are labelled TEST AMPLITUDE.
- [x] ✅ Both sides (mirror-checked).
- [x] ✅ Ascent / descent / reversal; commanded and measured reversal frames match.
- [ ] 🟡 Multi-plane and coupled motions. Hip at 0°/90° flexion; GH in 3 planes and axial rotation at 2 elevations; elbow at 2 pronations; forearm at 2 elbow angles. Couplings: shoulder complex, knee screw-home, patellar follower, fibular follower, TMJ rotation + glide, thumb opposition components. Run 014: 135 tests (talonavicular added). Full opposition, rib–sternum coupling and midfoot remain untested.
- [x] ✅ Joint-centre trajectory checks: drift ≤ 6e-8 m; distal-marker radius constancy; GH-centre path with the scapula.
- [x] ✅ Continuity / acceleration checks: second differences match commands within 1e-3°.
Gate 9: ⛔ NOT PASSED. Joint coverage and follower/contact behaviour are incomplete (see the findings report), and the Gate 6 proportion conflict is unresolved.

## PHASE 10 — WHOLE-BODY FUNCTIONAL MOVEMENT TESTS
Not started. The tracker order requires isolated Gate 9 first, and the atlas holds no task kinematics (`task_expected_range` is null for every profile), so functional sweeps would be invented. Next route: drive the master from the project's authored exercise definitions after Gates 6/9, and report joint angles against the context observations.
- [ ] ⛔ Squat.
- [ ] ⛔ Split squat / lunge.
- [ ] ⛔ Hip hinge.
- [ ] ⛔ Calf raise / forefoot loading.
- [ ] ⛔ Curl.
- [ ] ⛔ Row.
- [ ] ⛔ Shoulder press.
- [ ] ⛔ Pull-up / hang.
- [ ] ⛔ Push-up / plank.
- [ ] ⛔ Reaching in multiple planes.
- [ ] ⛔ Loaded grip / pinch.
- [ ] ⛔ Wrist-supported loading.
Gate 10: ⛔ BLOCKED

## PHASE 11 — DERIVE RUNTIME RIG
- [ ] ⬜ Map anatomical master movement to production controls.
- [ ] ⬜ Prove which anatomical bones can safely be grouped.
- [ ] ⬜ Keep any control whose removal causes meaningful mechanical error.
- [ ] ⬜ Automated anatomical-master vs runtime-rig comparison.
Gate 11: ⬜ NOT PASSED

## PHASE 12 — SKIN / DEFORMATION REBUILD
Only after skeleton gates pass.
- [ ] ⬜ Shoulder / chest / axilla.
- [ ] ⬜ Neck / torso.
- [ ] ⬜ Elbow / forearm.
- [ ] ⬜ Wrist / hand.
- [ ] ⬜ Pelvis / hip.
- [ ] ⬜ Knee / patella.
- [ ] ⬜ Ankle / foot.
- [ ] ⬜ Pose-space correctives only where skeleton + weights cannot produce the required soft-tissue result.
Gate 12: ⬜ NOT PASSED

## PHASE 13 — APP EXPORT / PERFORMANCE
- [ ] ⬜ Export HGPT_RUNTIME_RIG.
- [ ] ⬜ Measure GLB size.
- [ ] ⬜ Measure deform-bone count.
- [ ] ⬜ Measure influences/vertex.
- [ ] ⬜ Measure CPU solver cost.
- [ ] ⬜ Measure GPU skinning cost.
- [ ] ⬜ Measure memory / FPS on target phone.
- [ ] ⬜ Keep master-vs-runtime regression suite.
Gate 13: ⬜ NOT PASSED

## CURRENT POSITION

Checkpoint plan: [2026-10-08 skeleton verification checkpoints](superpowers/plans/2026-10-08-skeleton-verification-checkpoints.md). Current checkpoint **CP1 — canonical regional target closure**, Gate 6 open. No new corrected whole-body canonical Blender revision exists. CP0 is confirmed only for baseline/tooling; provisional source fixtures and a003 tests do not close CP3–CP7.

Completed: Phases 0–5 (reference definitions, evidence compilation and static gap comparison); Blender toolchain verification.
Done: Phase 6 fit and Phase 7 master structure (fit revision a003); Phase 8 solver core; Phase 9 isolated tests (135, run 014).
Not passed: Gate 6 (owner decision is now resolved as skeleton-first; canonical target geometry is still not freeze-ready), Gate 8 (followers/contacts), Gate 9 (coverage).
Next: finish target selection rather than creating a premature Blender candidate. Shoulder defects are confirmed, but absolute SC/AC placement is deliberately reopened after source verification; find/derive a valid SC/manubrial constraint and solve the landmark-compatible scapular frame. In parallel, run the direct ANSUR forearm report, continue spine/rib/carpal target closure, and resolve foot/pelvis/head blockers. a003 remains the comparison baseline only; production mesh reshaping waits until the canonical skeleton target is frozen.
Morning review pack (current a003, read-only renders, links, hashes, defects, owner questions): `ORIGINAL_V1_WORK/anatomy/review_pack_a003_20261007/README.md`.
Resume: see the "Resume instructions" section of `docs/BLENDER_ANATOMICAL_VALIDATION_HANDOFF_20261007.md`.
Gates 6–13 remain unpassed.
Production model, recovery work, geometry, weights and motion drivers unchanged.
Comprehensive findings, source register, verification and local acceptance checklist: `docs/COMPLETE_SKELETON_FINDINGS_AND_VERIFICATION_20261007.md`.

Local validation preparation is available in `docs/BLENDER_ANATOMICAL_VALIDATION_HANDOFF_20261007.md`: read-only capture, source-bound test requests and offline numerical reports. Prepared tools do not complete Gates 6–10. The Blender adapter passed a live smoke test here (Blender 5.2.1 `bpy`, runs `blender_smoke_001`/`002`); a laptop run with the Blender application is still advisable.

## 2026-10-08 measured scapula continuation

**PROVISIONAL:** Added a source-bound relative 29-landmark scapular envelope from Lee/Lawrence/Rainbow 2024 (dataset DOI 10.5683/SP3/PHVS3D; paper DOI 10.1111/joa.14124). The raw workbook, SHA256, source endpoint mapping and recomputable direct stature regressions are committed. Coverage: 125 subjects, 45 male; the asymptomatic/no-full-thickness-tear male subgroup has 34 subjects, 33 with stature. At the current ~182 cm stature, that subgroup predicts superior-to-inferior angle distance ~167.16 mm and medial spine to exterior acromial angle ~129.23 mm. These are provisional measurements, not frozen joint coordinates.

**CONFIRMED source-definition correction:** The 2022 scapular study d1 measures glenoid tubercles rather than articular rim endpoints; d6/d7 are projected distances along a reference line rather than direct chords. Exact endpoints remain distinct. No averaging with incompatible definitions, or substitution of the interior acromial angle to force agreement, is permitted.

Verification: 13 scapular tests, 44 canonical tests and atlas structure validation pass. Tests reject reflection/chirality errors, degeneracy, missing/duplicate IDs, nonfinite values and extrapolation; rigid coordinate invariance and committed report reproduction are checked. Workbook A1-only dimension metadata was independently found incorrect; actual cells give complete coverage. Live Blender 5.2.1 LTS bpy adapter: 22 synthetic checks pass. Bilateral sparse-landmark save/reload: 58 points, max coordinate error 5.58e-9 m. Evidence: `ORIGINAL_V1_WORK/anatomy/audit/runs/work_bpy_preflight_20261008_001/`. Initial Blender harness failure from a stale RNA pointer is retained and corrected; it changed no anatomy.

**BLOCKED exact shoulder freeze:** Absolute SC/AC/GH centres, thorax-relative neutral scapular pose and endpoint-matched independent confirmation remain required. The glenoid shallowest point is not a GH sphere centre. The safest next action is resolve these mappings and constraints using the measured envelope. Gate 6 remains open, and no new canonical skeleton/production mesh is created.

## 2026-10-08 lumbar semantics, rib validator and radius recheck

**PROVISIONAL:** P1 now has six superior-endplate orientation frames, S1 through L1. The retrieved original source Figure 5C confirms superior-to-superior segment angles. They include the upper vertebral body wedge plus intervening disc; using the entire angle as a disc-only wedge would double-count body shape. Frame/sign tests give S1 slope +40.9° and L1 slope −15.5°, consistent with provisional 56.4° total lordosis. Absolute centres and inferior endplates remain undefined. The legacy KIM_2022 source identifier is retained, while the DOI/title and PDF attribution are explicitly recorded. Source: https://d-nb.info/127884676X/34 (Figure 5, printed page 6).

**CONFIRMED validation weakness:** Rib demographic evaluator accepted NaN/Infinity predictors and could silently truncate malformed coefficient lists through zip. A failing mutation test reproduced it; finite predictor/coefficient/result and exact five-term checks now reject those inputs. Six rib tests pass. Source parameters are unchanged, and no age/weight is silently selected. Full curved ribs remain blocked on the unambiguous proximal Eq 2.18 branch constraint; three University of Michigan source routes returned HTTP 403.

**STRONGLY SUPPORTED:** Direct ANSUR radius regression independently recomputed from the committed 4,082-man dataset and matches the stored report within 1e-9. The a003 proxy is ~30.72 mm below the stature-conditioned prediction. Ulna dimensions are not inferred. The report-builder default pointed to a missing surface filename; corrected to the existing character_surface.json and verified by the recomputation.

Verification: 48 canonical, 13 scapular and six rib tests pass. Full Python discovery: 685 tests, five failures and four errors, all in the previously identified production/recovery fixtures; retained output at `ORIGINAL_V1_WORK/anatomy/audit/runs/work_bpy_preflight_20261008_001/python_suite_685_tests.txt`. Region-specific essential targets and safest next actions are recorded in `target_blockers.json`. Gate 6 remains NOT FREEZE READY; Gates 8/9 are not accepted. Blender is available, but a new canonical candidate must wait for the essential numerical geometry.

## 2026-10-08 clavicle endpoint cross-check

**STRONGLY SUPPORTED context; exact target still open:** Qiu et al. 2016 (PMC4819086, DOI 10.1155/2016/6219761) independently reports male clavicular articular-surface-centre chord 152.9±9.3 mm. This is more directly mapped to the desired bone endpoints than an extremal-point length, but it is not an instantaneous rotation-centre measurement. The sample has 26 men with bilateral bones, and no stature regression; its mean is not promoted into the canonical skeleton. It remains separate from 154.8 mm extremal chord and 166.8 mm true centreline evidence. Source semantics and cross-check: canonical_clavicle_endpoint_crosscheck_v1.json.

SC anchor search: Li 2012 PMID22340551 measured bilateral clavicle separation, but the accessible abstract omits the required value and endpoints. Tuscano 2009 PMID19308406 reports joint-space/head-diameter/offset variability, not SC-centre breadth. Wijeratna 2013 PMID22933016 concerns joint-plane orientation. None justifies substituting maximum manubrial width for SC-centre breadth. Need the endpoint-matched full table/figure or independent articular landmarks before exact placement.

## 2026-10-08 Work Blender recheck and Claude inspection handoff

Fresh Blender 5.2.1 LTS bpy run: unchanged a003 master, 135/135 implemented isolated integrity tests pass; 41 mirror pairs pass and two remain SOLVER_TEST (43 total). Source SHA256 before/after matches and the frame is restored. This is repeatability/implementation evidence for the diagnostic baseline, not acceptance of canonical proportions or all contact/follower mechanics. Compact per-test evidence, hashes and explicit mirror statuses: `ORIGINAL_V1_WORK/anatomy/audit/runs/work_bpy_baseline_recheck_20261008_001/`.

Eight independent distal-spiral tests pass: all 12 source mean endpoints, derivative-zero peak check, analytic circular special case, no loops, physical scale, arc/chord distinction, sampling consistency and nonfinite/bad sample rejection. Failure before correction retained: nonfinite physical span was accepted, and noninteger sample count raised the wrong exception. Source-mean distal segments are now reproducibly exported. No reference age/weight is selected, and no full proximal rib is claimed. Live bpy non-bone curve save/reload checks 24 bilateral distal curves, 101 points each, 7.44e-9 m maximum coordinate error, zero bilateral reflection error, and no costotransverse permission for ribs 11/12.

Prepared independent review handoff: `docs/CLAUDE_WORK_SKELETON_INSPECTION_HANDOFF_20261008.md`. Gate 6 remains open; no new canonical skeleton or corrected-skeleton renders are presented. Production geometry, weights and drivers unchanged.

## 2026-10-08 adversarial carpal-axis verification

Existing unit-length and mirror checks could accept seven identical proximal lines, despite failing every non-zero source angle. Added a separate projection validator: sagittal palmar-positive and coronal ulnar-positive angles must be recovered from each bilateral XYZ line. Four tests reject mirrored/unit stubs, palmar sign reversals, side swaps, missing vectors and NaN; existing vectors pass. Numeric targets are unchanged. This checks source-frame arithmetic, not contact geometry.

Evidence independence guard: the 2021 and 2023 normal alignment reports both describe 121 asymptomatic wrists. Until subject provenance proves otherwise, treat them as a potentially shared cohort rather than two independent replications. The 2023 publisher abstract independently confirms the angle signs and geometric-versus-articular-normal axis definitions. Absolute carpal centres, pisiform orientation and contact layout remain open. Primary: https://journals.sagepub.com/doi/10.1177/17531934231160100.

## 2026-10-08 lumbar body/disc orientation continuation

**PROVISIONAL:** Bailey et al. 2016 (DOI 10.1111/joa.12451, Methods/Table 2) supplies separate male body wedge angles, with standing disc angles retained as context. P1 now has five inferior endplate frames and five derived disc wedges alongside the six superior frames. Body + disc closes each superior-to-superior segment, without assigning the entire segment to the disc. The source reports standard errors, not population SD; no corridors are fabricated. Pooled body means plus standing disc means leave a 0.50° source closure residual because the subsets differ; this is preserved. Derived P1 disc angles are explicitly cross-cohort provisional calculations, not the source's standing means or a measured individual.

**CONFIRMED coordinate convention:** +X left, +Y posterior, +Z superior. Positive body lordosis is inferior slope minus superior slope. An independent anterior-taller trapezoid checks this sign; body L1 is kyphotic, so its inferior plate slope is −19.56°, not −11.44°. No absolute centres or thickness/contact placement are inferred.

**REOPENED source review:** The 2026 lumbar CT paper text states 50 men/50 women, while Table 1 counts total 46/54. Its width definitions also mix mid-sagittal language, lateral-edge language and a later reference to mid-coronal planes. Existing height means remain available as provisional context; no AP/ML width target is frozen. Machine-readable review: `canonical_lumbar_ct_source_review_v1.json`. Need independent endpoint-matched height/envelope corroboration or author clarification before freezing these dimensions.

Verification: 60 canonical tests plus 27 scapula/rib tests pass (87 total). Atlas remains 206 bones/427 contact complexes; source target selection and carpal projection validators pass their limited scopes. Blender 5.2.1 LTS save/reload checks 11 local orientation fixtures, maximum matrix error 5.96e-8, maximum determinant error 1.79e-7. No canonical candidate is created. Evidence: `audit/runs/work_bpy_lumbar_orientation_20261008_001/verification.json`; reproducible command in its README. Gate 6 and Gates 8/9 remain open. Production mesh/weights/runtime unchanged; engine checks remain deferred per owner priority.

## 2026-10-08 independent lumbar edge-height cross-check

**PROVISIONAL:** Added Hegazy/Hegazy 2014 primary full-text male MRI data (46 men, age 25–57; DOI 10.1155/2014/370852). Anterior/posterior body heights and separate anterior/posterior disc gaps are stored with endpoint definitions, distinct from CT central body heights and three-point mean disc heights. The MRI posture is supine with hips/knees flexed; disc heights cannot silently become standing geometry. No AP depth is inferred, so height differences do not uniquely determine angular wedges. Source data: `canonical_lumbar_edge_height_crosscheck_v1.json`.

**CONFIRMED source statistic inconsistency:** Table 4 prints L1 male posterior mean 26.30 mm and SD 26.30 mm, with observed range 20–30 mm. For n=46 the maximum possible sample SD is about 5.06 mm. The printed SD is preserved separately, the usable SD field is null, and no guessed correction is made. Other source-table statistics are not blanket accepted. A new necessary statistical consistency checker uses a bounded-variance test with the sample correction; it rejects impossible SD, nonfinite values, reversed ranges and bad sample counts. Passing this check alone does not prove anatomical validity.

Verification: 60 canonical, 27 scapula/rib and five statistical source tests pass (92 total). Current freeze-readiness records the new provisional lumbar orientations and independent edge-height evidence while retaining all essential global geometry blockers. Gate 6 remains NOT FREEZE READY. Existing Blender master, production mesh, weights and animation drivers unchanged. Need standing/contact/normal-height reconciliation, independent matched angle/envelope confirmation, and resolution of CT2026 source inconsistencies before placing lumbar centres.

## 2026-10-08 independent lumbar angle sensitivity and source identity audit

**STRONGLY SUPPORTED wedge pattern; exact target PROVISIONAL:** Been et al. 2007 primary Methods/Table 1 (DOI 10.1002/ar.20607) provides independent standing, same-body endplate-angle evidence: 106 adults, 56 men/50 women, radiographically normal clinical cohort, age 20–50. The pooled-sex wedge pattern supports upper lumbar kyphosis, near-neutral L3 and lower lumbar lordosis. These definitions match body wedges rather than full segments. Two source-separated P1 constructions are stored in `canonical_lumbar_orientation_sensitivity_p1.json`. Their inferior slopes differ by at most 1.06°; no averaging or numerical freeze occurs. This difference of means is not population SD or an uncertainty bound. Source: `canonical_lumbar_wedge_independent_crosscheck_v1.json`.

**CONFIRMED source identity correction:** CLAVICLE_CADAVER_3D_2013 and DARUWALLA_2013_CLAVICLE_3D share PMID24142486/DOI10.1002/ca.22288. Primary publisher metadata identifies Bernat et al.; the Daruwalla attribution was wrong. Both legacy IDs remain for compatibility, but count as one publication. Registry scan finds four bibliographic alias groups across clavicle, tarsal and rib evidence: 105 records map to 101 identifier groups. That count does not establish independent cohorts; missing identifiers and repeated cohorts across separate papers still require review. All four groups are explicitly guarded against double counting in the register. Numeric geometry and confirmed clavicle defect direction are unchanged.

Verification: 63 canonical tests plus 37 source-statistics/source-identity/scapula/rib tests pass (100 relevant tests). Live Blender 5.2.1 LTS checks 22 local endplate orientation helpers across both families, save/reload matrix error 5.96e-8 and determinant error 1.79e-7. No absolute centres or candidate skeleton created. Evidence: `audit/runs/work_bpy_lumbar_sensitivity_20261008_001/verification.json`. Source selection/atlas validators retain 206 bones and 427 articulations; Gates 6/8/9 remain open. Exact shoulder SC-centre breadth and full clavicle curve definition still lack essential compatible evidence; publisher abstract retrieved, Antwerp PDF routes returned 403 and Ghent copy is institution-restricted. Safest action is recover source endpoint/curve data or compatible independent landmarks, without inferring absolute joint positions from a surface width.

## 2026-10-08 measured glenoid rim orientation

**PROVISIONAL:** Derived a least-squares glenoid rim plane from the measured Lee2024 LM15 inferior, LM16 posterior, LM17 anterior and LM18 superior landmarks. The 34 asymptomatic/no-full-thickness-tear male subject orientations are retained as statistical context; the stature-conditioned mean-shape frame is separate. Report: `canonical_glenoid_rim_frame_v1.json`. Its centroid is the arithmetic rim-landmark centroid, not the humeral-head/GH centre. SC/AC/GH coordinates remain null. The predicted rim plane residual is 1.574 mm; nonplanarity is recorded rather than hidden. Projection angles are in this measured scapular basis and must not be compared directly with clinical version/inclination definitions.

**CONFIRMED bilateral frame convention:** Right first tangent is anterior; left first tangent is posterior so both pose rotations have determinant +1 while their outward normals and point geometry reflect correctly. Left anatomical anterior is negative first axis. Improper reflections are not used as rig rotations. Source-coordinate shape is still unposed relative to the thorax.

**CONFIRMED adversarial validation weakness and correction:** An isotropic four-point tetrahedral rim has no unique least-squares plane, but the initial fitter accepted an arbitrary normal. The failed mutation test is retained at `audit/runs/work_bpy_glenoid_rim_20261008_001/ambiguous_plane_before_fix.txt`. A smallest-singular-value separation check now rejects it. Seven tests cover analytic signs, tilt/translation covariance, rank deficiency, NaN, mirror/chirality errors, nonplanarity, proper bilateral frames and exact report reproduction.

Verification: 70 canonical plus 37 source/scapula/rib tests pass (107 total). Blender 5.2.1 LTS bilateral relative-rim helper save/reload: max matrix error 1.01e-7, determinant error zero, reflected centroid error zero. Evidence: `audit/runs/work_bpy_glenoid_rim_20261008_001/verification.json`. No canonical candidate, global shoulder pose or GH sphere is claimed. Exact SC-centre breadth, neutral scapular thorax pose and GH contact/sphere geometry are still essential blockers; need compatible primary landmarks/mechanics before global placement. Gates 6/8/9 stay open; production mesh, weights and runtime drivers unchanged.

## 2026-10-08 continuous endplate clearance and finite shoulder invariants

**CONFIRMED geometric validation requirement:** A positive disc-centre gap is insufficient. Two tilted planes can intersect inside an elliptical endplate footprint even when the centre and four cardinal rim points all have positive gaps. Added an analytic minimum over the entire caller-supplied common ellipse, with an explicit minimum witness and strict nonzero clearance. Measurement is HGPT +Z projection, not nearest-point/normal distance. It applies only to planes over an established common footprint; actual curved endplate surfaces and coverage remain required.

**PROVISIONAL diagnostic only:** 90 explicitly synthetic footprint/gap cases across the two provisional P1 lumbar orientation families expose six intersect/touch cases. These sweep radii and centre gaps are neither anatomical population means nor selected targets. No vertebral centres are inferred from them. Report: `canonical_endplate_clearance_sensitivity_v1.json`. Eight tests include independent dense-boundary verification, tangency, normal scaling, nonfinite/vertical/overflow rejection and exact report reproduction.

**PROVISIONAL source surface context:** Wang/Battié/Videman 2012 primary publisher abstract (DOI 10.1007/s00586-012-2415-8; 591 endplates from 76 male spines) supports asymmetric concavity. Its cranial/caudal labels are relative to the DISC: cranial means the upper vertebra's INFERIOR plate; caudal means the lower vertebra's SUPERIOR plate. Pooled mean depths 1.5/0.7 mm are recorded as context, not assigned to individual levels. Level-specific table/footprint and height definition remain essential. See `canonical_lumbar_endplate_surface_semantics_v1.json`.

**CONFIRMED shoulder validator weakness and correction:** Existing chord helper could accept an infinite curved length and coincident SC/AC endpoints; other measurement helpers could return NaN. Three failing tests are retained at `audit/runs/work_endplate_clearance_20261008_001/shoulder_invalid_before_fix.txt`. Finite numeric inputs are now required, collapsed chords fail, malformed/nonfinite endpoint predicates return false, and normal valid geometry is preserved. This changes validators, not target values or a003 geometry.

Verification: 78 canonical + 37 source/scapula/rib + 10 shoulder constraint tests pass (125 affected tests). Independent Blender 5.2.1 LTS mesh fixture: six synthetic planar surfaces, 128 rim points each, max coordinate error 4.38e-10 m. Mesh minima independently give intersection −0.656854 mm, separated +6 mm and tangency 0 mm. Report: `audit/runs/work_endplate_clearance_20261008_001/blender_verification.json`. The anatomy atlas/target validators retain their limited accepted scopes; Gates 6/8/9 remain open. New canonical skeleton and production geometry/weights/runtime remain unchanged. Actual endplate envelopes, source-compatible standing gaps and continuous curved contact clearance block global spine placement.

## 2026-10-08 hyoid axis correction and current dependency reconciliation

**CONFIRMED source mapping error:** Primary Abdelkader2025 Table 1 (DOI 10.1038/s41598-025-85518-w) defines CC-prime as AP body thickness, while Figure 1A shows the BB-prime minor axis vertically across the body. The existing provisional `body_AP_length=11.32` was an incorrect label. Source values are preserved; explicit local body extents are X width 24.3, Y AP thickness 6.99 and Z minor-axis height 11.32 mm. A neutral body tilt is not inferred from these population means. Historical source keys and the 6.99 generic thickness alias remain with explicit semantics. The failing pre-fix regression is retained in `audit/runs/work_hyoid_axis_review_20261008_001/hyoid_axis_before_fix.txt`.

**PROVISIONAL:** Six Blender dimension markers reproduce these axis extents after save/reload with maximum span error 4.35e-7 mm. These are a dimension fixture, not a whole hyoid, landmark envelope, global pose or canonical candidate. One unpaired reference bone and no osseous parent are preserved. Independent matched geometry/stature context, body/cornu landmarks, neutral tilt and canonical cervical placement remain open; C3 level alone does not fix AP position.

Current implementation specification/readiness/selection now reflect existing measured scapular/glenoid frames, verified distal rib segments, independent lumbar wedge context and provisional hyoid dimensions. Earlier subtraction-based AC inference remains rejected; the later direct full-text 3D distance remains available with its endpoint restrictions. These updates remove stale descriptions of missing work without clearing numerical freeze or contact/placement blockers. Hyoid overall D grade is retained pending complete independent geometry review.

Verification: 79 canonical + 47 source/scapula/rib/shoulder tests pass (126 relevant tests); target-selection, atlas and carpal projection validators pass their limited scopes. Current freeze_ready=false, Gates 6/8/9 remain open, production geometry/weights/runtime and a003 unchanged. No new corrected skeleton render is claimed. Primary PDF checked at Table 1/page 3, Figure 1/page 4 and Results/page 6; source review stored beside the hyoid values. Details/hashes: `audit/runs/work_hyoid_axis_review_20261008_001/`.

## 2026-10-08 target-selection gate adversarial continuation

**CONFIRMED validator defects corrected:** Unsupported, empty or missing evidence grades could falsely pass a synthetic otherwise-unblocked freeze check; nonboolean falsy freeze flags were accepted; malformed shoulder values raised TypeError rather than reporting rejection. The gate now requires a literal boolean, explicit A/B evidence leaves for freeze, and finite positive measurements before comparisons. C/D, unknown labels, empty collections and missing grades cannot justify freezing. Synthetic test fixtures are not anatomical target data. No target value or production geometry changes.

Verification: 82 canonical + 47 source/scapula/rib/shoulder tests pass (129 relevant tests). Full discovery: 740 tests, five failures/four errors, exactly the same named legacy production/recovery failures as the earlier 685-test checkpoint. No whole-project green claim; raw traces and per-name comparison retained in `audit/runs/work_target_gate_mutations_20261008_001/`. Target-selection/atlas/carpal-axis validators pass their limited scopes; 206 bones/427 articulations retained, freeze_ready=false. Gates 6/8/9 and new canonical skeleton construction remain open.

**BLOCKED exact shoulder SC anchor:** Li2012 PMID22340551 primary abstract omits bilateral clavicle distance value and precise endpoints. PubMed-linked Ovid full-text route was checked and returns HTTP402 Payment Required. Need accessible primary full table/figure or independent endpoint-matched SC articular landmarks before absolute SC/AC placement. No surface width or manubrial outer breadth is substituted. Other region-specific evidence/contact dependencies remain in current readiness; independent validation work continued despite this evidence blocker.

## 2026-10-08 independent review of Claude's 21 recent commits

Reviewed live HEAD `6570e750fdf0b6fbd899b3ab594ba1a84bd248e4`; all newer work is preserved. Details: `docs/GPT_REVIEW_OF_CLAUDE_RESULTS_20261008.md`. CP2 ledger covers all 206 bones and catches a003's zero disc gaps; CP3 builder rehearsals and source-register corrections are useful within their limited scopes. They do not close CP1 or create an accepted canonical skeleton.

**CONFIRMED validator weaknesses:** collapsing C3 crashes CP2 with division by zero; an unknown non-root parent-relation type passes; tiny positive disc planes 100 metres away from the candidate pass clearance. The axial specimen report also checks fitted planes over a partial footprint rather than full curved endplates. Read-only adversarial fixtures/results are retained in `audit/runs/work_claude_review_20261008_001/`; these implementation weaknesses remain unresolved at this review checkpoint.

**REOPENED measurement claim:** Claude's review again compares oblique GH-to-inferior-angle span with vertical scapular height. That does not establish a matched numerical scapular shortening target. The existing corrected shoulder audit remains authoritative; clavicle rebuild is still justified. Forearm shortness is strongly supported, but exact radius/ulna endpoints remain open. The de-Leva-only thigh-shortness claim was withdrawn; three recalled de Leva values still need primary-table verification.

Verification: 52 focused tests pass. Full discovery runs 787 tests with five failures/four errors; all nine names match the retained pre-Claude baseline. Static target/atlas validators pass within scope with `freeze_ready=false`, 206 bones, 427 articulations and 30 frames. Blender run-002 results were reviewed as archived observations, not freshly rerun; its raw captures/.blend were not retained. CP1 remains PROVISIONAL/BLOCKED, CP2 needs validation repair and anatomy closure, CP3 remains a builder rehearsal, CP4 is blocked. Gates 6/8/9 and Phase 10 remain open/deferred. Production geometry/weights/runtime and a003 are unchanged.

Next safe action: fix and adversarially test CP2 rejection/geometry binding, then continue CP1a source-compatible shoulder mapping and regional target closure; fresh Blender rehearsal with retained captures precedes a new immutable canonical candidate.

## 2026-10-08 CP2 adversarial repair checkpoint

**CONFIRMED fixes:** Degenerate vertebral disc participants now return failure instead of division by zero; unknown/malformed parent relations reject, with explicit root/carrier constraints preserving existing valid relations. Malformed plane entries return rejection. Positive plane-only clearance is now UNVERIFIED for actual endplates, with diagnostic gaps retained; a remote tiny footprint cannot yield structural acceptance. This is a scope correction, not completed curved-contact validation.

Before-fix failing regressions and after-fix adversarial observations are retained in `audit/runs/work_cp2_repair_20261008_001/`. 27 affected tests pass; full discovery runs 792 tests with the same named five failures/four errors as the preceding 787-test review. Target-selection/atlas validators pass within their static scopes; freeze_ready=false. Actual candidate-bound endplates, full footprints and surface error bounds remain unresolved. CP1/CP2 anatomy acceptance and Gates 6/8/9 remain open. a003 and production geometry/weights/runtime are unchanged.

## 2026-10-08 fresh Blender rehearsal and CP1a source-frame correction

**CONFIRMED build-path verification:** Blender 5.2.1 LTS restored via Python 3.13. Fresh empty-scene a003-data and mirrored-copy builds retain 206 bones/427 markers; both fresh-process captures pass round-trip comparison. Marker-position error is below 2e-7 m; exactly mirrored roll difference 0.027 degrees. All 135 isolated implementation tests pass on the new builder output; 41 Blender mirror pairs pass and two side-specific-amplitude pairs remain solver-only checks. Retained raw captures, both rehearsal .blend files, input fixtures, movement report/samples and hashes: `audit/runs/work_cp3_independent_20261008_001/`. This is an a003-data rehearsal, not corrected anatomy or Gate 9 acceptance.

**CONFIRMED source mismatch corrected:** Historical shoulder vector paired medial/lateral-extrema clavicle length with ventral/dorsal-extrema standing angles; surface landmarks were being treated as articular centres, and pooled data lacked male context. The vector/sweep numbers are preserved as illustrative history and their current states are reopened/ineligible for freeze. Matsumura2020 male data and precise definitions are now source-registered. Proper IJ/C7/PX/T8 source-point mapping is implemented and tested; it does not select global landmarks or transform clinical Euler angles. Tilted Blender fixture errors are below 2.1e-8 m / 3.6e-8 frame components. See `audit/runs/work_shoulder_source_frame_20261008_001/`.

Verification: 25 focused tests pass; full discovery 796 tests with the same named five failures/four errors. Static target/atlas validators retain scope and freeze_ready=false. CP1 numerical closure still requires endpoint-compatible SC/AC surface-to-articular mapping, canonical thorax pose and independent/stature context. CP2 actual curved-contact validation remains open. CP3/CP4 corrected-candidate acceptance and Gates 6/8/9 remain open; Phase 10 is deferred. a003, production geometry/weights and runtime remain unchanged.

## 2026-10-08 CP1a clavicle-shape statistics and SC-contact review

**CONFIRMED source-statistics conflict:** Fontana2020's printed pooled height/clavicle correlation 0.968 is incompatible with its reported subgroup/overall summaries if they describe the same paired sample. A conservative covariance bound, including printed-mean rounding and the full observed height range, is 0.691416 (below 0.692 with correlation rounding). Primary Figures 5/6 were inspected. The printed statistic is quarantined; no guessed replacement, inverted height-on-length fit or 1.82 m target is selected. Projected curvature radii and conoid context are retained with explicit endpoint, ratio-direction and unit limitations in `canonical_clavicle_shape_source_review_v1.json`.

**PROVISIONAL contact evidence:** Languth2024 MRI provides AP clavicular diameters, not bilateral SC-centre breadth; Table 1 interreader ICCs below .001 to .154 prevent precision target use. Lee2014 primary dissection distinguishes whole osseous end, anteroinferior cartilage patch, first-costal-cartilage contact and intra-articular disc; pooled disc thickness is not a uniform joint gap. See `canonical_SC_contact_semantics_v1.json`. Three source records added; identity scan retains five alias groups. Qiu's mean/SD remain unchanged; the unsupported claim that per-bone SD necessarily understates between-person SD is removed.

Verification: 21 affected tests pass; nine statistics tests also pass under Python 3.13. Full discovery: 800 tests, same named five failures/four errors as previous 796-test checkpoint. Source hashes, before-fix traces, a corrected analytic-test fixture mistake and transient annotation failure remain in `audit/runs/work_shoulder_shape_review_20261008_001/`. Static target/atlas validators retain scope and freeze_ready=false, 206 bones/427 articulations/30 frames. Exact SC articular anchors, matched stature/chord evidence and neutral shoulder contacts remain BLOCKED; CP1/CP2 acceptance and Gates 6/8/9 remain open. No Blender geometry or corrected candidate is claimed; a003 and production geometry/weights/runtime remain unchanged.

**2026-10-08 CP1a follow-up:** Checked Suarez Romero2026 full primary text (PMID41659779 / PMC12876668, DOI10.1016/j.xrrt.2025.100650), including Table I from ten bilaterally dissected cadavers. Its coordinates are surgical-portal distances to capsule/neurovascular structures, not bilateral SC articular-centre geometry. Source/access hash and exclusion reason are retained; no numerical shoulder target inferred. Exact SC anchor remains BLOCKED by essential endpoint-matched primary coordinates. Safest next action remains contact-patch/manubrial landmark acquisition rather than substitution of an unrelated distance.

## 2026-10-08 CP3 capture rejection/metadata repair and laptop handoff

**CONFIRMED validation weaknesses repaired:** Round-trip max reductions could hide NaN endpoints/frames; invalid bone Z vectors and substituted marker frame IDs could falsely pass; missing/empty data could crash. Full finite numeric/shape/nondegeneracy/identity checks now precede calculations, with structured rejections and CLI exit 1 for failed comparisons. Extreme finite inputs that overflow the frame norm also reject; the false-pass trace is retained.

**CONFIRMED capture semantic error:** Old `frame_bone` was populated from the attachment host, mislabeling 202 marker reference frames in the fresh legacy-file recheck. Builder now stores the source `hgpt_frame_bone` separately; capture retains source frame, carrier and actual parent as distinct fields. Fresh metadata-corrected a003/mirrored rehearsals retain 206 bones/427 markers and pass storage round-trip checks; all marker attachments and centres are unchanged. Older files/reports remain archived with this scope correction. No anatomical targets, a003 file or production geometry/weights/runtime changed.

Evidence: `audit/runs/work_cp3_rejection_repair_20261008_001/`, including new .blend/capture archives, SHA256, failed runs and parent comparison. 26 affected tests pass; full discovery 805 tests, same named five failures/four errors as the preceding 800-test checkpoint. CP2 anatomy remains FAIL on known baseline defects; freeze_ready=false, Gates 6/8/9 remain open, no corrected canonical candidate or Phase 10 acceptance. Planned 20:30 BST laptop inspection/continuation handoff: `docs/LAPTOP_SKELETON_HANDOFF_20261008_2030.md`. First unfinished numerical task remains CP1a matched SC/manubrial/clavicle/contact geometry; independent regional work may continue while essential evidence is unavailable.

## 2026-10-08 primary limb-endpoint review of Claude proposal

**CONFIRMED source correction:** Recovered original de Leva1996 PDF and visually checked Table 4, plus Tables 1/2 and the estimation text. Adjusted male SJC-EJC 281.7, EJC-WJC 268.9 and HJC-KJC 422.2 mm are confirmed source means. They are Table 4, not Table 1. **434.0 mm is KJC-LMAL; KJC-AJC is 440.3 mm.** The proposal now uses the correct endpoint row (460.3 mm under its diagnostic 1.82 m proportional scaling); the old 434.0 value remains in history/source review with its actual endpoint. No shank defect or resize is selected from this single scaled mean.

**REOPENED conversions:** Primary Table 2 HJC is 3.2 mm proximal of trochanterion, differing from the proposal's 8 mm below assumption. Added an explicitly approximate longitudinal-to-vertical sensitivity near 430 mm; no global HJC change or thigh shortening is selected. Primary WJC offsets are distal to stylion, differing from the proximal ISB-midpoint sensitivity. The old all-methods-within-1-SD forearm assertion is corrected: 12 mm exceeds the unshifted 10.8 mm ANSUR residual SD. That SD also excludes conversion uncertainty. Strong forearm shortness direction remains, while numerical radius/ulna targets require matched landmarks.

Machine-readable evidence: `canonical_de_leva_primary_endpoint_review_v1.json`, regenerated `canonical_limb_length_proposal_182_v1.json` and `canonical_forearm_endpoint_decision_v1.json`. Radius and ulna remain distinct/unselected; PRUJ/DRUJ and pronation-axis contact requirements persist. Source/statute-owner rules, talus exclusion, C2 dispersion quarantine, mandible quarantine, Rausch endpoints, source aliases and hyoid corrections are preserved. This review does not undo Claude's owner-approved decisions or promote freeze_ready.

Verification: 5 limb, 5 owner-policy/source-fix and 7 source-identity tests pass; target/atlas structural validators pass. Full discovery: 805 tests, unchanged 5 failures/4 errors from the previous checkpoint; no new remaining failures. Logs and SHA256 manifest: `ORIGINAL_V1_WORK/anatomy/audit/runs/work_limb_primary_review_20261008_001/`. No numerical radius/ulna selection or anatomical gate promotion.

### 2026-10-08 independent forearm landmark review

- STRONGLY SUPPORTED: named radial/ulnar articular and surface landmarks, neutral radial-head → ulnar-head reference, and distinct DRUJ notch projection versus wrist centre are now recorded in `canonical_forearm_landmark_requirements_v1.json`. Coordinates and bone lengths remain unselected.
- Hong 2021 supplementary workbook downloaded/read without alteration. Both bone sheets contain 132 matched donor IDs; IDs imply 75 M/57 F, conflicting with manuscript 71 male/61 female. Length headers say mm2 although the paper describes linear mm. No individual stature field identified. These issues are recorded, not silently corrected or converted into a 1.82 m target.
- Adversarial geometry check: the three-point sphere-fit wording in Thillemann 2021 cannot determine a unique 3D centre without extra constraints. Three different sphere centres reproduce the same synthetic points exactly; a small residual alone must not validate an anatomical centre. No builder/production fitting algorithm was changed.
- Source register adds two primary papers; existing source aliases and owner fixes are preserved. The numerical forearm selection remains BLOCKED by matched surface/centre geometry and stature context. Evidence: `audit/runs/work_forearm_landmark_review_20261008_001/`.

Affected verification: 5 owner-policy/source-fix, 7 bibliographic identity and 5 freeze-readiness tests pass; target-data validator reports no errors with the required not-freeze-ready warning. Source register now 113 records / 108 identifier groups / unchanged 5 alias groups and 11 missing-identifier records. No movement/Blender rerun required for this evidence-only checkpoint; prior full-suite failures remain explicitly open.

### 2026-10-08 original shoulder archive acquired and C2 reread

- CONFIRMED acquisition: Seth's original Stanford archive is publicly downloadable in Work, including the generic shoulder .osim and three subject models. SC is explicitly relative to the thorax/IJ origin; source coordinates, AC constraint points and GH reference are recorded with SHA256 in `canonical_sc_primary_model_reference_v1.json`. The model download is no longer laptop-only. Anatomical target selection remains PROVISIONAL: dimensions derive from Holzbaur 2005 and are not independent 1.82 m male evidence. No global SC target or production geometry selected.
- C2 primary Table 2 explicitly labels its dispersion SD. Calling it SE is an unconfirmed interpretation. The reported sex-specific means/SDs and pooled upper range cannot coexist: the single largest measurement needs more squared residual than both group SDs permit together. Kept Claude's usable SD quarantine and extended it to the source register, which still exposed 0.66 under `sd`. Printed label/value remain beside the value. Details: `canonical_c2_primary_dispersion_review_v1.json`. No C2 height/target/stack changed.

Verification: 6 owner-policy/source-fix and 7 bibliographic identity tests pass; target validator no errors with required freeze block. Full suite 806 tests retains the same 5 failures/4 errors, no new failures. Logs/manifest: `audit/runs/work_primary_shoulder_c2_review_20261008_001/`. Anatomical gates remain open.

### 2026-10-08 source shoulder frame-transfer checkpoint

The original Seth model body basis differs by 7.8584° from its own IJ/C7/PX/T8-derived thorax frame. A direct model-XYZ → ISB mapping displaces SC by 1.28585 mm. `map_between_thorax_frames` now performs source inverse-frame then target-frame rigid transfer, without scaling. SC source-frame coordinates and reconstruction evidence are recorded; no global canonical SC target selected. Six frame tests pass. Fresh bpy 5.2.1 LTS quaternion-parent verification checks bilateral signs in a synthetic pose; no anatomical Blender candidate created. Full suite: 808 tests, same 5 failures/4 errors, no new failures. Evidence/retained failed runs: `audit/runs/work_sc_frame_transfer_20261008_001/`.

### 2026-10-08 foot source acquisition and Blender inspection

- CONFIRMED acquisition: Zenodo 3464747 metadata and eight files downloaded in Work, repository MD5 and SHA256 verified. A matched M02 left calcaneus/talus/M1/grouped-midfoot set imports in bpy 5.2.1 LTS. Download is no longer laptop-only. No anatomical master, production geometry or .blend candidate changed.
- BLOCKED contact mapping: source methods transform segments individually; native common-foot transforms are not in the four filename lists. STL physical units and this case's sex/stature are not established. The grouped midfoot represents nine named bones, but this import has eight large components plus small fragments (28 components total). Components cannot be silently counted as named bones or cleaned into a complete 206-bone target. No length/contact selected. See `canonical_zenodo_foot_source_access_review_v1.json`.
- Other acquisition recheck: Brown carpal project page is accessible but actual dataset download requires SimTK sign-in. RibSeg v2 binary pages show sign-in; public quality document lists missing/incomplete ribs and labeling exceptions. Storage shape alone is insufficient completeness evidence. Laptop actions are recorded in `audit/runs/work_zenodo_foot_source_20261008_001/carpal_rib_access_recheck.json`.

Foot source checkpoint verification: 6 owner-policy, 7 source-identity and 5 readiness tests pass; target validator reports no errors and retains freeze_ready=false. Native Blender import preserves every source float32 vertex and triangle geometry in all four STLs. Retained initial bbox-only run demonstrates the weaker check; full geometry comparison replaces it. Audit run: `work_zenodo_foot_source_20261008_001`. No canonical candidate or movement acceptance is claimed.

### 2026-10-08 laptop source-only Blender pickup

CONFIRMED source-only Blender inspection file created in `audit/runs/work_foot_source_blender_pickup_20261008_001/`: four separate Grant/Zenodo sample scenes and four visibly labelled renders. Save/reload mesh hashes preserve all coordinates/polygon indices; original source hashes retained. No rig, canonical candidate, a003 or production changes. Units/common pose/contact centres remain UNVERIFIED. The owner can inspect actual acquired source geometry on the laptop without mistaking it for the rebuilt skeleton. Li 2012 full-table retry: publisher routes returned 403/402; bilateral-clavicle numerical distance and endpoint definition remain BLOCKED. Abstract joint spaces cannot supply SC-centre breadth.

### 2026-10-08 hyoid landmark semantics reopened

CONFIRMED primary figure/text endpoint conflict recorded in `canonical_hyoid_landmark_semantics_review_v1.json`. Figure 1B marks D/E at free horn tips and Dprime/Eprime near the body; the source table calls Dprime-Eprime a posterior-end span. Printed values remain preserved, but unresolved posterior-end and centre spans are removed from provisional coordinate nominals. GGprime is not a proven volume-centroid span. Do not bend horns to reproduce these marginal means. Whole hyoid geometry remains PROVISIONAL; existing corrected body axes and one suspended-bone topology retained. The old local READY wording is removed.

Verification: new semantic regression fails against the preceding target despite six old tests passing. After correction, 37 affected tests pass; full 809-test suite has the same 5 failures and 4 errors as baseline. Target validator has no errors and retains freeze_ready=false. Logs and hashes: `audit/runs/work_hyoid_landmark_semantics_20261008_001/`. No coordinates, a003, production, Blender candidate or movement acceptance changed.

### 2026-10-08 original rib thesis obtained; printed notation conflict retained

CONFIRMED original Holcombe 2016 thesis acquired through the university's current advertised bitstream (24,996,572 bytes, SHA256 recorded). The old legacy route returned HTML despite HTTP 200; file type and rendered equations were checked. PDF access is no longer laptop-only. Eq2.18 is legible but lacks phi_pia in its second inequality despite describing a phi_pia upper-bound purpose. Eq2.16/2.17 mix row/column conventions; an independent zero-spiral-rate case exposes nonstationary peak behaviour under literal Eq2.11 with standard atan2. These are notation conflicts, not accepted corrections.

Full proximal curves remain BLOCKED pending verified intended conventions or an independently justified equivalent branch rule. Verified distal curves remain intact. 33 affected tests pass, target validator no errors/freeze_ready=false. No rib coordinates, contacts, new canonical candidate, a003 or production changes. Evidence: `audit/runs/work_rib_primary_equation_review_20261008_001/`; updated source derivation retains historical OCR limitation and the new primary review.

### Claude continuation, 8 October (after GPT live head 0f8e677c)

- **CP2:** a femur declared as an extra root, or a radius declared "carried" by the humerus or femur, still passed GPT's relation repair. Roots are now limited to one skeletal root plus non-articulating bones, and carriers to documented exceptions (malleus–temporal, sternum–thoracic) (`a5f35880`). a003 still passes the structure checks.
- **Humerus** (`canonical_humerus_target_review_v1.json`): the joint-span sources agree (ANSUR GH–EJC 286.2 ± 10.6 mm, de Leva 294.5 mm), and a003's 287.7 mm lies inside both. Through the humeral head radius (24–28.8 mm) and the distal allowance (10.7–13 mm), they imply a maximum length of 312–336 mm. That is consistent with Mall's 334 mm, but below the inverted Trotter–Gleser 359.5 mm: the same pattern as the thigh. Nothing is selected, and the region stays PARTIAL.
- **Sternum** (`canonical_sternum_target_review_v1.json`): male population ranges are recorded (manubrium 46–55 mm, body 95–108 mm, total including xiphoid 154 ± 13 mm). In the BodyParts3D layout (grade D), rib 2 sits at the sternal angle and every topology rule holds. **a003 sternum:** a 213 mm stick (z +4.5); rib 2 is 38.7 mm down while the manubriosternal marker is 76.1 mm down; spacing is uniform (schematic). Per-notch dimensions need the Selthofer 2006 full text (Hrčak is blocked from the cloud). The ribs/sternum region stays BLOCKED.
- **Accepted GPT corrections:** the scapula-height claim is withdrawn (only the AA–TS width defect is established); the de Leva shank endpoint is KJC–LMAL.
- **Thorax frame / CP1a** (`canonical_thorax_frame_182_review_v1.json`):
  - **ANSUR standing anchors at 1.82 m:** IJ (suprasternale) 1494.5 ± 11.7 mm, C7 1575.2 ± 11.2 mm, acromion 1497.7 ± 16.2 mm.
  - **Conflict:** living men put C7 80.7 ± 11.4 mm above IJ, but the Seth model frame (32.8 mm) and the BodyParts3D specimen (45.5 mm) do not. Standing thorax pitch therefore stays OPEN.
  - **SC:** the Seth SC is 7.2 mm anterior, 6.0 mm superior and 25.5 mm lateral of IJ (breadth 50.9 mm, now a primary-model value for the feasible family's assumed 50 mm). Provisional SC height is 1500.5 mm (band 1486–1514); it is IJ-dominated, with ±20° of pitch moving it by under 5 mm.
  - **a003:** IJ is 24.7 mm high (z +2.1) and SC 13.7 mm high; its SC breadth of 50.0 mm matches.
  - Nothing is selected.

### Claude shoulder stage, 8 October (after `1d87ead4`; audit candidate, nothing selected)

- **Solution** (`canonical_shoulder_girdle_solution_182_v1.json`, `1d87ead4`). Joint weighted least squares over Seth SC, Matsumura male standing CT, Qiu chord, Lee 182 cm scapula and the 2026 AC–lateral-acromion distance; published SDs only; χ² 3.38 on 2 dof, all |z| ≤ 1.06. Values are relative to the thorax:
  - clavicle joint-centre chord 151.3 mm;
  - clavicle elevation 9.8°, retraction 18.4°;
  - scapula internal rotation / upward rotation / anterior tilt 30.3° / 11.3° / 9.7°;
  - AC 39.7 mm from the lateral acromion;
  - AC–GH 41.3–44.7 mm (Seth 42.0).
  - Status PROVISIONAL, not frozen.
- **Audit candidate `r95_a003_shoulder_proposal_c001`** (`89a9c3d5`), in `ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_proposal_c001/` (see its README).
  - Built: a003 with the clavicles and scapulae replaced and each humerus subtree translated rigidly with GH; a separately named blend.
  - Integrity: a003 blend hash unchanged (`670a37bf…`); round trip PASS; CP2 verdicts identical to a003.
  - Status `AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED`.
- **Review evidence** (`07c7b5e0`), in `review/`. Identical-camera a003 vs c001 renders, every image captioned with identity and status:
  - 20 views: full body front/back/both sides/three-quarters, upper body front/back/overhead, and bilateral shoulder front/side/rear/overhead plus axilla;
  - 4 illustrative GH poses (bones only);
  - before/after pairs and contact sheets;
  - `manifest.json` with sha256 of every file.
- **Erratum and defect** (`12ed2774`, `audit/shoulder_vertical_relation_audit_v1.json`).
  - Withdrawn: the v1 reading's single-offset hypothesis. The C7 relation needs the living suprasternale 35–48 mm *below* the bony IJ; the acromion relation needs it 23.5 mm *above*.
  - Corrected: the readiness blocker's "same direction as the C7 conflict" wording now reads opposite direction.
  - IJ-independent: even at the living-implied pitch, the solved AC sits ≥ 35.7 mm higher relative to C7 than ANSUR acromion−cervicale (−77.5 mm).
  - **c001 known defect:** lateral acromion 63.0 mm above ANSUR acromial height at 1.82 m (z 3.89); the lowest variant is still +38.3 mm.
  - Status AUDIT_OPEN_NOT_RESOLVED.
- **Tests:** `scripts/test_shoulder_proposal_c001.py`, 15 tests covering identity and pinned hashes, scope of change, CP2 parity, solution match, mirror, the erratum sign check, defect recorded-not-passed, and manifest hashes.
- **Still open:**
  - absolute shoulder height relative to the trunk;
  - acromiale/cervicale skin-to-bone offsets;
  - standing chest/thorax pitch (bony 7.04° vs living-implied −11.3°; disagreement kept explicit);
  - forearm length (not applied here);
  - mesh refit.
- **Shoulder region:** stays PARTIAL. Do not move to ribs/feet as if the shoulder were closed; the next shoulder step needs a source that pairs skin acromiale/cervicale/suprasternale with bone, or an owner decision on which vertical anchor governs.

### Claude shoulder stage: ANSUR living-height anchor (c002), 8 October

- **Owner policy `SHOULDER_HEIGHT_ANCHOR_ANSUR_LIVING`**, recorded in `canonical_target_selection_v1.json` `owner_decisions`:
  - absolute shoulder height follows the living standing ANSUR survey;
  - internal clavicle length and orientation, scapular geometry and AC–GH stay those of the bony solution;
  - thorax pitch is a sensitivity variable;
  - caveat recorded: a modelling policy, not a settled skin-to-bone relation.
- **Audit candidate `r95_a003_shoulder_proposal_c002_ansur_height`** (`a3068b38`; index `ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_proposal_c002_ansur_height/README.md`).
  - Construction: the pinned c001 translated rigidly by **z −63.0 mm**, so Lee LM27 (lateral distal acromion) meets ANSUR II acromial height at 1.82 m (**1497.7 ± 16.2 mm**, recomputed from the raw 4,082-man CSV).
  - Uncertainty: the LM25 bracket is 14.2 mm; the skin-to-bone offset is not applied (unquantified, one-sided); the primary ANSUR landmark text was unreachable here, so secondary wording was used.
  - Integrity: round trip PASS; CP2 identical to a003; a003 and c001 hashes unchanged.
- **Shoulder closure: FAIL (blocker).**
  - c002's SC joints sit 56.2 mm below the retained a003 jugular notch, beyond the range of published male mean manubrium lengths (46–55.2 mm); the source relation puts SC 6.0 mm above IJ.
  - In all 8 recorded pitch × IJ × landmark variants, the SC ends 17–62 mm below its own notch.
  - With the bony clavicle orientation retained, the living acromial anchor and SC-on-manubrium cannot both hold.
  - **Owner decision or evidence needed:**
    - (a) lower the thorax/sternum with the girdle;
    - (b) accept clavicle elevation of about −4.8° (≈3.2 SD below Matsumura's 8 ± 4°; first-order estimate);
    - (c) obtain a source pairing skin acromiale with bone.
- **Evidence** (`b83d7b5a`): 80 captioned JPEGs (c001-vs-c002 and a003-vs-c002 pairs, c002 views and poses, contact sheets) with a sha256 manifest.
- **Tests** (`63732056`): `scripts/test_shoulder_proposal_c002.py`, 16 tests. Readiness: shoulder stays PARTIAL with an SC-closure blocker.
- **Naming:** the audit IDs `…shoulder_proposal_c001/c002` are unrelated to the reserved `HGPT_CANONICAL_SKELETON_FIRST_c001`, which has not been created (test-enforced).

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

### All-pairs unconnected bone-axis crossing scan (9 October, Claude; mechanical, no clearance claims)

- **What:** `scripts/anatomy_fit/all_pairs_crossing_scan.py` extends the earlier scan, which examined only the 6 nearest bones and excluded only parent/child pairs, to **all 20,747 unconnected pairs**. Connected pairs (368, sharing an articulation or parent/child) are excluded. It runs on all 135 sweeps of a003 and c003 with the documented 1 mm axis bound; near approaches under 3 mm are listed only.
- **Dynamic (identical on both):** the only crossings are **tibia_left × tibia_right** in hip abduction/adduction, the known unsourced 20° TEST AMPLITUDE defect (still unresolved). The earlier nearest-6 shortcut hid nothing.
- **Static (newly surfaced; identical on both):** the mandible and vomer axes cross at rest (0.09 mm).
  - Classified **REPRESENTATION_ARTEFACT**: the mandible stick is a chord from the condylar midpoint (a midline point between the TMJs, not on bone) to the mental region, passing through oral/pharyngeal space. The bound's premise, that the axis lies inside the bone, does not hold for chord sticks of U-shaped or curved bones (mandible, ribs).
  - No other unconnected pair touches at rest.
- **Evidence:** `audit/all_pairs_crossing_scan/{a003_isolated_014,c003_isolated_001}.json`.
- **Tests:** `scripts/test_all_pairs_crossing_scan.py` (3), including mutations: an injected static contact (phalanx tail on the femur) and an injected dynamic crossing (tibia shifted onto the opposite tibia) must both be detected.

### Joint reference-frame audit at rest and through all 135 sweeps (9 October, Claude): frames CLEAN; one candidate-specific provenance defect found

- **What:** `scripts/anatomy_fit/joint_frame_audit.py`, read-only, on a003 (run 014) and c003 (run `isolated_bone_only_c003_shoulder_thorax_001`).
  - **Rest:** every joint marker's `frame_axes_columns_XYZ` is checked for finiteness, orthonormality (≤ 1e-9) and right-handedness (det +1). For each bilateral pair, the left frame is reflected and one axis sign flipped; the best flip is the pair's mirror convention, and the residual angle is the **inherited rest asymmetry**. Conventions are grouped per joint family.
  - **Motion:** every 2-participant articulation, at every saved frame, is carried by its frame bone and checked for orthonormality and det (float32 bound 1e-5). For the 106 single-channel tests, the child-relative-to-parent rotation axis, expressed in the parent-carried joint frame, is tracked: **axis drift** (max angle from its mean), **sign flips** (frames rotating against the command), and the followed joint axis with its alignment angle (reported, not graded, because oblique axes exist by design).
- **Rest (a003 = c003):** 427 markers, 0 improper; 180 bilateral pairs; every family uses the Z-flip convention, **no mixed conventions**. Max rest asymmetry is **0.399°**, confined to toes (mtp_5, toe5_pip/dip; mtp_1 and hallux_ip 0.29°). This is the same toe-fit inheritance seen in the mirror-parity scan, kept separate from motion.
- **Motion:** 0 frame issues (worst orthonormality/det 1.5e-6 on a003, 2.0e-6 on c003); max axis drift 0.0002° (a003) and 0.00012° (c003); **0 sign flips**.
- **Candidate-specific difference, a new defect:** on c003, 10 hand/thumb entries (both sides) align differently with their joint axes than on a003. Examples: thumb CMC radial abduction 40.7° → 21.3°; digit 2/4/5 MCP abduction ≈ 2.6° → ≈ 20°. Legs and spine are identical.
  - **Root cause:** `isolated_tests.frames()` builds the hand test frame from `skeleton_input.sides[*]['WJC']`, and the forearm frame from EJC and the styloids. The c001, c002 and c003 builders moved the arm bones and joint markers with GH but **left EJC, WJC, humeroulnar, humeroradial and both styloid inputs at a003 values**.
  - WJC to radiocarpal marker: a003 0.0 mm; c001 74.2 mm; c002 47.0 mm; c003 38.4 mm. Each equals that candidate's GH shift.
  - Bones and markers are correct; only the derived hand/thumb test axes (and the forearm frame inputs) are stale.
  - **Disposition:** UNRESOLVED. Classified as a CANDIDATE_PROVENANCE_DEFECT. The committed c001, c002 and c003 are preserved unchanged. A fix requires a new named candidate revision that translates those inputs with GH and re-runs Phase 9. c003 remains an audit candidate.
- **Evidence:** `audit/joint_frame_audit/{a003_isolated_014,c003_isolated_001,candidate_input_consistency}.json` (produced by `scripts/anatomy_fit/candidate_input_consistency.py`).
- **Tests:** `scripts/test_joint_frame_audit.py` (9). Pins cover the results, the hand difference and the stale inputs. The mutation tests each inject one error, and each must be detected:
  - a reflected (det −1) rest frame;
  - a different but proper mirror convention within a family (mixed flip);
  - an unmirrorable pair (residual > 90°);
  - a 3° per-frame axis drift in knee flexion;
  - knee rotation reversed against the command (sign flip).

### Repository-wide evidence integrity: hashes, references and orphans (9 October, Claude; read-only, nothing rewritten)

- **What:** `scripts/anatomy_fit/evidence_integrity_audit.py`.
  - It walks every JSON under `ORIGINAL_V1_WORK/anatomy` and re-checks each recorded sha256 that a documented anchoring rule ties to a file. The rules cover `{path: hash}` maps, `{path: {sha256}}` maps, `X_sha256` with a sibling `X`, and `sha256` with a sibling `path`/`file`.
  - It also checks `*.sha256` sidecars, backtick file references in the tracker, findings, review, handoff and `REVIEW_PACK_INDEX.md`, and evidence files under `audit/` that nothing in the repository names.
  - When a hash mismatches, every committed version of the path is hashed to tell **stale** (recorded against an earlier committed version) from **mismatch** (no committed version matches).
- **Result: 1,006 anchored hash references**; 230 unanchored hashes (blend hashes after a run, digests) are counted but not graded.

  | Status | Count | Meaning |
  |---|---|---|
  | OK | 924 | Hash matches |
  | OK_VIA_GZIP | 7 | Only `X.gz` is committed; the decompressed content matches |
  | STALE_HISTORICAL | 39 | Script/provenance hashes recorded against earlier committed versions of scripts edited since (e.g. `joint_markers.py`, `isolated_tests.py`, the master builder); this includes the provenance of a002, a003, c001, c002 and c003 and isolated runs 002–014 |
  | MISMATCH | 12 | Script provenance in early isolated runs 001–011 matching no committed version of `run_isolated_tests_blender.py`, `isolated_tests.py` or `joint_solver.py`: recorded from uncommitted intermediate working copies, so those script states cannot be reproduced exactly from git |
  | ABSENT_BINARY_NOT_COMMITTED | 21 | Test blends of the a003 mirror-fix recheck and c001 runs, Zenodo foot STLs, BodyParts3D `.bin` chunks, the OpenSim shoulder model; provenance only, unverifiable here |
  | MISSING | 1 | BodyParts3D `atlas.json` (a third-party source file, never committed) |
  | EXTERNAL | 2 | Scratch or `/tmp` test blends |

  - **Sidecars:** both official-capture sidecars verify through their committed `.gz`.
  - **Document references:** 361 checked when the audit ran, **0 missing**; 5 are context-relative short forms that each resolve to tracked files.
  - **Orphans:** 5 files are named nowhere in the repository: two cross-check inputs of isolated run 001 and three files of the 8 October Claude review run. They are listed in the JSON and deliberately not named here, because naming them would hide them from the check. Another 39 are named only by their run directory's README/manifest context.
- **Disposition:** nothing was rewritten; accepted evidence and baselines are untouched. The MISMATCH, MISSING and orphan items are recorded as UNRESOLVED provenance gaps, not as failures of the evidence content.
- **Index:** `REVIEW_PACK_INDEX.md` now carries a repository-wide integrity section linking the JSON.
- **Evidence:** `audit/evidence_integrity/evidence_integrity_v1.json`.
- **Tests:** `scripts/test_evidence_integrity_audit.py` (4):
  - pins the findings;
  - live re-verification: no previously verified reference may degrade, and no document reference may go missing;
  - mutations on a synthetic git repository prove each status (OK, MISMATCH, STALE_HISTORICAL, MISSING, OK_VIA_GZIP, ABSENT_BINARY_NOT_COMMITTED, EXTERNAL), a tampered sidecar target, a missing and a context-relative document reference, and a stray orphan are each detected.

### Solver ↔ Blender cross-implementation agreement over all 135 sweeps (9 October, Claude): AGREE on a003 and c003

- **Why:** the Phase 9 runner keyframes a pose basis derived from the pure-Python solver, then records what Blender EVALUATES (keyframes, quaternion decomposition, parent composition through the depsgraph) and measures from that. Nothing had checked that Blender's evaluated motion is exactly the solver's intent. The integrity audit also found the solver scripts edited since run 014 (STALE_HISTORICAL provenance), so it was open whether today's code still reproduces the committed runs.
- **What:** `scripts/anatomy_fit/solver_blender_agreement.py`, pure Python and read-only. Rest matrices are rebuilt from the record (head; Y = head→tail, the only rest quantity `measure()` reads besides the delta). It checks three things:
  - **(A)** the committed command series equals today's `isolated_tests.series()`;
  - **(B)** every recorded evaluated delta equals the solver delta composed through its commanded ancestors;
  - **(C)** re-running `isolated_tests.measure()` reproduces every recorded numeric channel. Plane of elevation is skipped below 1° elevation, where it is undefined (the runner's own rule).
  - Bounds are numerical only: transforms 1e-5 (float32); angles 1.7e-3° (3 × 1e-5 rad); lengths 1e-5 m.
- **Result, a003 run 014:** 135 tests, 9,575 frames, 13,509 deltas, 49,991 channels. **AGREE**: no series drift; worst composed delta 8.0e-7; worst channel difference 5.5e-5°. The uncomposed reading (delta = solver delta alone) would differ by up to 1.99, so composition is genuinely exercised.
- **Result, c003 run 001:** 49,667 channels. **AGREE**: worst composed delta 1.4e-6; worst channel 2.0e-4° (GH plane).
- **Consequence:**
  - The script edits after run 014 did not change any test series, solver output or measurement; the committed runs are reproducible from the current code.
  - Blender's evaluation adds no hidden constraint, driver or interpolation effect on commanded bones.
  - Followers and carried descendants were covered separately by the mirror, attachment and crossing scans.
  - Nothing here changes Gate 9 (still NOT PASSED for coverage and source reasons).
- **Evidence:** `audit/solver_blender_agreement/{a003_isolated_014,c003_isolated_001}.json`.
- **Tests:** `scripts/test_solver_blender_agreement.py` (7). Mutations, each of which must be detected: a drifted command value, a corrupted evaluated delta (0.1 mm), a child delta stored without its ancestors, a measured channel corrupted by 0.01°, and a test absent from the current specs.

### c004: c003 with the six stale arm skeleton_input points resynchronised (9 October, Claude; audit candidate, not canonical)

- **What:** `audit/candidates/shoulder_thorax_c004_arm_inputs/` (`scripts/anatomy_fit/build_candidate_c004_arm_inputs.py`). It derives from c003 and changes only EJC, WJC, humeroulnar, humeroradial, ulnar_styloid_bone and radial_styloid_bone, on both sides.
  - Each point takes the c003 position of the reference it is *identical* to in a003: the joint marker for WJC, humeroulnar and humeroradial; the bone endpoint for EJC (humerus tail) and the styloids (ulna/radius tails).
  - No joint marker coincides with EJC or the styloids in a003 (the nearest are 9.4–17.8 mm away), so using a marker would have redefined those points. This is the one deviation from "joint-marker positions", and it is evidence-based.
  - Every new value is asserted to equal old + the side's GH translation (38.432 mm).
  - The per-point before/after table and hashes are in `candidate.arm_input_correction` and `correction_and_causality.json`.
- **Causality, pure Python:**
  - The record diff from c003 is exactly the 12 points.
  - The derived hand/forearm test frames now equal a003's to 8e-14° (c003 was off by up to 25.8°); all 148 other frames are identical.
  - Only 16 hand/thumb/wrist specs change. The wrist test pivot moves from 38.4 mm off the radiocarpal marker to 0.
- **Phase 9 rerun** (`runs/isolated_bone_only_c004_arm_inputs_001`, on the byte-identical c003 blend): 135/135 integrity and 41/43 mirror, the same as c003.
  - 111 sample sets are byte-identical to c003.
  - The 24 changed hand/thumb/wrist tests reproduce **a003's** rotations and measured angles within float32 bounds.
- **Requested criteria** (`validation_summary.json`): **MET**.
  - The wrist-centre gaps are closed.
  - Every hand/thumb axis alignment equals a003 (c003 had 10 deviations).
  - Bones, markers and ANSUR/SC acceptance checks are identical to c003.
  - Mirror, continuity, collision, all-pairs, state restoration, solver agreement and the CP3 round trip (report identical to c003's) are clean, and nothing changed outside the 24 corrected tests.
  - The a003/c001/c002/c003 sources are unchanged.
  - c004 remains `AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED`; Gate 9 is unchanged.
- **New finding: c003's wrist sweeps were mechanically wrong.** They rotated the carpus about the stale WJC, opening the radiocarpal joint by **16.687 mm** on both sides. c004 closes it to 0, as in a003. The committed v1 attachment scan missed this:
  - **Detector gap fixed:** `joint_attachment_scan.py` v1 skipped every articulation with a soft-tissue participant (59 of 427, including radiocarpal with its TFCC). The new `--v2` mode checks such joints on their bone participants (372 checkable). v1 outputs are preserved, and the v2 outputs are `joint_attachment_scan/{a003_isolated_014,c003_isolated_001,c004_isolated_001}_v2.json`.
  - Only radiocarpal is newly detected, and only on c003. The other 55 articulations have fewer than two bone participants and cannot be checked by this method.
- **Mirror-scan determinism fixed:** the `worst_*_bone` labels were tie-breaks taken in set order, which varies with `PYTHONHASHSEED`. The scan now iterates in sorted order; values were never affected.
- **Builder guard:** `scripts/anatomy_fit/skeleton_input_guard.py` records, for every skeleton_input point, the bone endpoints and markers it is identical to in the base, and requires the same in a derived candidate.
  - It flags EJC, WJC, humeroulnar, humeroradial, both styloids, `carpals` and `hand` in c001, c002 and c003.
  - On c004 it flags only `carpals` and `hand`. These are also stale but outside the requested six-point scope, and are read only by `skeleton_fit.py`, not by Phase 9. **UNRESOLVED.**
- **Renders:** none were made. The c003 pack is reused because every visual input is hash-identical (`review_reuse.json`; recorded in `REVIEW_PACK_INDEX.md`).
- **Tests:** `scripts/test_candidate_c004_arm_inputs.py` (14). They cover baseline hash pins, builder reproducibility and scope, causality, and guard mutations (a stale point re-injected; a bone moved without its input; a consistent rigid move passes except the shared tibia head). They also cover the run summary, the v1-missed/v2-detected radiocarpal opening, and mirror determinism under three hash seeds.
  - The evidence-integrity live test now admits a new non-OK reference only as an inherited duplicate of a recorded one (c004 inherits c003's stale provenance hashes).

### Remaining stale carpals/hand inputs: audited; source rebuild shows no defensible c005 (9 October, Claude; BLOCKER)

- **What:** `scripts/anatomy_fit/hand_input_source_rebuild_audit.py` → `audit/hand_input_audit/hand_input_source_rebuild_v1.json`. c004 stays preserved as a successful, non-canonical audit candidate.
- **Points and consumers:** `skeleton_input.sides.<side>.carpals.<8 carpals>` and `.hand.<mc1–5, th_pp, th_dp, d2–5_pp/mp/dp>` are [head, tail] pairs, 108 points in total. They are consumed **only** by `skeleton_fit.build`, one bone each; Phase 9 and the joint markers do not read them. All 108 are stale (equal to a003) in c001, c002, c003 and c004, while every corresponding c004 bone endpoint moved by exactly the side's GH shift.
- **Correspondence:**
  - **98 points** are identical to their a003 bone endpoint, so the correction (the c004 endpoint) is uniquely determined.
  - **10 points** (the distal-phalanx tails of digits 2–5 and the thumb, both sides) are *pre-containment stations*: `skeleton_fit.contain` pulled those bone tails 5.28–9.00 mm inside the a003 skin. c004 bones and markers encode only the post-containment endpoint, so these inputs are **not determined** without a further assumption.
- **Source rebuild** (pure Python, using the master builder's pipeline: build → enforce_midline → contain against the a003 body mesh exported by `export_body_mesh_blender.py`, 17,946 vertices / 35,888 triangles, as recorded):
  - a003 inputs reproduce **all a003 bones exactly**.
  - c004 inputs rebuild **a003's hand placement**: 54 carpal, metacarpal and phalanx bones are off by exactly 38.432 mm, so the hand is detached from c004's wrist.
  - Both candidate corrections (every point + GH shift; every point = its c004 endpoint) fail to rebuild c004, by up to **353 mm**.
- **Root blocker (new):** c003 and c004 translated the arm but the body mesh is a003's and unskinned. The c004 distal radius and ulna, the whole carpus and the hand lie **outside the a003 skin** (45 left-arm endpoints; a003 has none), so `contain()` relocates them in any rebuild.
  - c003/c004 hand geometry therefore cannot come from the source pipeline at all. It exists only as the rigid translation applied by the candidate builders.
- **Decision:** **NO c005.** Not every correction is an exact causal correspondence encoded by c004, and no correction is rebuild-equivalent. The blocker is recorded:
  - a c005 would need a decision on the fingertip pre-containment rule;
  - and either a skin/mesh that follows the c003 shoulder change or a candidate-specific exemption from containment.
  - Neither is invented here.
- **Tests:** `scripts/test_hand_input_source_rebuild.py` (6). They rebuild from skeleton_input rather than reusing the c003 blend:
  - a003 rebuilds itself;
  - c004's stale inputs rebuild a003's hand exactly, offset by the GH shift;
  - the classification is pinned;
  - mutations: a single moved carpal input is detected; correcting only the 98 exact points satisfies the guard and the mesh-free rebuild but not the full pipeline.

### Amplitude provenance of every commanded peak (9 October, Claude; next independent Phase 8–10 invariant): TRACED on a003, c003 and c004

- **Why:** the isolated tests must not invent movement magnitudes. Nothing had checked mechanically that every commanded extreme comes from a recorded basis rather than an unlabelled number.
- **What:** `scripts/anatomy_fit/amplitude_provenance_audit.py`, read-only. For each of the 135 tests, every channel's max and min (278 non-zero peaks) is classified by explicit rules only:

  | Class | Count | Rule |
  |---|---|---|
  | EXACT_CONTEXT | 100 | Equals an atlas observation **value** (never population text, sample sizes, CIs or SDs) |
  | HALF_OF_SOURCED_TOTAL | 76 | Twice the peak is a sourced value, and the basis states the split |
  | LABELLED_TEST_AMPLITUDE | 78 | Stated in a sentence that declares TEST AMPLITUDE, or a stated "−10% of the mean" reversal |
  | CONDITION_IN_TEST_ID | 10 | A held condition named in the test ID |
  | STATED_IN_BASIS | 8 | Stated in the spec's own basis text; the citation cannot be verified here |
  | TARGET_MINUS_FITTED_REST | 4 | Thumb CMC: clinical intermetacarpal mean minus the fitted rest angle, exact |
  | DRIVEN_TO_MEASURED_TARGET | 2 | Opposition palmar abduction |

  TEST AMPLITUDE statements take precedence over number matches. The glide is compared in mm.
- **Result:** **0 UNTRACED** on all three runs, and identical classes across them. Every thumb intermetacarpal target (62.9° / 61.2°) is **measured at peak** in each committed run, within 1e-5°.
- **Unsourced amplitudes, now explicit:** 78 of 278 peaks, across 49 tests, are labelled test amplitudes:
  - cervical C4/5 adduction and axial rotation;
  - digit hyperextension reversals;
  - GH elevation 120° and GH axial rotation ±50°;
  - hallux plantarflexion;
  - hip ab/adduction (+20/−30°, which also causes the known leg-crossing);
  - knee follower 90° and screw-home 60°;
  - rib 1–7 pump-handle 4.6°;
  - subtalar and talocrural extremes;
  - opposition pronation 30°;
  - TMJ.

  These remain UNRESOLVED as sources; nothing was changed.
- **Classifier errors found and fixed during the work** (each is a mutation test now):
  - a number merely restated beside a TEST AMPLITUDE label (the hip 20/30°) counted as traced;
  - coincidental matches to population text (e.g. "age 20–44") counted as context;
  - a key filter that dropped `mean`;
  - metres compared against millimetres.
- **Evidence:** `audit/amplitude_provenance/{a003_isolated_014,c003_isolated_001,c004_isolated_001}.json`.
- **Tests:** `scripts/test_amplitude_provenance_audit.py` (9). They pin the results and include these mutations: an untraceable peak; a split whose basis no longer states it; a removed TEST AMPLITUDE label; an inexact thumb rest angle; an unreached intermetacarpal target; a sample size used as a peak; a changed glide; and a TEST AMPLITUDE statement overriding a coincidental match.


### Work independent hand reconstruction review — 9 October 2026

- Live audit baseline `2d4b352c`; PR #8 head reviewed `8b56e876`.
- GitHub Actions `isolated-probe` succeeded at that head (run 37895321897).
- All eight original probe tests pass locally. Existing source-rebuild 6, c004 arm-input 14, hand-ray 3 and carpal 8 tests also pass.
- New independent audit imports neither the probe nor the builder: all 108 input/endpoint relationships checked, 98 exact and 10 unresolved distal tails. Six independent tests pass, including endpoint/marker mutations and NaN rejection.
- 27 mirror pairs: maximum residual 3.16e-12 mm. 28 digit seams: maximum 0.00007590 mm; digit marker-to-head residual 0.00006019 mm. These are stored-coordinate consistency results, not anatomical accuracy.
- 36 wrist-relative endpoint checks preserve a003 geometry through c004 translation. This does NOT validate carpal contact surfaces, centroids or wrist movement.
- Ten offsets are explicitly matched to recorded containment (5.28–9.00 mm); neither pre-containment nor post-containment tails are accepted canonical coordinates.
- Full pre-change discovery: 989 tests, five failures/four errors in inherited production-control/orchestration checks; exact names retained in `docs/WORK_SKELETON_DEVELOPMENT_20261009.md`.
- Stage 1 computational/provenance review complete; anatomical fingertip and carpal acceptance BLOCKED. PR remains draft/unmerged. No c005 or asset changes. Continue independent Stage 2 tooling while those anatomical blockers remain open.
- Evidence: `audit/hand_input_audit/work_independent_20261009/{coordinate_integrity,mesh_free_probe}.json`.


### Work Stage 2 construction contract — 9 October 2026

Separate `skeleton_first_builder.py` copies explicit skeletal endpoints/markers with no mesh-fit or containment dependency. It validates CP2 geometry, endpoint-defined length constraints and joint-participant attachment constraints, and exposes missing independent evidence/axes. a003/c004 replay retains 206 bones/427 markers exactly, while CP2 correctly remains FAIL (legacy spine discs). Skin clearance is non-mutating diagnostic only. 18 constructor tests plus seven independent hand tests pass after an independent reviewer identified three defects and RED/GREEN mutation verification corrected them. No canonical acceptance/promotion is possible in this module. Stage 2 engineering contract delivered, whole-body anatomical instantiation BLOCKED pending source coordinates and full contacts/envelopes. Gates 6/8/9 remain open.

### Work movement evidence queue and fresh mesh-free Blender replay — 9 October 2026

Read-only queue retains all 78 unsupported peaks across 49 tests/12 families. Seven queue tests pass after independent review exposed and RED/GREEN tests corrected untraced-peak omission and digit-family misclassification. Three primary evidence contexts are retained separately; no original amplitude, target or skeletal coordinate is changed.

Blender 5.2.1 restored with Python 3.13.16. Fresh c004 empty-scene construction retains 206 bones/427 markers and passes storage/reference-frame roundtrip; CP2 remains FAIL (known spine gap, contact envelope unverified). Fresh 135-test movement rehearsal: 135 integrity PASS, 41 Blender mirror PASS, two side-specific-amplitude pairs solver-only; current independent solver agrees over 9,575 frames/13,509 deltas/49,991 channels with zero discrepancies beyond declared numerical tolerance. Both blends, raw inputs/capture/samples and SHA256 are preserved in `audit/runs/work_fresh_c004_rehearsal_20261009/`.

Full post-review discovery: 1,021 tests, 1,012 pass, same named five failures/four errors as the initial 989-test baseline. PR #8 GitHub Actions passed at b0cb388d; no merge. Source, anatomical contact/proportion and visual acceptance remain incomplete; no c005/canonical promotion. Readiness 0 READY/9 PARTIAL/3 BLOCKED; Gates 6/8/9 unchanged. Read `WORK_SKELETON_PICKUP_20261009.md` for current review procedures and exact blockers. Laptop/interactive inspection remains useful, but source-ready anatomy rather than Blender installation is the principal construction blocker.


### Work primary fingertip recheck — 2026-10-09

Read-only distal-span context checks now trace runtime surface stations rather than assuming raw tips are validated skeleton endpoints. The official Aydinlioglu1998 Table5 and endpoint methods were independently rechecked; its legacy DOGAN source ID remains one publication. Raw distal spans differ from AP male means by4–11 source SD units, but projection/frame/population differences prevent diagnostic tolerances or replacement coordinates. Ten regression tests pass, including metadata-origin, stale-frame and nonfinite-derived-value rejection. All five a003/c001–c004 constructor replays preserve206bones/427markers exactly and retain CP2FAIL/no promotion. Full suite1031:1022pass,5fail,4error; same nine inherited names, trace retained. No accepted assets, limits or source values changed. See HAND_TIP_PRIMARY_RECHECK_20261009.md and audit/work_hand_tip_context_20261009. Ten distal endpoints and carpal contact geometry remain unresolved; no programme stage promoted.

### Claude independent anatomical investigation (9 October, branch `claude/skeleton-independent-verification-20261009`)

- Work's 9 commits were reproduced independently: the 1,031-test suite, the fresh skeleton-only Blender rehearsal (135 sample sets byte-identical to Claude's c004 run), hand 108/98/10 and 78 test amplitudes.
- **All 206 bones audited** on a003 and c004. **30 suspected problems classified** in `audit/claude_independent_review_20261009/skeleton_defect_register_v1.json`:

  | Class | Count |
  |---|---|
  | Genuine geometry defects | 4 |
  | Joint/coordinate defects | 3 |
  | Structural invariant failures | 1 |
  | Movement-test design defects | 4 |
  | Movement-model gaps | 3 |
  | Representation limits | 5 |
  | Evidence gaps | 5 |
  | Not defects | 5 |

  Highlights:
  - **Genuine:** M2–M4 short (two sources); zero disc spaces (CP2); thumb CMC 10.6 mm gap; calcaneocuboid/talonavicular centres 33–38 mm off their bones; radius short; a003 clavicle/scapula/shoulder breadth (corrected in c003/c004).
  - **Visualisation only:** straight ribs, floating femoral heads (hip centre exact; os coxae drawn as a chord), skull sticks, carpal stubs.
  - **New whole-body finding:** with c004's realistic shoulder width, isolated hand, forearm and GH-rotation sweeps from the hanging posture drive the hand into the thigh (a003's over-wide shoulders hid this).
- **Diagnostic proposal P001** (`audit/proposals/p001_metacarpal_m2_m4`): M2–M4 at the male radiographic means with fixed CMC ends. All 135 sweeps run, every check clean, before/after renders made. **Not a candidate**; carpal/CMC geometry still blocks a freeze.
- **Spine:** the sourced body+disc stack is 89.6 mm shorter than the C3–L5 sticks. The current thoracic span agrees with the CT source within 3.4%. The full sagittal stack rebuild remains sequence item 2; no local patch applied.
- Real Blender renders: a first pass (28 views, including 8 movement extremes) and an annotated pass with axes, scale bar, labels and an automatic camera check.
- **Readiness unchanged: 0 READY / 9 PARTIAL / 3 BLOCKED** (`readiness_review_addendum_20261009.json`). No c005; nothing promoted.

### 2026-10-09 (Claude, anatomical development continuation; branch `claude/skeleton-anatomical-development-20261009`)
- **Spine:** ANSUR-closed column length rejects thoracic source A (it would need a 1.43–1.49 m cohort). Source B with male MRI edge lumbar heights fits. Trunk closure on c004: lumbar +43 mm long; T12/L1 +38.5 mm, rib 10 +28.0 mm and IJ +24.7 mm high (new U10, coupled, BLOCKED). The curve-preserving disc re-partition P003 was rejected by the rib-level rule.
- **Knee:** a static patella stretches the patellar ligament by 114%; the Rajagopal follower template keeps it within 9.4% (L3 quantified; not installed).
- **Hip and hand:** the hip-adduction test needs at least 10–14° contralateral abduction (L4). Finger grip capacity: no defect (H10).
- **Shoulder:** the missing clavicular elevation (MoBL 0.1025°/°) leaves the AC 24–45 mm low overhead (U3).
- **PR #12:** reviewed, not merged. Its registration check is circular (a mesh 5 m away passes). A bone-geometry specification for eight regions was added.
- **Status:** readiness unchanged at 0/9/3. Details: `docs/CLAUDE_ANATOMICAL_DEVELOPMENT_20261009.md`.

### 2026-10-09 (Claude, coupled trunk experiment T001; branch `claude/coupled-trunk-rebuild-20261009`)
- **T001 (isolated experiment, not a candidate):** the sourced C2–S1 bodies and discs close between the fixed sacrum and C2 at Hasegawa-mean curvature (all z < 0.5, scale 0.998).
- **Outcomes:** discs all positive (CP2 0 FAIL); T12/L1 moves from +38.5 to +6.2 mm; rib levels preserved; girdle and arms unchanged; 60 spine/rib tests changed, all others identical.
- **Open:** C7 sits about 11 mm lower against ANSUR, the thoracic shape is unsourced, and rib inclination has no source.
- **Erratum:** the earlier "IJ +24.7 mm" residual used a stale a003 skin input; c004's bony IJ is already at ANSUR.
- **Readiness:** unchanged at 0/9/3.

### 2026-10-09 Integration checkpoint (Claude) — authorized branch `codex/whole-body-biomechanics-audit-20261007`
- **Integrity correction (owner):** the only authorized target branch is `codex/whole-body-biomechanics-audit-20261007`. Earlier Claude work had been pushed to `claude/*` branches. Those branches are preserved, not deleted.
- **Source:** `claude/coupled-trunk-rebuild-20261009` @ `de8d521bca94b826234a36a44fd3ea9243646d1f`, 24 commits. They include Work's skeleton-first regional verification up to `42943652`, Claude's independent verification (`96bc7420`…`f83e6ab3`), anatomical development (`e5c135ac`…`f3f725f4`), T001 (`82aec54d`) and the PR #12 re-check (`de8d521b`).
- **Destination:** `codex/whole-body-biomechanics-audit-20261007` @ `2d4b352c30ebc092eb167832d727a529cd18fef6`.
  - That branch had no newer commits, so there were no conflicts and nothing was discarded.
  - Integrated by a non-fast-forward merge commit `f864e50d`; no rebase, no reset, no force-push.
- **Scope check:** 202 files changed; the only existing files modified are this tracker (append-only) and `evidence_integrity_audit.py` and its test (external-URL classification). No production, a003, c001–c004 or `.blend` file was touched.
- **Verification on the merged tree:**
  - `test_evidence_integrity_audit`: OK;
  - `test_t001_coupled_trunk` (7 tests): OK;
  - `test_spine_trunk_audits` (13 tests): OK.
  - The last full suite before integration ran 1,064 tests with 1,054 passing; the 9 inherited production-control failures are unchanged, and the tenth (a render manifest) was fixed.
- **Status unchanged:** readiness 0 READY / 9 PARTIAL / 3 BLOCKED. T001 and P001 stay experimental/diagnostic; no candidate was promoted and no c005 exists.
- **Handover and review documents on this branch:**
  - `docs/CLAUDE_SKELETON_INDEPENDENT_VERIFICATION_20261009.md`;
  - `docs/CLAUDE_ANATOMICAL_DEVELOPMENT_20261009.md` (includes the erratum and the T001 summary);
  - `ORIGINAL_V1_WORK/anatomy/audit/experiments/t001_coupled_trunk/README.md`.

### 2026-10-09 Follower verification on c004 (Claude; verification only, no record changed)
- **Evidence:** `ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/follower_verification_c004_v1.json`, from `scripts/anatomy_fit/follower_verification.py`; tests in `scripts/test_follower_verification.py` (5).
- **Kneecap** (`knee_flexion_with_patellar_follower`):
  - observed patellar rotation equals the sourced ratio 0.66 × knee flexion within 9e-5°;
  - left/right symmetric within 2e-5°;
  - patella-to-femur/tibia axis clearance at least 40.9 mm.
  - **UNRESOLVED:** the follower is rotation-only (the translation path is unsourced), so the patellar ligament still lengthens by up to 23.3 mm (+43%), against +62.7 mm (+114%) in plain flexion with a static patella.
- **Shoulder girdle** (`shoulder_complex_scapular_plane`):
  - scapular upward rotation, tilt and external rotation, plus clavicle posterior rotation and retraction, all match the committed rhythm within 5e-5°;
  - the SC head does not move; AC closure is at most 0.00015 mm; the GH–AC distance stays constant at 41.29 mm;
  - left/right symmetric;
  - minimum axis clearance is 6.6 mm for clavicle to ribs 1–2.
  - **UNRESOLVED (U3):** clavicle elevation stays at 0° up to 170° of humerothoracic elevation, because no follower is applied and the sources conflict.
- **Status:** no collision or disconnection regression; the 9 inherited production-control failures are separate and unchanged.

### 2026-10-09 Follower source audit (Claude; documentation/evidence only)
- **Evidence:** `ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/follower_source_matrix_v1.json`, from `scripts/anatomy_fit/follower_source_matrix.py`; tests in `scripts/test_follower_source_matrix.py` (4).
- **Patella:**
  - the only primary source is the repository's lunge ratio (0.66, linear, rotation only, no translation);
  - the official models (Rajagopal 2016, MyoLegs within 0.14 mm of it, and Gait2392 credits) share one Delp / Yamaguchi–Zajac lineage;
  - Rajagopal's rotation is non-linear: cumulative 0.67 at 50° and 0.85 at 120°, which **conflicts** with 0.66.
  - **E-PAT-1** is proposed as a future named experiment only: the Rajagopal translation, scaled by femur length, tested with two rotation arms. Nothing is adopted.
- **Clavicle:** **E-CLAV-1 is UNRESOLVED; no relation is proposed.**
  - MoBL elevation (0.1025°/°, 17.2° at 168° HT) exceeds the repository's "below 10°" bound above about 98°.
  - MoBL retraction (−40.7° at 168°) conflicts with the repository's 15° end value.
  - No primary bone-pin table is reachable.

### 2026-10-09 H6 hand–thigh start posture quantified (Claude; test-design evidence only)
- **Evidence:** `ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/hand_thigh_start_posture_c004_v1.json`, from `scripts/anatomy_fit/hand_thigh_start_posture.py`; tests in `scripts/test_hand_thigh_start_posture.py` (4).
- **Method:** the committed c004 sweeps, preceded by a GH-only start abduction α of the whole arm.
- **Consistency:** α = 0 reproduces the interaction scan exactly (1.49 / 3.67 / 5.39 / 6.89 mm).
- **Result:** α ≥ 7° gives at least 10 mm and α ≥ 9° at least 25 mm axis distance from the femur and hip bone in every affected sweep, on both sides. Wrist flexion is the binding test.
- **H6** moves from OPEN to QUANTIFIED (test redesign pending; amplitudes unchanged; the start posture's scapular participation is to be stated).
- **Unchanged:** no model, record or test changed.

### 2026-10-09 L7 hip-rotation start posture quantified (Claude; test-design evidence only)
- **Evidence:** `ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/hip_rotation_start_posture_c004_v1.json`, from `scripts/anatomy_fit/hip_rotation_start_posture.py`; tests in `scripts/test_hip_rotation_start_posture.py` (3).
- **Consistency:** β = 0 reproduces the interaction scan (1.40 / 1.74 mm, hallux against the opposite first metatarsal).
- **Result:** abducting the opposite hip by β ≥ 3° gives at least 10 mm, and β ≥ 4° at least 25 mm, bone-axis distance in `hip_rotation_at_0_flexion` on both sides. `hip_rotation_at_90_flexion` is already clear (133.7 mm).
- **L7** moves from OPEN to QUANTIFIED (test redesign pending; amplitudes unchanged; bone-axis proxy only).
- **Unchanged:** no model, record or test changed; H6 stays QUANTIFIED.

### 2026-10-09 Session stop (Claude): blocker matrix
- **Blocker matrix:** `ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/blocker_matrix_v1.json`, covering 11 rows. Every remaining open item needs bone surfaces, primary literature, a contact model or an owner decision.
- **Exact next item:** E-PAT-1 (named patellar experiment), which needs an owner/GPT decision; otherwise, literature acquisition.
- **Handoff:** `docs/CLAUDE_ANATOMICAL_DEVELOPMENT_20261009.md` (session-stop section).
