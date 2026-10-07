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
- [ ] 🟡 Create machine-readable conventional adult bone inventory.
- [ ] ⬜ Verify total conventional count = 206.
- [ ] ⬜ Classify every bone: axial/appendicular, region, side, paired/unpaired.
- [ ] ⬜ Mark fused adult structures explicitly (e.g. sacrum, coccyx, hip bones).
- [ ] ⬜ Add anatomical aliases needed by Blender/code.
- [ ] ⬜ Check for zero missing/duplicate bones.
Gate 1: ⬜ NOT PASSED

## PHASE 2 — COMPLETE ARTICULATION / JOINT INVENTORY
- [ ] ⬜ Map every mechanically relevant articulation between the bones.
- [ ] ⬜ Classify joint type: synovial/fibrous/cartilaginous/functional.
- [ ] ⬜ Mark joints with effectively zero adult exercise-motion DOF.
- [ ] ⬜ Mark joints requiring active/follower mechanics.
- [ ] ⬜ Explicitly cover skull/TMJ, spine, ribs, SI, shoulder, elbow, forearm, wrist, hand, hip, knee, tib-fib, ankle, foot and toes.
- [ ] ⬜ Check for zero unclassified articulations.
Gate 2: ⬜ NOT PASSED

## PHASE 3 — ANATOMICAL LANDMARK / JOINT-FRAME ATLAS
- [ ] ⬜ Define landmarks for skull/cervical spine.
- [ ] ⬜ Define thoracic/lumbar/sacral and rib-cage landmarks.
- [ ] ⬜ Define SC/AC/scapula/GH landmarks.
- [ ] ⬜ Define elbow/radius/ulna/wrist landmarks.
- [ ] ⬜ Define hand/thumb/finger landmarks.
- [ ] ⬜ Define pelvis/hip landmarks.
- [ ] ⬜ Define femoral condyle/patella/tibial landmarks.
- [ ] ⬜ Define malleoli/talus/calcaneus/forefoot/toe landmarks.
- [ ] ⬜ Adopt consistent joint coordinate conventions.
Gate 3: ⬜ NOT PASSED

## PHASE 4 — WHOLE-BODY MOVEMENT / ROM EVIDENCE ATLAS
For every moving articulation record: axes, DOF, active/passive ROM, coupling, translations, posture/load dependence, movement-plane dependence, source, confidence.
- [ ] ⬜ TMJ / skull.
- [ ] ⬜ C0-C1 / C1-C2 / C2-C7 cervical spine.
- [ ] ⬜ Thoracic spine.
- [ ] ⬜ Lumbar spine.
- [ ] ⬜ Sacroiliac / pelvis.
- [ ] 🟡 Shoulder complex: SC / AC / scapulothoracic / GH.
- [ ] ⬜ Elbow.
- [ ] ⬜ Proximal + distal radioulnar / forearm.
- [ ] ⬜ Wrist / carpal functional stages.
- [ ] ⬜ Thumb.
- [ ] ⬜ Fingers / metacarpals.
- [ ] ⬜ Hip including rotation at different flexion angles.
- [ ] ⬜ Knee including translation / screw-home.
- [ ] ⬜ Patellofemoral tracking.
- [ ] ⬜ Tibiofibular mechanics.
- [ ] ⬜ Talocrural ankle.
- [ ] ⬜ Subtalar / hindfoot.
- [ ] ⬜ Midfoot / forefoot.
- [ ] ⬜ Hallux / lesser toes.
Gate 4: ⬜ NOT PASSED

## PHASE 5 — CURRENT RIG VS ANATOMICAL MASTER GAP ANALYSIS
- [ ] 🟡 Shoulder gap analysis.
- [ ] ⬜ Neck/spine gap analysis.
- [ ] ⬜ Elbow/forearm gap analysis.
- [ ] ⬜ Wrist/hand/thumb/fingers gap analysis.
- [ ] ⬜ Pelvis/hip gap analysis.
- [ ] ⬜ Knee/patella gap analysis.
- [ ] ⬜ Ankle/foot/toe gap analysis.
- [ ] ⬜ Produce one final “real anatomy vs current rig vs required change” matrix.
Gate 5: ⬜ NOT PASSED

## PHASE 6 — CHARACTER-SPECIFIC FITTING
- [ ] ⛔ Fit complete skeleton to HomeGymPT_Male_ORIGINAL_v1 proportions.
- [ ] ⛔ Place joint centres from character landmarks.
- [ ] ⛔ Verify bilateral symmetry and segment lengths.
- [ ] ⛔ Verify no distinct anatomical joint centres are accidentally collapsed.
Requires Blender/laptop.
Gate 6: ⛔ BLOCKED

## PHASE 7 — BUILD HGPT_ANATOMICAL_MASTER
- [ ] ⛔ Create complete anatomical armature/reference collection.
- [ ] ⛔ Represent every conventional adult bone.
- [ ] ⛔ Tag each bone ACTIVE / FOLLOWER / FIXED / REFERENCE.
- [ ] ⛔ Add required non-deforming anatomical landmarks/joint frames.
- [ ] ⛔ Validate hierarchy, naming and symmetry.
Requires Blender/laptop.
Gate 7: ⛔ BLOCKED

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
Completed: Phase 0.
Active now: Phase 1 complete bone inventory + Phase 4 shoulder evidence + Phase 5 shoulder gap analysis.
Next hard gate: Gate 1 — prove the complete conventional adult bone inventory has exactly 206 entries with no duplicates or omissions.
