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
- [ ] 🟡 Verify bilateral symmetry and segment lengths. Symmetry PASS (0.38 mm). Stature-equation check still recorded FAIL, but the same chain run on 4,082 ANSUR II men shows a method bias (femur −6.4 cm, humerus −9.7 cm). The character's femur and humerus fall at the 26th and 20th percentiles of real men, while HJC, KJC, elbow and GH depth match independent ANSUR / open-model references within 2–10 mm. The forearm and hand are genuinely short on the authored body (z −2.2): a character-specific limitation, not a fit error. See the findings section “F-PROP-001 / F-GH-001 / F-HJC-001 investigation”. No a004; a003 retained.
- [x] ✅ Verify no distinct anatomical joint centres are accidentally collapsed. AC–GH 41.8 mm, talocrural–subtalar 31 mm; no two of the 427 markers are within 0.1 mm.
Gate 6: ⛔ NOT PASSED. The femur/humerus conflict is now explained as stature-equation method bias, with independent corroboration of the HJC, KJC, elbow and GH. OWNER DECISION 2026-10-08: do not treat the short forearm/hand or long feet as intended final styling. The anatomical skeleton is the source of truth; the production mesh/skin will later be refit around validated skeletal proportions. The current a003 fit remains an audit baseline only. Gate 6 remains open because canonical target proportions must be set independently of the r95 mesh and 115 proportional bone placements remain low confidence.

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
Completed: Phases 0–5 (reference definitions, evidence compilation and static gap comparison); Blender toolchain verification.
Done: Phase 6 fit and Phase 7 master structure (fit revision a003); Phase 8 solver core; Phase 9 isolated tests (135, run 014).
Not passed: Gate 6 (proportion conflict needs an owner decision), Gate 8 (followers/contacts), Gate 9 (coverage).
Next: continue implementing remaining followers where defensible source magnitudes can be obtained; define and verify canonical skeleton-first target proportions independently of the r95 mesh; retain a003 only as the comparison baseline; then complete Gate 9 and run Phase 10 from authored exercise definitions. Production mesh reshaping waits until the validated skeleton target is frozen.
Morning review pack (current a003, read-only renders, links, hashes, defects, owner questions): `ORIGINAL_V1_WORK/anatomy/review_pack_a003_20261007/README.md`.
Resume: see the "Resume instructions" section of `docs/BLENDER_ANATOMICAL_VALIDATION_HANDOFF_20261007.md`.
Gates 6–13 remain unpassed.
Production model, recovery work, geometry, weights and motion drivers unchanged.
Comprehensive findings, source register, verification and local acceptance checklist: `docs/COMPLETE_SKELETON_FINDINGS_AND_VERIFICATION_20261007.md`.

Local validation preparation is available in `docs/BLENDER_ANATOMICAL_VALIDATION_HANDOFF_20261007.md`: read-only capture, source-bound test requests and offline numerical reports. Prepared tools do not complete Gates 6–10. The Blender adapter passed a live smoke test here (Blender 5.2.1 `bpy`, runs `blender_smoke_001`/`002`); a laptop run with the Blender application is still advisable.
