# Phase F — final source-rig binding / weights and canonical retarget intake

## Gate

Dormant until all final geometry decisions are accepted:
- body/knee;
- hand;
- shoulder/back/chest/armpit;
- appearance/material source.

This phase prepares the **final character asset that the frozen canonical rig will drive**.
It must remain a candidate until rest equivalence, mapping and the full exercise library pass.

## Correct architecture

The current production architecture deliberately keeps the imported character's
own authored skeleton, bind pose, inverse binds, helper bones and weights.

`hgpt_canonical_v3` is the **driver**, not the skin skeleton.

The preferred path is therefore:

1. preserve the source character hierarchy and bind;
2. ensure the source rig has correctly placed/weighted deform structure for any
   canonical capability we actually want to drive;
3. map the frozen canonical bones onto those source bones;
4. let the existing retarget layer transfer canonical motion.

Do **not** globally rebind the surface to the 63 canonical bones merely to make
the asset look structurally similar to the driver. The current source documents
why: a previous canonical rebind of a 160-bone Rigify character changed 21.7%
of edges by more than half their length before animation even began.

`rebindToCanonical` exists as a tool, but it is not the preferred production
character path. Use it only if a separately reviewed decision proves it is
required and rest geometry survives.

## Frozen driver target

The mapping target remains:
- skeleton ID `hgpt_canonical_v3`;
- 63 canonical bones;
- freeze commit `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`;
- four canonical metacarpals per hand;
- `thumb_01` as canonical thumb CMC/metacarpal control;
- canonical scapulae between clavicles and upper arms;
- no new canonical bones.

The source character may legitimately contain many more bones.

## Source-rig structure to preserve

Keep working source features that the retargeter intentionally supports:
- face/detail branches;
- connected helper bones;
- character-specific forearm twist helper(s);
- authored source proportions;
- authored inverse bind matrices unless a deliberate local rig repair requires
  a measured update.

The retarget layer currently gives the forearm deform helper a 50% share of
canonical axial twist. Do not create canonical twist bones to replace it.

## Palm/metacarpal requirement

The old production character's exported Rigify palm bones were measured roughly
207–213 mm from their own knuckles and carried no useful weights. The retargeter
therefore rejects implausible palm mappings.

The final source asset must contain **plausibly placed source palm/metacarpal
deform controls with real weights** if visible canonical palm cupping is wanted.

Requirements:
- each source metacarpal lies anatomically inside the palm;
- it drives the appropriate finger root/palm region;
- mapping to canonical `metacarpal_index/middle/ring/pinky_[lr]` passes the
  current palm plausibility checks;
- rest pose is unchanged when those controls are neutral.

Do not falsify the mapping to the old misplaced palm bones.

## Scapula requirement

Visible scapular rhythm later requires a source-side deform structure the
canonical scapula can drive.

The final character must therefore have either:
- existing plausible source scapula deform bones with suitable weights; or
- a deliberately added/repaired source-side scapula deform setup.

Requirements:
- neutral scapula pose reproduces the accepted mesh exactly;
- upper back / deltoid / axillary weights are continuous;
- source hierarchy/helpers remain coherent;
- canonical `scapula_l/r` can map to the intended source controls.

Scapular rhythm remains OFF throughout Phase F.

## Binding/weighting order

1. Preserve the accepted source character rest geometry exactly.
2. Preserve the working source hierarchy/helper structure.
3. Repair/add only the source-side metacarpal/scapula deform controls required
   for final mapping.
4. Paint/tune palm/metacarpal weights.
5. Paint/tune shoulder/scapula/upper-back/axillary weights.
6. Preserve/tune wrist and forearm transition without breaking the established
   twist-helper behaviour.
7. Export the candidate with its **source skeleton** intact.
8. Run the current retarget mapping against `hgpt_canonical_v3`.
9. Prove neutral/rest surface equivalence through the production retarget path.
10. Only then proceed to motion activation.

## Neutral equivalence is mandatory

With new palm/scapula motions at zero:
- character geometry must match the accepted pre-Phase-F geometry at rest,
  beyond only the normal uniform character scale used by the studio;
- accepted hand/equipment offsets must not drift;
- bare and dressed body surfaces must agree;
- source helper bones remain functional;
- canonical-to-source mapping is deterministic;
- no unexpected unmapped weighted source bones;
- no implausible palm mapping;
- mirrored hand orientation remains correct.

A visually similar rest pose is not enough.

## Weight safeguards

Record:
- source bone count and hierarchy hash;
- exactly which source bones were added/repaired;
- inverse-bind changes and why;
- influence count distribution;
- normalization error;
- zero/unweighted vertices;
- left/right weight symmetry;
- maximum rest-surface difference;
- protected hand-contact difference;
- palm/scapula weighted-vertex counts;
- forearm twist-helper detection/share;
- canonical mapping report.

Do not hide a weight defect with a pose corrective until the base deformation is
understood.

## Current-source validation

Against the then-current source HEAD, run at minimum:
- full source suite;
- frozen canonical hierarchy test;
- real-character importer diagnostic;
- unmapped-bone diagnostics;
- palm mapping;
- mirrored hands / hand roll;
- all exercise validity and technique;
- floor / feet / bench contacts;
- self-collision;
- equipment clearance;
- bare/dressed equivalence;
- exported playback agreement;
- full mesh coordination report.

Use the production retarget path, not a special Phase-F-only viewer path.

## Deformation review

Generate close-up matched reviews for:
- open palm and closed fist;
- curl/press/pull-up grips;
- wrist/forearm twist;
- shoulder press Bottom/Half/Overhead;
- pull-up Bottom/Top;
- front/lateral raise;
- push-up;
- bench/fly;
- row;
- neutral and back views of the scapular region.

Palm/scapula controls remain at neutral unless a specific static mapping probe is
being run.

## Output

Produce:
- editable final source-rig Blend;
- dressed/bare GLBs;
- source-rig hierarchy/bind manifest;
- canonical mapping report;
- weight audit;
- neutral-equivalence report;
- current-source integration report;
- hashes and rollback point.

No scapular rhythm, palm cupping or new thumb exercise motion yet.


## Prepared asset audit

A generic source-rig audit is already available:

`AUDIT_PHASE_F_SOURCE_RIG.bat accepted_geometry.glb final_character_candidate.glb`

It verifies the Phase F scope before runtime testing:
- accepted POSITION/NORMAL/UV/COLOR/topology data remain exact;
- non-body/garment mesh data remain unchanged;
- source skin-joint additions/removals are reported;
- no previously weighted source/helper bone silently loses all influence;
- candidate weight sums remain normalized;
- no new unweighted body vertices appear;
- source-joint parent changes are listed explicitly.

It intentionally does **not** require the source character to have exactly 63
skin joints. Canonical mapping/plausibility remains a runtime retarget check.


## Prepared runtime retarget validation

After the raw asset audit passes, validate the accepted reference character and
Phase F candidate through the newest source runtime:

`VALIDATE_PHASE_F_RUNTIME.bat accepted_reference.glb final_candidate.glb phase_f_candidate`

This creates a detached latest-source worktree, requires the source suite to be
clean, then compares reference/candidate on palm mapping, unmapped bones,
mirrored hands, real-character diagnostics, self-collision, equipment clearance
and contact-related family tests. It reports any new failing gate or increased
failed-test count and removes the worktree afterward.
