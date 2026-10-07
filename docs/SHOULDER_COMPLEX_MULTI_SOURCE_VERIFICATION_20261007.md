# Shoulder complex multi-source verification — 2026-10-07

Status: PRE-BLENDER EVIDENCE + STATIC TESTS COMPLETE; DYNAMIC BLENDER TESTS PENDING EXECUTION

Branch: `codex/shoulder-biomechanics-audit-20261007`

## What is being verified

This is not a request to add arbitrary extra "bones." It verifies that the rig separately represents and correctly drives the anatomical shoulder complex:

thorax -> SC articulation -> clavicle -> AC articulation/scapula -> glenoid/GH articulation -> humerus.

The scapulothoracic articulation is a functional gliding articulation, not a true synovial joint. A production rig may represent SC/AC/GH with control/reference bones, pivots, empties or transforms; they do not have to be deforming bones. What matters is that their positions and degrees of freedom are not collapsed into one point or one rotation.

## Independent evidence

1. Chang et al., *Shoulder Anatomy and Normal Variants* (PMCID PMC6251069): shoulder mobility is produced by four separate articulations: glenohumeral, acromioclavicular, sternoclavicular and scapulothoracic; GH is the humeral head articulating with the glenoid fossa.
2. StatPearls, *Anatomy, Shoulder and Upper Limb, Shoulder* (NCBI Bookshelf NBK536933): SC joins clavicle to sternum; AC joins clavicle to acromion; ST is scapula gliding over thorax; GH is humeral head with glenoid.
3. Wu et al. 2005, International Society of Biomechanics recommendation, J Biomech 38(5):981-992, PMID 15844264: standard shoulder kinematics use separate coordinate systems for thorax, clavicle, scapula and humerus and distinct SC, AC and GH motion definitions.
4. McClure et al., *Three-dimensional clavicular motion during arm elevation*, PMID 15089027: during elevation the clavicle generally elevates 11-15 deg, retracts 15-29 deg and posteriorly rotates 15-31 deg, varying by subject and movement plane.
5. Ludewig & Reynolds, *The Association of Scapular Kinematics and Glenohumeral Joint Pathologies*, PMCID PMC2730194: normal shoulder elevation depends on coordinated scapular and clavicular kinematics.
6. Phadke, Camargo & Ludewig, *Scapular and rotator cuff muscle activity during arm elevation*, PMCID PMC2857390: normal scapular motion includes upward rotation, posterior tilt and external rotation; upper trapezius contributes clavicular elevation and retraction; rotator cuff limits excessive humeral-head translation and assists external rotation.
7. Ludewig et al., *Motion of the shoulder complex during multiplanar humeral elevation*, PMID 19181982 / PMCID PMC2657311: bone-fixed tracking found clavicular elevation/retraction/posterior axial rotation; scapular rotation/upward rotation/posterior tilt; and GH elevation/external rotation. Substantial rotations occurred at all four shoulder joints and differed by elevation plane.
8. Yabata & Fukui 2022, PMCID PMC9246406: scapular upward rotation, posterior tilt and external rotation differ between flexion and abduction and are influenced by thoracic posture.
9. Stokdijk et al., *External rotation in the glenohumeral joint during elevation of the arm*, PMID 12689779: each elevation plane has its own external-rotation pattern.
10. Matsuki et al., *Dynamic in vivo glenohumeral kinematics during scapular plane abduction*, PMID 22030448: healthy GH translation is small (millimetres) and changes direction through elevation; humeral rotation relative to scapula is dynamic, not a simple fixed-point hinge.

## Static tests run against current r97/r98 implementation

### T1 — AC versus GH location
Inputs:
- exported rev2c left clavicle tail = (-0.215, 1.515, -0.03)
- exported rev2c left upperarm head = (-0.215, 1.515, -0.03)
- r97 `scapula_pivot.py` explicitly moves scapula head to clavicle tail and labels it AC joint
- r97 `add_gh_helper.py` explicitly uses upperarm head and calls it the glenohumeral centre

Result: **FAIL**
Effective r97/r98 AC/scapula pivot to GH/upperarm origin separation = **0.0 mm**.
This is a rig abstraction, but because both locations are explicitly given different anatomical identities in project code, their coincidence is not anatomically defensible as the final shoulder model.

### T2 — Explicit shoulder-girdle DoF coverage
Current `girdle_for_elevation()` explicitly commands:
- clavicle elevation
- scapular upward rotation

It does not explicitly command:
- clavicle retraction/protraction
- clavicle posterior/anterior axial rotation
- scapular posterior/anterior tilt
- scapular internal/external rotation

Result: **FAIL / incomplete 3-D shoulder model**.

### T3 — Plane dependency
At the same humerothoracic elevation, current formulas return the same clavicle elevation, scapular upward rotation and straight-arm humeral external rotation for flexion, scaption and abduction.

Examples:
- 90 deg: clavicle 8.1 deg; scapula 18.75 deg; generic humeral ER 30 deg in all planes.
- 150 deg: clavicle 13.5 deg; scapula 51.15 deg; generic humeral ER 60 deg in all planes.
- 170 deg: clavicle 15 deg; scapula 62.15 deg; generic humeral ER 70 deg in all planes.

Result: **FAIL**.
Published 3-D studies show plane-dependent scapular and humeral rotation patterns.

### T4 — Clavicle elevation magnitude
Current rule reaches 15 deg maximum clavicle elevation.

Result: **PASS for magnitude only**.
McClure et al. reports about 11-15 deg maximum elevation, but the current model is missing the simultaneously observed retraction and posterior axial rotation.

### T5 — Piecewise scapular rule smoothness
Current scapular upward-rotation rule is position-continuous but its slope changes abruptly:
- at 30 deg: 0.025 -> 0.30 deg scapular rotation per degree elevation
- at 90 deg: 0.30 -> 0.53
- at 120 deg: 0.53 -> 0.55

Result: **FAIL for production motion smoothness / requires replacement with a smooth curve**.
This is not proof that the sampled angles are anatomically wrong; it is proof that the current rule introduces non-smooth contribution-rate changes.

### T6 — Humeral axial rotation model
Current straight-elevation rule is:
`ER = min(80, 0.5 * max(0, elevation - 30))`
and is independent of movement plane.

Result: **FAIL as a universal shoulder rule**.
Stokdijk et al. and other in-vivo work show distinct axial-rotation patterns by elevation plane.

## What is confirmed versus not yet confirmed

CONFIRMED:
- The anatomical shoulder complex requires distinct SC, AC, GH and scapulothoracic functions.
- Clavicle, scapula and humerus are the principal bones; the project does not need arbitrary extra anatomical bones.
- Current r97/r98 collapses its explicitly-labelled AC pivot and GH centre to the same coordinate.
- Current shoulder driver omits explicit major 3-D clavicular/scapular components.
- Current driver is insufficiently plane-dependent.
- Current piecewise rhythm function is not first-derivative smooth.

NOT YET CONFIRMED:
- Exact final AC and GH coordinates for this character.
- Exact subject-specific motion curves at every elevation angle.
- Whether additional deforming helper bones are needed after correct joint mechanics.
- Final skin/weight/corrective solution.

Those require the Blender bone-only sweep and visual/kinematic review.

## Dynamic Blender test suite already prepared

`scripts/audit_shoulder_complex_overhead_blender.py` samples both sides at:
0, 30, 60, 90, 120, 150, 170 deg
in flexion, 30-deg scaption and abduction.

Required expansion before acceptance:
- define ISB-style thorax/clavicle/scapula/humerus frames;
- report SC elevation/retraction/axial rotation;
- report AC/scapular upward rotation/posterior tilt/internal-external rotation;
- report GH elevation/plane/axial rotation;
- report GH centre relative to glenoid;
- sample ascent, descent and reversal for hysteresis/continuity;
- compare central reference envelopes without forcing one universal subject curve;
- render bone-only front/side/rear/3Q views.

No shoulder skeleton change is production-approved until these tests pass.
