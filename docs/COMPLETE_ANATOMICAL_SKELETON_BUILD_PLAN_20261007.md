# Complete anatomical skeleton build plan — 2026-10-07

Branch: codex/whole-body-biomechanics-audit-20261007
Purpose: create a complete adult-human anatomical reference skeleton and derive a validated production rig from it.

## Non-negotiable rules
1. Do not modify the current production candidate while the reference skeleton is being built.
2. The conventional adult skeleton inventory is the starting checklist: all bones must be explicitly accounted for.
3. A bone may be FIXED, FOLLOWER, ACTIVE or REFERENCE, but may not be silently omitted.
4. Joint correctness is more important than bone count: every articulation must have a sourced centre/frame, degrees of freedom and movement behaviour.
5. No joint is declared LOCKED until its bone-only dynamic tests pass.
6. Production simplification happens only after equivalence testing against the anatomical master.

## Phase A — Inventory and evidence ledger
Create one machine-readable ledger covering:
- axial skeleton: skull, auditory ossicles, hyoid, vertebral column, thoracic cage;
- appendicular skeleton: pectoral girdle, upper limbs, pelvic girdle, lower limbs;
- all conventional adult bones, left/right where applicable;
- every articulation between them;
- anatomical landmarks needed for joint coordinate systems;
- source references and confidence.

For every articulation record:
- parent/child bones;
- joint type;
- rest centre / reference frame;
- axes;
- degrees of freedom;
- active/passive ROM where applicable;
- coupled motion;
- load/posture dependence;
- known moving-axis/translation behaviour;
- evidence sources.

Gate A: zero unclassified bones and zero unclassified articulations.

## Phase B — Character-specific anatomical fitting
Use the HomeGymPT character proportions rather than copying generic coordinates.

Fit/reference:
- skull base and cervical column;
- vertebral levels and rib cage;
- sternum;
- clavicles/scapulae;
- humeral heads, elbow landmarks, radius/ulna, wrist/hand;
- pelvis landmarks, acetabular centres;
- femoral heads/condyles;
- patellae;
- tibia/fibula and malleoli;
- talus/calcaneus and forefoot landmarks;
- metatarsals/toe phalanges.

Reference landmarks include at least:
SC, AC, glenoid/GH, scapular inferior angle/medial border, humeral epicondyles,
radial/ulnar styloids, ASIS/PSIS, acetabular/femoral-head centres,
greater trochanters, femoral condyles, tibial tuberosities, patellae,
medial/lateral malleoli, calcaneus, navicular, metatarsal heads and hallux landmarks.

Gate B: bilateral symmetry checks and plausible segment proportions; no anatomically distinct joint centres collapsed without evidence.

## Phase C — Build the complete Blender anatomical master
Create a separate armature/reference collection:
HGPT_ANATOMICAL_MASTER

Each conventional adult bone is represented.
Roles:
- ACTIVE: independently solved movement;
- FOLLOWER: follows a coupled articulation;
- FIXED: structurally present but normally immobile in adult exercise motion;
- REFERENCE: landmark/coordinate-system helper where needed.

Detailed bone surface meshes are not required for the biomechanics layer; bone transforms, landmarks and joint frames are the priority.

Gate C: complete hierarchy loads in Blender, names and left/right mapping validated, no orphan or duplicate bones.

## Phase D — Joint solvers
Implement region solvers against sourced biomechanics:
- TMJ;
- C0-C1, C1-C2, C2-C7;
- thoracic/lumbar distribution and rib-cage reference;
- SI/pelvis;
- SC/AC/scapulothoracic/GH;
- elbow + proximal/distal radioulnar;
- radiocarpal/midcarpal;
- thumb CMC/MCP/IP;
- long-finger CMC/MCP/PIP/DIP;
- hip;
- tibiofemoral + patellofemoral;
- tibiofibular relationships;
- talocrural + subtalar + midfoot;
- MTP/IP joints including independent hallux.

No exercise-name hacks. Solvers take joint state / task constraints.

Gate D: each joint passes isolated bone-only ROM and coupling tests.

## Phase E — Whole-body dynamic validation
Run both sides and multiple starting postures.

Isolated tests:
- flexion/extension;
- ab/adduction;
- internal/external rotation;
- pronation/supination;
- inversion/eversion;
- circumduction where appropriate;
- ascent/descent/reversal.

Functional tests:
- squat;
- split squat/lunge;
- hip hinge;
- calf raise;
- push-up/plank;
- curl;
- row;
- shoulder press;
- pull-up/hang;
- reaching in multiple planes;
- loaded grip;
- wrist-supported loading.

Record:
- joint-centre trajectories;
- rotations in anatomical frames;
- coupled translations;
- symmetry;
- continuity and acceleration;
- source-envelope compliance.

Gate E: no unexplained discontinuities, collapsed joint centres, impossible translations or unsupported extrapolation.

## Phase F — Compare current production rig to master
For every current production bone/control:
- map it to the anatomical master;
- quantify what anatomical motion it reproduces;
- identify missing functions;
- add only the controls/helpers required to reproduce the master.

A production bone/reference may be removed or grouped only if automated comparison demonstrates equivalent motion within agreed tolerance.

Gate F: production rig passes the same functional tests against the anatomical master.

## Phase G — Skin/deformation
Only after the skeleton passes:
- rebind/reweight where required;
- rebuild shoulder/axilla;
- wrist/hand;
- pelvis/hip;
- knee/patella;
- ankle/foot;
- add pose-space correctives only after bone mechanics are correct.

Gate G: multi-angle visual convergence against real human references.

## Phase H — App export
Export HGPT_RUNTIME_RIG only.
Do not ship reference-only bones unless useful at runtime.

Measure:
- GLB size;
- bone count;
- deform-bone count;
- max influences/vertex;
- CPU solver time;
- GPU skinning time;
- memory;
- frame rate on target phone.

Maintain an automated master-vs-runtime biomechanics regression test.

## Work split
Can be done now without local Blender:
- source/evidence ledger;
- complete bone/articulation inventory;
- data schema;
- static audits;
- solver specifications;
- automated test specifications and scripts.

Requires Blender/laptop:
- character-specific 3-D landmark fitting;
- armature generation/check;
- actual bone-only motion sweeps;
- renders and joint-trajectory extraction;
- binding/weight/deformation work.

## First build order
Although the inventory covers the entire skeleton immediately, implement/test in this dependency order:
1. pelvis/spine/thorax reference frames;
2. shoulder complex;
3. hip/pelvis;
4. knee/patella;
5. ankle/hindfoot/foot/toes;
6. elbow/forearm;
7. wrist/hand/thumb/fingers;
8. cervical spine/head/TMJ;
9. ribs and remaining reference/fixed bones;
10. whole-body compound validation.

This is an implementation order, not permission to omit later regions.
