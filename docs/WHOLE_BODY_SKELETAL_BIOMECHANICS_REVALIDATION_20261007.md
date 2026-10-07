# Whole-body skeletal biomechanics revalidation — 2026-10-07

Status: REOPENED. Previous LOCKED labels are historical evidence only and do not constitute acceptance under this stricter review.

Branch: `codex/whole-body-biomechanics-audit-20261007`

## Rule

Every major joint must pass, in order:
1. anatomical structure / joint-centre review;
2. degrees-of-freedom and axis review;
3. static code/rig audit;
4. bone-only Blender sweep through representative ROM;
5. continuous-motion / reversal / load-path testing;
6. multi-view visual review against multiple human biomechanics references;
7. only then skin/weights/deformation review.

Passing a broad ROM envelope is not sufficient.

## Current rig versus stricter anatomical target

| Region | Current representation | Preliminary status | What must be proven / likely change |
|---|---|---|---|
| Head / cervical spine | head + one neck bone | REOPEN | Test flex/ext, lateral bend, axial rotation and coupled motion. One neck bone may be too coarse because upper cervical axial rotation and lower cervical flex/ext have different distributions. Consider upper- and lower-cervical controls if testing confirms this. |
| Thoracic / lumbar spine | pelvis + spine_01..03 | REOPEN | Verify lumbar vs thoracic distribution, axial rotation, lateral flexion, extension and loaded anti-rotation. Add thorax/ribcage reference if needed; shoulder solver requires a stable thorax frame. |
| Shoulder complex | clavicle + scapula + upperarm + GH helpers | FAIL / ACTIVE REBUILD | Separate SC, AC and GH functions/locations; full 3-D clavicle/scapula motion; plane-dependent GH rotation; moving glenoid. |
| Elbow | upperarm -> forearm, hinge-oriented pose logic | REOPEN | Verify real flexion axis, carrying angle, flex/ext path and separation from forearm pronation/supination. Consider explicit elbow-axis/reference control; do not assume perfectly straight one-axis hinge. |
| Forearm | one forearm structural bone + two axial twist helpers | REOPEN | Validate pronation/supination axis, radial/ulnar relationship, elbow-to-wrist distribution and load transfer. Decide whether separate radius/ulna references or the current twist-chain abstraction reproduces anatomy sufficiently. |
| Wrist | forearm -> single hand bone | HIGH-PRIORITY REOPEN | Test radiocarpal/midcarpal distribution, flex/ext, radial/ulnar deviation and loaded push-up extension. Single wrist pivot may be insufficient for realistic loaded deformation; consider carpal/wrist helper stage. |
| Palm / long fingers | hand + 4 metacarpals + MCP/PIP/DIP chains | STRUCTURE MOSTLY PRESENT; MOTION FAILS SCRUTINY | Existing finger bones are broadly sufficient, but current grip applies identical fixed MCP/PIP/DIP angles and parallel-hinge logic. Validate digit-specific coupling, palm arch/cupping and object-driven contact. |
| Thumb | thumb_01..03 | HIGH-PRIORITY REOPEN | Map existing bones explicitly to CMC/metacarpal/MCP/IP function; reproduce saddle-joint opposition (flexion + abduction + pronation) rather than treating the entire chain as parallel hinges. |
| Hip | pelvis -> thigh | REOPEN | Verify femoral-head joint centre, 3-DoF rotation, pelvis/femur coupling and deep-flexion/rotation paths. A single ball-joint control may remain sufficient if correctly centred. |
| Knee | thigh -> shin | HIGH-PRIORITY REOPEN | Current fixed pivot/aim model must be tested against rolling/sliding and coupled tibial rotation (screw-home). Add moving knee-centre / coupled rotation logic if needed. Patellar motion must be represented for visible knee realism. |
| Lower leg | one shin bone | REOPEN | Decide whether tibia-only structural bone plus helpers is sufficient; fibular reference may be needed for ankle/lateral-knee landmarks even if it mostly follows tibia. |
| Ankle / hindfoot | shin -> foot | HIGH-PRIORITY REOPEN | Separate talocrural dorsiflexion/plantarflexion from subtalar inversion/eversion/pronation-supination. Likely needs hindfoot/subtalar control rather than one all-purpose foot pivot. |
| Forefoot / toes | one foot bone + one toe bone per side | HIGH-PRIORITY REOPEN | A single toe block cannot independently represent hallux and lesser-toe mechanics. Test push-up, calf raise, lunge and gait-like forefoot loading; likely split hallux from grouped lesser toes and add forefoot/heel controls. |

## Source-backed mechanical facts guiding the audit

### Cervical spine
Healthy cervical motion is distributed. Flexion/extension and lateral bending are mainly subaxial; axial rotation depends strongly on C1-C2. Coupled rotation/translation is normal rather than pure one-axis motion.
Sources: PMCID PMC9794546; PMID 36496482; PMID 10946096.

### Elbow / forearm
The elbow complex contains ulnohumeral, radiocapitellar and proximal radioulnar articulations. Flexion/extension is hinge-dominant, but the flexion axis is oblique and produces a carrying angle; forearm rotation is a separate proximal/distal radioulnar function.
Source: PMCID PMC8258984.

### Wrist / hand
Wrist function distributes motion across multiple carpal articulations and supports flexion/extension, radial/ulnar deviation and circumduction. Forearm pronation/supination should not be implemented as wrist twist.
Source: PMCID PMC5397304.

Long-finger MCP joints have flex/ext plus ab/adduction; PIP and DIP are primarily hinge joints with linked motion. Dynamic gripping is not four identical chains: PIP generally contributes the largest ROM and joint sequence/coupling varies.
Sources: PMCID PMC3193629; PMC10296280; PMC2483967.

Thumb opposition is a coordinated multi-joint, multi-axis motion with CMC flexion/pronation coupling; the CMC is a saddle joint and IP is hinge-like.
Sources: PMID 16643926; PMCID PMC3193629.

### Hip
The hip is a ball-and-socket joint permitting flex/ext, ab/adduction and internal/external rotation. Its joint centre and impingement-free envelope are more important than adding arbitrary helper bones.
Sources: PMCID PMC3558075; PMC10965652.

### Knee
The native knee is not a perfect fixed-axis hinge. Flexion/extension includes coupled translation/rollback and tibial axial rotation; terminal extension includes the screw-home mechanism.
Sources: PMCID PMC10511824; PMC4553277; PMID 33554884; PMID 15797589.

### Ankle / foot
The ankle complex includes talocrural, subtalar and transverse-tarsal functions. Talocrural motion dominates plantar/dorsiflexion; subtalar mechanics are major contributors to inversion/eversion and combined pronation/supination.
Sources: PMCID PMC4994968; PMC8381447; PMID 20300732.

The first MTP/hallux is a distinct condyloid joint important in loaded propulsion and may dorsiflex roughly 57-82 degrees in passive measurements; it should not automatically be fused to all lesser toes.
Sources: PMCID PMC12019138; PMC7944704; PMC7337226.

## Dynamic Blender test matrix

Each region receives neutral -> intermediate -> near-limit -> reversal sweeps, both sides where relevant.

- neck: flexion, extension, L/R axial rotation, L/R lateral flexion, coupled look-up-and-turn;
- spine: flex/ext, L/R rotation, L/R lateral flexion, hip hinge, anti-rotation;
- elbow: 0-150 flexion with neutral/pronated/supinated forearm;
- forearm: pronation/supination at elbow 0, 90 and elevated-arm positions;
- wrist: flex/ext + radial/ulnar deviation; loaded 70-90-degree extension; circumduction path;
- fingers: open/close, cylindrical grip, large bar, small handle, pinch; per-digit MCP/PIP/DIP traces;
- thumb: opposition/reposition, abduction/adduction, cylindrical wrap and pinch;
- hip: flex/ext, ab/adduction, IR/ER at neutral and flexion, squat/lunge;
- knee: 0-140 flexion under unloaded and squat/lunge paths; tibial rotation and joint-centre trace;
- ankle: dorsiflexion/plantarflexion with separate inversion/eversion; squat, lunge, calf raise;
- forefoot/toes: hallux and lesser-toe extension under push-up/lunge/calf-raise contact.

## Decision rules for adding bones/controls

Add a new anatomical or helper control only when one of these is true:
- two real articulations are currently collapsed into one pivot;
- two mechanically independent DoFs cannot be represented independently;
- a moving joint centre cannot be represented by the existing chain;
- realistic load transfer requires a distinct segment;
- a clearly visible bony landmark moves independently enough to affect surface deformation.

Do not add 206 literal deform bones simply because they exist anatomically. The target is anatomical mechanical equivalence, with explicit references/helpers where needed.

## Current preliminary priorities after shoulder

1. knee;
2. ankle/hindfoot/forefoot;
3. wrist/forearm;
4. thumb/finger mechanics;
5. cervical spine;
6. elbow;
7. hip;
8. thoracic/lumbar distribution.

This order reflects current structural simplification risk, not final severity.
