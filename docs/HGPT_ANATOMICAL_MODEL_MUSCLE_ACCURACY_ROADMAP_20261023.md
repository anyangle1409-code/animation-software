# Home Gym PT — Anatomically credible exercise-model and muscle-layer roadmap
Date: 2026-10-23
Status: RESEARCH-BACKED DEVELOPMENT PLAN ONLY; no muscle-layer model, biomechanical certification or production approval.

## Owner goal

Build one first-party human exercise model that (1) looks convincing as a natural human in neutral and moving poses, (2) demonstrates exercises safely and with biomechanically plausible joint motion, (3) has an internally coherent, individually named muscle atlas and reusable exercise-to-muscle rules, and (4) can author many subsequent movements efficiently in animation software and run on an iPhone. Commercial functionality follows model reliability. No false claim of precise physiology or patient-specific medical accuracy.

**Core recommendation:** Skeleton + joint kinematics → corrected skin deformation → verified muscle attachments/paths → selectively muscle-driven visible skin changes → reusable exercise contracts → baked efficient mobile playback.

Adding a full muscle layer prematurely **cannot** fix an incorrect shoulder pivot, axillary fold, wrist rotation, hip crease or foot proportions. It can make all five look worse.

## Existing repository work to reuse, not rebuild

- Experimental PR [#124](https://github.com/anyangle1409-code/animation-software/pull/124) on `work/experimental-anatomical-muscles-20261022`, built independently from PR123:
  - `experiments/anatomical_muscles/registry_seed.json`: **120 bilateral semantic records** from **60 base records**. Permanent IDs `hgpt.muscle.<functional_head>.<L|R>`, with descriptions for origin, insertion, depth, joints, other muscles, and source. IDs do **not** prove actual bone-coordinate bindings.
  - **90 pilot records**, **22 bilateral interaction records**; these are source-backed hypotheses, not physical tissue meshes.
  - `EXERCISE_MUSCLE_CONTRACT.md`, `exercise_contracts.json`, compiler and tests: bilateral curls, shoulder presses and squats with explicit phase envelopes and **activation independent of skeletal pose**. **34/34 synthetic foundation tests** reported on experimental handover. `PT_MODEL_VERSION 1.0` unchanged.
  - No actual muscle-rigged Blender file, no certified attachments, no finished tissue geometry, no approved skin deformation, no validated exercise appearance.
- `docs/recovery_20261023/muscle_attachment_worklist_shoulder_arm.json`: **42 shoulder, arm and scapular records**, **30** referenced by existing exercise phase contracts. Every native landmark/anchor binding remains unresolved.
- Independent cloud workbench `work/phone-blender-workbench-20261023`: three reconstructed candidate `.blend` models run safely on GitHub Blender 5.2; rigorous read-only reports; automated visual contact sheets.
- Original hidden/unsaved Blender authoring states have **NOT** been recovered equivalently. Current reconstructed V14 has **238,065** vertices versus archived **238,067**; W8 archived offsets and body proportions also fail correspondence. W8, V14 and R120 each fail existing deformation quality gates and grip acceptance. Their 77-bone rigs are not trivially compatible with the older 67-bone application bridge. Anatomical side naming and physical landmarks are not independently certified.
- R120 is an experimental denser surface, not a validated improvement. Its higher triangle counts may partly reflect topology density. Preserve all three read-only for A/B and provenance. **V14 is the provisional candidate for validation, NOT yet the approved base**.

## Evidence-based architecture — separate layers that must not be confused

### A. Skeleton, articular kinematics, movement

- Fixed, independently reviewed bony joint axes/centres; explicit bone and joint coordinate conventions (degrees, metres, anatomical side map).
- Distinct coordinated scapula, clavicle and humerus motion; shoulder elevates with scapular upward rotation, posterior tilt and clavicle action, and the ratio is not fixed. Dynamic clavicle/scapula support must be tested; hiding an axillary slit with larger deltoid shape keys is not an anatomical solution.
- Contact-aware pelvis, feet, toes, ground and dumbbell/grip positions; separate muscle visuals from movement geometry.
- Build pose envelopes for each exercise variant and validate the full movement, not only the start and final frames.

### B. Muscle atlas, paths and contraction semantics

Each functional muscle/head gets:
- Immutable anatomical ID, side, multi-bundle membership, tissue layer (superficial/intermediate/deep).
- Reviewed origin **attachment patch**, insertion **attachment patch**, bone-local landmarks and provenance — never invented from suffixes or weight-group centroids.
- Tendons/aponeuroses, via points, obstacles / wrapping around bones, crossed joints; path lengths measured in the moving rig, not only guessed in rule tables.
- Neighbor/fascia/adjacency, collision clearance and soft-tissue stacking. Underlying muscle bulges must not visibly penetrate skin or adjacent muscles.
- Independent channels: (1) bone pose, (2) measured musculotendon path length and velocity, (3) task-dependent qualitative activation/excitation, (4) visual belly deformation/skin response. A muscle may produce force while changing length very little; actively resisting lowering is not 'switched off'. Fiber shortening can differ from whole-tendon length behavior.
- Superficial muscles may deform a bounded, reviewed skin cage/region. **Deep muscles receive no direct arbitrary skin bulge**. Volume-preserving or nearly-volume-preserving muscle belly **proxy** is a graphics approximation, not real constitutive physics.

### C. Correct-looking outer skin and mobile runtime

- Retain *one coherent external skin*, not visible overlaid cylinders, segmented shoulders or an extra lumpy surface. Muscle layer is an anatomical authoring driver; body/fascia/fat produce the actual viewed silhouette.
- Repair core deformation first using evidence-guided weights, skeletal helper motion, contact/collision correction, and only necessary pose-space corrective shapes. Consider linear vs dual-quaternion/centre-of-rotation skinning at **isolated candidate scope**, not as an untested universal patch.
- In authoring Blender, calculate and validate high-quality deformation. For first-party mobile engine, bake supported animation/bone tracks and controlled corrective channels (GLB/export parity) to avoid runtime all-muscle volumetric physics. Keep visual rendering and anatomy-rules source-owned and independently tested.

## Research-backed muscle interactions to model, with verification caveats

| Exercise | Skeleton/joints | Main muscle interactions | Appearance tests |
|---|---|---|---|
| Supinated dumbbell biceps curl | Elbow flexion with stable humerus and forearm supination | Biceps long/short heads; brachialis and brachioradialis assist flexion; triceps opposes movement/stabilizes; wrist/grip stabilizers hold load | Elbow crease, tendon route to radius, believable biceps belly; sustained activation during controlled lowering; no spherical elbow, palm/forearm twist artifact |
| Shoulder press | Glenohumeral elevation + upward scapula rotation/posterior tilt + clavicle motion + elbow extension | Deltoid anterior/middle/posterior bundles; supraspinatus and rotator cuff stabilize humeral head; trapezius–serratus anterior force couple rotates/stabilizes scapula; triceps extends elbow; pec/lat/teres relationships vary with variant | No spherical deltoid cap, axillary slit, shoulder-head discontinuity, cap snap at high elevation or posterior upper-back bulges; checked 0°, ~90°, ~120°, ~149°, 160° relevant poses and lowering |
| Bodyweight squat | Hip/knee/ankle flexion and extension, pelvis/trunk and planted feet | Vastii/rectus femoris quadriceps, gluteus maximus, adductor magnus hip extension, hamstring and hip stabilizers; soleus/gastrocnemius/foot muscles support and regulate lower-limb moment | No groin pinch, hip shelf, horizontal knee ring, calf–ankle discontinuity, heel lift or foot drift; correct descending and ascending loading semantics |

**Important scientific caution:** Muscle activation cannot be measured from a joint angle alone. Exact force, recruitment percentage, EMG or safety claims would require load, speed, anthropometry and independently validated inverse/forward dynamics and/or experimental measurements. Current `0–1` contract values are relative *visual authoring estimates*, NOT measured physiology. Normal scapular motion and squat muscle demands also vary with task and individual.

## Gated execution plan — exact order

### Gate 0 — immutable trusted inputs and project single source of truth (now)

1. Preserve original and reconstructed W8/V14/R120 source SHA256 and initial render archives; keep experimental PR124 separate.
2. Address the V14 **two-vertex archive difference** by provenance, not manually inserting vertices. Investigate V14 right-leg cut-loop report discrepancy (699 archive vs 700 recovery) and absent/extra processing stages independently; original model identity remains unresolved.
3. Check anatomical sides against sternum/scapula landmarks and camera orientation; author explicit `anatomical_left ↔ runtime_suffix` map once truly verified.
4. Decide **V14 provisional** vs W8 rollback or R120 only with shape, movement, provenance and topology evidence. Do not silently promote the newest model.
5. Acceptance: input provenance and unchanged hash checks PASS, model topology and landmark validity documented, and one canonical candidate identified without loss of baselines. Until then no native muscle binds.

### Gate 1 — the base body must look and move credibly WITHOUT added muscles

1. Triage shoulder/scapula/clavicle/axilla deformation. Current evidence: S7 saved override 95° across models, shoulder-cap fraction 0.45, no axilla helper, large pose key offsets, press deformation still fails. These are **hypotheses, not automatic settings to change**.
2. Compare matched poses using diagnostics under independently chosen controlled variables: no correctives vs original correctives; old/new cap support and axilla only in *isolated in-memory tests or separately authorized suffixed experiments*, preserving all source files.
3. Triage hip/groin, knees, ankle, feet, hand/grip. Do not relax existing stretch/collapse/intersection/grip guards. Foot proportion and floor contact remain independent gates.
4. Before/after orthographic front/back/side/three-quarter body renders, exact movement metrics and foot/dumbbell contact at all test frames. No zero-data or aesthetic-only passing.
5. Acceptance: no glaring anatomical shape defects in rest/movement, no unresolved severe deformation, no regressed existing benchmark and reviewed tests/pass criteria. Existing 'FAIL' remains until demonstrably resolved.

### Gate 2 — one **minimal** isolated muscular proof of concept (do not build all 120)

1. Start with one **reviewed upper arm** at least complex enough to expose correct biceps long and short heads, deeper brachialis, brachioradialis, triceps long head and anatomical tendon paths; choose **one superficial biceps bundle first** for a small independent prototype, *only after actual bone-local attachment patches are reviewed*.
2. Check at elbow 0°, 45°, 90°, 120° and active/eccentric curl phases and forearm supination variants. Verify observed path length and tendon routing agree with registry and phase contracts.
3. Test *pose changes with zero visual activation*, then *activation changes at fixed pose*, then combined pose+activation. Confirm activation does not move skeleton and muscle deformation does not create elbow/collar collisions.
4. Render **muscle-only, translucent skin/muscle overlay, skin-only** with matched cameras. User reviews the appearance from phone.
5. All authorship on a new, explicitly approved, separate experimental candidate source; no production assets replaced.

### Gate 3 — shoulder muscle groups and real interaction between neighbors

1. Independently fit deltoid 3 heads, rotator cuff, trapezius bundles, serratus slips, pectoralis head bundles, latissimus, teres major and long-head biceps/triceps routes; use 42-record queue rather than rebuilding registry.
2. Validate moving scapula–thorax geometry, clavicle/AC/SC and GH joint correspondence, broad attachments (not toy straight cylinders), tendons, overlaps/clearance, and arm-down-to-overhead trajectories.
3. With no skin driving, test muscle paths and soft-tissue contact. Only then enable bounded superficial skin cages and corrective channels with comparison evidence.
4. Require shoulder press overhead pose and return to pass original surface rules and human visual review from back/front/side. Do not hide underlying slit or spherical shoulder with artificial muscle bulges.
5. Independent L and R attachment/camera checks, no arbitrary mirroring of anatomical side IDs.

### Gate 4 — lower-body muscle groups, ground contact and exercises

- Fit gluteal heads/regions, adductors, quadriceps vasti/rectus femoris, hamstrings, calf layers and tibialis anterior where justified by validated skeletal guides.
- Test squats first, then lunges/deadlifts/step-ups with planted feet, pelvic/hip motion and transition shape. Ensure knee extensor and biarticular hamstring roles respect pose/load variation.
- Keep proportions, heel/arch/toes, ground contact and hand-dumbbell grip as non-muscle dependencies.

### Gate 5 — reproducible exercise generator in animation software

Reuse PR124's versioned `hgpt.exercise...` contract and stable `hgpt.muscle...` identifiers; do not author muscles again for each exercise. The generator takes:
`exercise_variant + joint_trajectory + resistance/load description + tempo + phase + muscle/activation rules`.
It resolves reviewed anchors; derives musculotendon path length independently; adds **qualified** activation and stabilizer visual weighting; produces Blender motion, candidate high-resolution renders, exact test evidence and an exportable runtime animation.
If ID, binding, biomechanical rule, side or evidence is missing, **fail closed** rather than fabricate a motion or fake muscle.
Start curl, press, squat; then expand controlled variants without changing canonical anatomy.

### Gate 6 — final first-party production candidate and release acceptance

- One validated rig + one outer skin + one registered optional anatomical-muscle authoring layer; multiple LODs **only as derivatives**.
- App gets efficient bone motion, approved morph/pose correctives and muscle highlight metadata, *not a 120-muscle simulation running on the phone*.
- Device-level parity comparisons (Blender render vs mobile screenshot), loading and frame-rate targets measured on actual target devices, memory/asset size recorded.
- Separate acceptance levels **Structural Anatomy**, **Exercise Kinematics**, **Surface/Visual**, **Interaction/Contact**, **Educational Muscle Semantics**, **Runtime parity**; never describe a semantic registry pass as full physiological validity. Specialist anatomy/biomechanics and human-art review still required for any 'accurate' certification.
- Production deployment, merge or `PT_MODEL_VERSION` change only with owner approval after gates pass.

## What 'accurate' should mean in the app

**Commit to:** anatomically recognizable attachment regions and muscle labels, plausible joint kinematics and interacting tissue, stable deforming skin, visually credible contraction/relaxation, a reusable source of truth for exercises, full evidence and transparent caveats.

**Do NOT claim:** one human's exact true muscle-force/EMG pattern, individual-safe joint technique from a single anatomy model, mathematically exact fiber mechanics or fully physically simulated skin merely because OpenSim literature or some muscle proxies were used.

## Research sources and reason for inclusion

1. OpenSim model documentation: muscle paths, attachment points, fiber/tendon lengths, velocity and activation are distinct state/data channels. https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53088473
2. Seth et al., 2018, OpenSim framework peer-reviewed overview. https://pubmed.ncbi.nlm.nih.gov/30048444/
3. Seth et al., 2019, independently driven shoulder/scapular motion with muscle routes and reviewed moment arms; shoulder approximation guidance, not copied assets. https://pmc.ncbi.nlm.nih.gov/articles/PMC6856649/
4. Scapular kinematics systematic review (2025) finds substantial variability, rejects a universally fixed scapulohumeral rhythm and setting phase. https://pmc.ncbi.nlm.nih.gov/articles/PMC12398250/
5. NCBI, upper-arm anatomy, biceps long/short and forearm supination vs flexion role. https://www.ncbi.nlm.nih.gov/books/NBK519538/
6. NCBI, deltoid 3 bundles and origin/insertion shapes. https://www.ncbi.nlm.nih.gov/sites/books/NBK537056/
7. Straub & Powers (2024), squat technique variation influences joint loading and muscular demand. https://pmc.ncbi.nlm.nih.gov/articles/PMC10987311/
8. Rajagopal et al. (2016), full-body model with 80 lower-limb muscle-tendon units, upper body torque actuation; not an anatomical gold standard for all exercises. https://pubmed.ncbi.nlm.nih.gov/27392337/
9. Dynamic implicit muscles for character skinning: modeling muscle bellies, collisions and skin response can improve realism, but is distinct from physiological validation. https://www.sciencedirect.com/science/article/abs/pii/S0097849318301742
10. Disney Research, optimized centers-of-rotation skinning study: linear and dual-quaternion methods can have joint collapse/swelling artifacts; use controlled skinning comparisons. https://studios.disneyresearch.com/2016/07/11/real-time-skeletal-skinning-with-optimized-centers-of-rotation__trashed/
11. OpenSim activation is independent dynamic state, not simply joint angles. https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53090590

Scientific/source material is referenced for facts and implementation strategy only. No third-party geometric assets, copyrighted figures, code modules or proprietary runtime are imported. Check licensing before reuse of any anatomical dataset or reference mesh.

## Near-term laptop-off safe work package

- Document canonical landmark IDs and independent anatomical-side verification protocol.
- Add non-destructive cross-source consistency tests: permanent IDs, attachments remain unresolved, PR124 motion phase roles, no accidental deep-muscle direct skin, no production file writes.
- Run/preserve existing GitHub Blender pose reports and visual contact sheets with strict hashes.
- Create read-only side-by-side S7/cap/axilla metadata and actual pose-state report when the cloud workflow supports it.
- Do not pretend an authoring-only muscle proxy or registry passes Blender native validation. Don't automatically bind muscle names to body vertex groups as their origins.

**Decision:** build **one accurate model**, not three competing production models. Keep W8 and R120 as controlled baselines; V14 is provisional, not accepted. Add verified muscle anatomy incrementally after primary joint/skin defects are solved. This plan is compatible with laptop-off GitHub-based development and preserves Claude and PR124 lanes.


## Joint coordinate and human ROM foundational research (owner clarification, 23 October)

The owner has adopted a critical additional **FOUNDATION-FIRST** rule: build a generally human-like articulated body with verified interactions **before** teaching it dozens of exercise-specific movements. Generic body deformation quality must not depend on manually sculpting a new correction for every exercise.

Source-backed data/plan in:
- [Human Joint ROM Reference](anatomy/HGPT_HUMAN_JOINT_ROM_REFERENCE_V1.json): **43 semantic coordinates, 44 CDC adult age/sex reference means with confidence intervals of population means, 12 AAOS-style secondary nominal goniometry values, 12 cervical/lumbar regional means + SD, 19 conceptual full-body motion tests**.
- [Research interpretation / actual test gates](HGPT_HUMAN_JOINT_ROM_AND_MOVEMENT_PLAN_20261023.md).
- [PR124 motion vocabulary crosswalk](anatomy/HGPT_EXERCISE_ROM_CROSSWALK_V1.json): 16 joint/coordinate pairs from three existing exercise contracts. **Four bilateral shoulder records BLOCKED on ambiguous 'elevation' vs 'humerothoracic_elevation' anatomical plane/axis terminology**. Other pairs are semantic matches only and not native calibrated bones.
- `scripts/cloud_body_analysis/human_rom_reference.py`: compares clinical population means **descriptively**; no joint angle clamping or editing. Regression tests ensure means/CI, normative goniometry and rig data never get confused.

**Mandatory distinction:** Range-of-motion research is not a model-specific constrained skeleton. Each real rig axis, joint center, movement-specific contact and anatomical laterality must be checked in Blender before any numeric hard stop or exercise target can be accepted. Clinical ROM reference values differ across age, sex, load, posture, task and testing method. The existing PR124 shoulder press angles are authoring envelopes, not automatically validated anatomical kinematics.

**Priority order amended:** Stage 0 trustworthy provenance and side-axis calibration → isolated joint range & surface test suite across whole body → coupled joint kinetic movement and contact → native muscle attachment / path checks → exercise template reuse → app. Existing movement-gate failures remain open. More complex variants **may** still require individual geometry/contact validation, even when a credible general rig is finally established. Future muscle highlighting remains a naming-only, owner-deferred requirement.


## Cloud-native ISB rig-axis evidence and test readiness (23 October, verified)

- [Native rig-axis / ISB gap report](HGPT_ISB_NATIVE_RIG_LANDMARK_GAP_20261023.md): all three pinned Blender reconstruction candidates' 77 rest bones have identical recorded bone-local head/tail, orientation and pose-mode metadata. This is a **rig structural consistency result**, not an anatomical or deformation PASS.
- [Read-only five-job CI run 40030774310](https://github.com/anyangle1409-code/animation-software/actions/runs/40030774310) SUCCESS; its cross-model artifact `12535425648` was downloaded, SHA256 matched `d3fca1d8303ed65d14402f471e23ae44ef609229c43646d1f8125212eaf931a9`, and reports were inspected. Reproducible `compare_rig_axes.py` fails closed on wrong source hashes, invalid local axes, mismatched bone metadata or unearned anatomy approvals.
- 35 named L/R rest-control pairs: one `muscle_pec_l/r` helper head X-mirror offset of 2.433 mm is a review candidate, **not** an established muscle-origin defect. W8 foot/toe control span suggests a targeted foot geometry review, not a validated toe length.
- [46 unbound ISB-inspired anatomical landmarks](anatomy/HGPT_ISB_LANDMARK_REQUIREMENTS_V1.json) and tests provide a checklist for thorax/scapula/clavicle/humerus/radius-ulna, pelvis/hip/knee/ankle/foot calibration. No landmark assigned to a mesh vertex or bone; no physical muscle attachment inferred.
- [19-scenario generic motion test ledger](anatomy/HGPT_HUMAN_MOTION_TEST_EXECUTION_LEDGER_V1.json) records **0/19 generic tests executed/accepted**; previously recorded native shoulder press, squat and grip failures remain **failures**, not accepted isolated-joint tests.
- **New next gate:** independently identify anatomical side/front/back and bone landmarks in native mesh, define segment coordinate frames, verify shoulder complex versus GH/scapula/clavicle rotation and forearm twist, and only then run *pose-state* tests across realistic but not hard-coded ROM envelopes. Use joint-contact, soft-tissue and skin deformation evidence; don't let identical rest rigs hide differing mesh weights/correctives.
- Future muscle highlighting remains deferred by owner. Permanent semantic muscle IDs preserved without a visual/UI implementation.
