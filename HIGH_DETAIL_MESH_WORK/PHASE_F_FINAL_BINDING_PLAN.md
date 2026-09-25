# Phase F — final 63-bone character binding and deform weights

## Gate

Dormant until all final geometry decisions are accepted:
- body/knee;
- hand;
- shoulder/back/chest/armpit;
- appearance/material source.

This is the first phase allowed to create the **final correctly bound character
asset**. It must still remain a candidate until neutral equivalence and the full
exercise library pass.

## Structural target

Bind to the frozen canonical hierarchy:
- skeleton ID `hgpt_canonical_v3`
- 63 canonical bones
- freeze commit `19ca602...`
- four metacarpals per hand
- `thumb_01` as CMC/metacarpal control
- scapulae between clavicles and upper arms
- no new canonical bones

Do not infer canonical palm placement from the old exported production palm
bones: those were measured roughly 207–213 mm from their own knuckles and were
unweighted. Use the frozen canonical metacarpals.

## Character-specific structure

Preserve the established character-specific forearm twist-helper behaviour.
Do not add twist helpers to the canonical skeleton merely because the character
uses them internally.

Any helper-to-canonical mapping must be explicit and reproducible.

## Binding order

1. Reproduce accepted rest geometry exactly.
2. Bind the canonical 63-bone structure.
3. Prove neutral/rest surface equivalence before painting new behaviour.
4. Establish palm/metacarpal deformation.
5. Establish shoulder/scapula/upper-back deformation.
6. Tune wrist/forearm transition and character twist helpers.
7. Re-run neutral equivalence.
8. Only then proceed to motion activation.

## Neutral equivalence is mandatory

With every new motion feature at zero:
- final bound surface must match the accepted pre-bind geometry to a tight
  numerical tolerance;
- accepted hand/equipment offsets must not drift;
- bare and dressed surfaces must agree;
- no unmapped canonical bones;
- no unexpected helper bones in canonical export;
- bind matrices/nodes/skin structure recorded.

A visually similar rest pose is not enough.

## Hand weighting

The final hand should use:
- metacarpal influence through the palm/finger roots;
- smooth MCP transitions;
- correctly bound thumb base/CMC;
- wrist-to-palm continuity;
- preserved fingertip/contact shape.

Do not activate palm cupping or thumb twist yet.

After hand weighting, re-run the previously accepted grip certification if the
surface/handle relationship changed materially.

## Shoulder/scapula weighting

Introduce explicit scapula deform influence only on the final accepted topology.

Goals:
- scapular region can translate/rotate under later rhythm without a spike;
- deltoid/upper-arm weighting does not tear away from torso;
- axillary fold compresses smoothly;
- upper back/chest remain stable at rest.

Scapula rotations remain zero during this phase.

## Weight safeguards

Record:
- influence count distribution;
- normalization error;
- zero/unweighted vertices;
- left/right weight symmetry;
- maximum rest-surface difference;
- protected hand-contact difference;
- equipment/grip offsets.

Do not hide weight defects with pose correctives until the base weighting is
understood.

## Validation

Against the latest source HEAD:
- full source suite clean;
- frozen hierarchy test;
- importer/unmapped-bone diagnostics;
- palm mapping;
- mirrored hand orientation;
- all exercise validity/technique;
- floor/feet/bench contacts;
- self-collision;
- equipment clearance;
- bare/dressed equivalence;
- exported playback agreement.

Generate deformation reviews for the entire current exercise library, with
close-ups for hand, wrist, elbow, shoulder, axilla, scapular region and knees.

## Output

Produce:
- editable final-bound Blend;
- dressed/bare GLBs;
- binding manifest with hashes;
- explicit bone mapping;
- weight audit;
- neutral-equivalence report;
- current-source integration report.

No scapular rhythm, palm cupping or new thumb exercise motion yet.
