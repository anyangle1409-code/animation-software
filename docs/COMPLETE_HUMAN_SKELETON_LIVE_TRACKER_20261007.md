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
- [ ] ❌ Verify bilateral symmetry and segment lengths. Symmetry PASS (0.38 mm). Segment lengths FAIL: humerus −13.2 cm and femur −10.0 cm against Trotter–Gleser stature (F-PROP-001); owner decision required.
- [x] ✅ Verify no distinct anatomical joint centres are accidentally collapsed. AC–GH 41.8 mm, talocrural–subtalar 31 mm; no two of the 427 markers are within 0.1 mm.
Gate 6: ⛔ NOT PASSED. The fit is produced and verified, but the femur/humerus proportion conflict (F-PROP-001, F-HJC-001, F-GH-001) needs an owner decision. Placement accuracy for proportional bones is low.

## PHASE 7 — BUILD HGPT_ANATOMICAL_MASTER
- [x] ✅ Create complete anatomical armature/reference collection. `HGPT_ANATOMICAL_MASTER` in `HGPT_ANATOMICAL_REFERENCE`, audit file a002 (`f172720b…`).
- [x] ✅ Represent every conventional adult bone. Independent capture: coverage 206/206 and identity PASS.
- [x] ✅ Tag each bone ACTIVE / FOLLOWER / FIXED / REFERENCE (92 / 87 / 26 / 1), as Blender custom properties.
- [x] ✅ Add required non-deforming anatomical landmarks/joint frames: 427 joint markers and 51 landmarks, round trip ≤ 2.9e-7 m.
- [x] ✅ Validate hierarchy, naming and symmetry. 201 articular parents, 3 explicit carriers, 2 roots; no cycles; symmetry PASS.
Gate 7: 🟡 STRUCTURE VERIFIED. Not passed for placement while Gate 6 is not passed.

## PHASE 8 — JOINT SOLVERS
- [ ] ⛔ Spine / cervical solvers.
- [ ] ⛔ Shoulder-complex solver.
- [ ] ⛔ Elbow / forearm solver.
- [ ] ⛔ Wrist / hand / thumb / finger solver.
- [ ] ⛔ Hip / pelvis solver.
- [ ] ⛔ Knee / patella solver.
- [ ] ⛔ Ankle / hindfoot / forefoot / toe solver.
Requires Blender for final validation, although solver specifications can be written earlier.
Gate 8: ⛔ BLOCKED FOR FINAL PASS

## PHASE 9 — ISOLATED BONE-ONLY MOVEMENT TESTS
- [ ] ⛔ Neutral → intermediate → near-limit sweeps.
- [ ] ⛔ Both sides.
- [ ] ⛔ Ascent / descent / reversal.
- [ ] ⛔ Multi-plane and coupled motions.
- [ ] ⛔ Joint-centre trajectory checks.
- [ ] ⛔ Continuity / acceleration checks.
Requires Blender/laptop.
Gate 9: ⛔ BLOCKED

## PHASE 10 — WHOLE-BODY FUNCTIONAL MOVEMENT TESTS
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
Done: Phase 6 fit and Phase 7 master structure on the r95 audit copy (a002). Gate 6 is not passed (F-PROP-001); Gate 7 structure is verified.
Next: Phase 8 joint-solver specifications and isolated tests on the a002 master (audit only).
Gates 6–13 remain unpassed.
Production model, recovery work, geometry, weights and motion drivers unchanged.
Comprehensive findings, source register, verification and local acceptance checklist: `docs/COMPLETE_SKELETON_FINDINGS_AND_VERIFICATION_20261007.md`.

Local validation preparation is available in `docs/BLENDER_ANATOMICAL_VALIDATION_HANDOFF_20261007.md`: read-only capture, source-bound test requests and offline numerical reports. Prepared tools do not complete Gates6–10; their Blender adapter still requires a local smoke test.
