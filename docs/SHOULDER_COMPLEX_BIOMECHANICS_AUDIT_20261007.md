# Shoulder-complex biomechanics audit (bone-only)

Branch: `codex/shoulder-biomechanics-audit-20261007`

This work is deliberately isolated from the whole-body recovery branch and from r98. It must not change mesh topology, weights, shape keys, clothing, production READY state, or the preserved r98 candidate.

## Why this audit exists

The current elevated-arm pose driver explicitly commands only:

- clavicle elevation;
- scapular upward rotation;
- humeral elevation/aim;
- a heuristic elevation-coupled humeral external-rotation rule.

That is insufficient evidence that the skeleton reproduces three-dimensional human overhead shoulder mechanics. Healthy arm elevation couples motion at the sternoclavicular, acromioclavicular/scapulothoracic and glenohumeral articulations. Relevant components include clavicular elevation/retraction/posterior rotation and scapular upward rotation/posterior tilt/transverse-plane rotation, with plane-dependent humeral axial rotation.

The current driver also extrapolates its scapular upward-rotation curve above 120 degrees and uses a project heuristic for clavicle elevation. Those choices must be measured, not assumed correct.

## Evidence base used for the audit design

Primary/review literature consulted before writing this audit:

- Ludewig PM, Reynolds JF. *The Association of Scapular Kinematics and Glenohumeral Joint Pathologies.* J Orthop Sports Phys Ther. 2009. PMCID: PMC2730194.
- Phadke V, Camargo PR, Ludewig PM. *Scapular and rotator cuff muscle activity during arm elevation: A review of normal function and alterations with shoulder impingement.* Rev Bras Fisioter. 2009. PMCID: PMC2857390.
- Lawrence RL et al. *The Coupled Kinematics of Scapulothoracic Upward Rotation.* PMCID: PMC8204887.
- Umehara J et al. *Relationship between scapular initial position and scapular movement during dynamic motions.* PMCID: PMC6936830.

The literature shows substantial inter-subject and plane-of-elevation variability. Therefore this audit does **not** encode one rigid "perfect human" angle curve. It first captures the model's actual 3-D bone motion and exposes which degrees of freedom are explicitly driven, absent, or extrapolated. Reference envelopes can then be added only where adequately sourced.

## Required sweep

Bone-only samples at:

`0, 30, 60, 90, 120, 150, 170 degrees`

for:

- flexion;
- scaption (30 degrees anterior to the frontal plane);
- abduction.

For each sample record both sides:

- clavicle head/tail, world orientation, elevation/protraction-axis/twist components;
- scapula head/tail, world orientation and 3-D rotation-vector components;
- glenohumeral/upper-arm head position;
- upper-arm orientation and axial rotation;
- helper-bone orientation if `glenohumeral_half_<side>` exists;
- humeral-head translation relative to the glenoid/scapular frame.

## Immediate fail-closed questions

1. Is overhead motion being produced by a complete 3-D shoulder-complex mechanism, or mainly by scapular upward rotation plus humeral rotation?
2. Does the clavicle gain posterior rotation and retraction as elevation rises, or are those DOFs absent?
3. Does the scapula posteriorly tilt and change transverse-plane orientation, or is it effectively a one-axis hinge?
4. Is humeral axial rotation plane-dependent, or does one generic elevation formula dominate flexion/scaption/abduction?
5. Does the humeral head remain plausibly centred relative to the moving glenoid through the sweep?
6. Are there discontinuities at 30, 90 or 120 degrees caused by the piecewise rhythm function?
7. Above 120 degrees, does the extrapolated rule remain plausible rather than simply forcing the hand overhead?

## Promotion rule

No mesh, weight, axillary-fold or corrective work should be justified from this branch until the bone-only report is reviewed. A visually poor shoulder may not be repaired by asking skinning to compensate for incorrect skeleton motion.

The next executable is `scripts/audit_shoulder_complex_overhead_blender.py`. It is read-only and never saves the .blend.
