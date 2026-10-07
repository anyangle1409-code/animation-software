# Whole-body anatomical movement atlas — specification
Date: 2026-10-07
Branch: codex/whole-body-biomechanics-audit-20261007
Status: RESEARCH / REFERENCE FOUNDATION

## Purpose
Build a complete adult human skeletal reference for Home Gym PT in which every bone and every articulation is accounted for before production-rig simplification.

The atlas is not a single table of maximum angles. For each articulation it must record:
- participating bones;
- anatomical landmarks and joint centre/reference frame;
- parent/child or coupled relationship;
- degrees of freedom;
- primary axes;
- normal active and passive ROM where available;
- coupled motion;
- moving/instantaneous centre behaviour where relevant;
- load/posture dependence;
- differences by movement plane where relevant;
- whether motion is negligible/fused in the adult;
- evidence confidence and sources;
- proposed Blender representation;
- bone-only test cases and acceptance criteria.

## Standard coordinate-system sources
- Wu et al. 2002, ISB Part I: ankle, hip and spine. PMID 11934426.
- Wu et al. 2005, ISB Part II: shoulder, elbow, wrist and hand. PMID 15844264.
These are the primary convention references for segment frames and joint motion terminology.

## Complete regional coverage

### Skull / jaw
- cranial sutures: adult reference geometry; normally no animation DOF.
- temporomandibular joint: rotation + translation during opening/closing, protrusion/retrusion and lateral excursion.
- occiput-C1: upper-cervical flexion/extension and smaller coupled motions.
- C1-C2: major contributor to cervical axial rotation.
- C2-C7: distributed subaxial flexion/extension, lateral bending and rotation.

### Thorax / spine
- C1-C7 individually accounted for.
- T1-T12 individually accounted for.
- L1-L5 individually accounted for.
- sacrum/coccyx accounted for.
- costovertebral/costotransverse joints and sternocostal system included as a rib-cage mechanics layer.
- SI joints included with small but non-zero motion.
Evidence anchors: PMID 10946096, 36496482, 40046266, 27487429, 30100219, 29395226, 33256545, 35782518.

### Shoulder girdle / upper limb
- sternoclavicular joint;
- acromioclavicular joint;
- scapulothoracic functional articulation;
- glenohumeral joint;
- elbow: ulnohumeral + radiocapitellar;
- proximal radioulnar;
- distal radioulnar;
- wrist: radiocarpal + midcarpal functional stages;
- carpal bones individually present in anatomical reference;
- CMC joints;
- MCP joints;
- PIP/DIP joints;
- thumb CMC/MCP/IP.
Evidence anchors: PMID 15844264; shoulder sources already documented in SHOULDER_COMPLEX_MULTI_SOURCE_VERIFICATION_20261007.md; PMID 15621323; 16945717.

### Pelvis / lower limb
- sacroiliac articulation;
- hip/femoroacetabular joint;
- tibiofemoral joint;
- patellofemoral joint;
- proximal/distal tibiofibular relationships;
- talocrural joint;
- subtalar joint;
- transverse-tarsal/midfoot functional mechanics;
- tarsometatarsal joints;
- metatarsophalangeal joints;
- toe interphalangeal joints.
Evidence anchors: PMID 11934426, 31078827, 31019669, 17004269, 20300732, 9675688, 10659530, 40290610, 7738816.

## Important modelling rule
A real bone may be present in the anatomical reference without being an independent production deform bone. Production simplification is permitted only after the full reference model demonstrates what mechanical behaviour is being replaced and an automated comparison shows the simplified control reproduces that behaviour within the agreed tolerance.

## ROM policy
Do not encode one universal "human ROM" number when evidence shows population or task variation.

For each motion record:
- source mean/range;
- active vs passive;
- subject posture;
- loading condition;
- sex/age dependence if material;
- measurement method;
- conservative production envelope;
- task-specific expected range.

Examples of why:
- cervical axial rotation depends heavily on C1-C2 while flexion/extension is distributed more subaxially;
- thoracic/lumbar/pelvic contribution changes by plane and task;
- wrist flexion/extension and radial/ulnar deviation are coupled;
- shoulder kinematics differ by plane of elevation;
- hip rotation depends on hip flexion angle;
- knee has coupled axial rotation/translation and patellar tracking;
- ankle and subtalar contributions differ by movement direction;
- hallux ROM under gait differs from passive clinical ROM.

## Validation sequence
1. Anatomical inventory complete.
2. Landmark / coordinate-frame definitions complete.
3. Joint centre and axis definitions sourced.
4. ROM/coupled-motion evidence compiled.
5. Full anatomical reference skeleton authored.
6. Bone-only sweeps executed.
7. Multi-joint functional movements executed.
8. Compare against source envelopes.
9. Only then derive/approve the lighter production rig.
