# ORIGINAL v1 whole-body human-motion realism audit

## Purpose

This audit closes the gap between numerical deformation health and a body that
actually looks human while moving.

A candidate can pass edge-ratio, volume, contact and self-intersection gates and
still show an implausible chest, axilla, shoulder, back, groin, knee, elbow,
wrist, hand or other body transition. Therefore numerical deformation results
remain necessary but are **not sufficient** for anatomical acceptance.

This protocol applies to `HomeGymPT_Male_ORIGINAL_v1` and is additive to the
existing Phase 3/4 deformation evidence and Phase 5 anatomy packages. It does
not weaken, replace or re-pin any existing baseline, tolerance, pose or
production gate.

The audit must be bound to an exact candidate SHA-256. A result from one
candidate cannot be inherited by a later candidate unless the relevant geometry,
weights, rig and pose definitions are proven unchanged.

## Core rule

**The entire body must be reviewed as a moving human system, not as a collection
of isolated static meshes.**

Every major region and every joint transition must be observed in:

1. neutral/rest;
2. a lengthened or elevated state;
3. a shortened/compressed or loaded state;
4. at least one transition frame between endpoints;
5. a whole-body silhouette view;
6. a regional close view when the transition is visually important.

Endpoint images alone are insufficient.

## Human-reference method

External human references are observation evidence only. They must never be used
as source geometry, textures, scans, projections, image planes, transferred
weights, bind data or copied coordinates.

For each motion family under review, use multiple real-human references where
possible:

- real exercise video or sequential photography showing the movement through
  time;
- anatomy/kinesiology references that explain which structures move, rotate,
  shorten, lengthen, slide or become more/less prominent;
- more than one adult subject/body type when practical, to avoid treating an
  individual anatomy quirk as a universal target;
- front/rear/side/three-quarter views where the region cannot be understood from
  one angle.

Record observations, not pixels. A useful observation is for example:
"as the humerus elevates, the anterior axillary fold rises and changes angle
while the pectoral mass stays continuous with the chest; the armpit does not
become a rigid circular hole."

Do not require bodybuilding striation, extreme vascularity or identity-specific
surface detail. The target remains an athletic everyday adult male suitable for
exercise instruction.

## Realism dimensions

Every reviewed state is assessed independently across these dimensions.

### 1. Skeletal plausibility

- Joint centres and limb paths remain mechanically credible.
- The visible skin surface follows the locked rig rather than appearing detached
  from it.
- Bony landmarks remain in plausible relationships to surrounding soft tissue.
- No surface correction may disguise a genuine skeletal defect.

### 2. Volume behaviour

- Major masses retain plausible volume while changing shape.
- A muscle or soft-tissue mass may flatten, broaden, shorten, lengthen or shift,
  but must not disappear, inflate abruptly or form a rigid balloon.
- Torso breathing-like elasticity is acceptable; implausible rigid ribcage
  collapse is not.
- Left/right volume behaviour should remain coherent unless an explicit
  asymmetrical pose demands otherwise.

### 3. Soft-tissue sliding and attachment

- Skin and muscle envelopes slide around joints rather than behaving like welded
  plates.
- Attachments remain coherent: pec-to-deltoid, deltoid-to-upper-arm,
  lat/triceps/posterior axilla, glute-to-thigh, calf-to-Achilles, palm-to-finger
  and similar transitions.
- No region may visibly detach, cave into an anatomical void, or develop a
  floating lobe.

### 4. Fold and crease behaviour

- Folds appear where compression creates them and relax when compression is
  removed.
- Joint creases are directional and soft, not fixed rings.
- No fold should persist identically through unrelated joint states.
- Deep creases may not self-intersect, knife-edge, tunnel or form an artificial
  circular pit.

### 5. Silhouette continuity

- The outside contour remains recognisably human at normal app distance.
- Joint transitions are smooth enough to read as continuous anatomy while still
  preserving useful landmarks.
- No pose may create a sudden shelf, notch, spike, dent or cylindrical hinge
  unless real anatomy supports it.

### 6. Surface continuity

- No pinching, crumpling, faceting, inverted-looking patch, unexplained
  depression or stretched sheet is visible in the standard close views.
- Normals/topology artifacts must be distinguished from weight or shape-key
  artifacts before fixing.

### 7. Motion continuity

- Intermediate frames matter as much as endpoints.
- Shape change should progress continuously across the motion.
- A corrective that looks good only at one endpoint but pops, snaps or overshoots
  during the transition fails.

### 8. Contact and load response

- Hands, feet and equipment contacts remain physically credible.
- Loaded palm/wrist, forefoot, heel and shoulder/torso contact areas must not
  collapse merely because a cosmetic corrective fires.
- Contact preservation remains governed by the existing measured contact gates.

## Mandatory whole-body regions

The machine-readable plan in
`ORIGINAL_V1_HUMAN_MOTION_AUDIT_PLAN.json` is authoritative for coverage.

At minimum review:

- head / neck / trapezius transition;
- clavicle / shoulder / deltoid;
- chest / pectorals / anterior axilla;
- scapular back / lats / posterior axilla;
- ribcage / abdomen / obliques / lumbar;
- upper arm / elbow;
- forearm / wrist;
- palm / thumb web / fingers;
- pelvis / groin / glute;
- thigh / knee;
- calf / ankle / Achilles;
- foot / toes.

The anterior and posterior axilla are explicit review zones, not incidental parts
of "shoulder".

## Axilla/chest-specific required sweep

The chest/armpit defect that triggered this protocol must be reviewed through an
arm-elevation sweep, not only the named exercise endpoints.

Required qualitative checkpoints on each side:

- arm low / near neutral;
- approximately 45 degrees elevation;
- approximately 90 degrees elevation;
- approximately 120 degrees elevation;
- approximately 150 degrees elevation;
- near-full overhead;
- return transition.

At each useful checkpoint inspect:

- pectoral-to-deltoid continuity;
- anterior axillary fold;
- axillary hollow depth and shape;
- posterior axillary fold / lat-triceps transition;
- deltoid cap volume;
- chest wall continuity;
- scapular/back drape;
- crease appearance and disappearance;
- symmetry;
- absence of lobe, shelf, tunnel, hard pit or collapsed membrane.

Existing exercise poses such as press and pull-up remain important, but they are
samples of the sweep rather than substitutes for it.

## Movement-family coverage

Do not prove realism only on the five original exercises. The audit should cover
movement families broad enough to exercise the body mechanics:

- vertical push / overhead elevation;
- vertical pull / overhead hang;
- horizontal pull;
- horizontal push / loaded shoulder extension;
- elbow flexion and extension;
- forearm/wrist loading and rotation;
- grip open/close and loaded grip;
- squat/deep bilateral hip-knee flexion;
- split stance/lunge;
- hip hinge;
- ankle dorsiflexion/plantarflexion under load;
- trunk flexion/extension and controlled rotation;
- neutral standing control.

Where a current exercise pose is unavailable, use a deterministic audit pose or
motion sweep. Such audit poses are validation evidence, not new exercise
definitions and must not silently alter runtime biomechanics.

## Severity

### CRITICAL

A visually impossible or safety-relevant deformation, including:

- apparent dislocation;
- major body-part interpenetration;
- gross collapse/inversion;
- broken equipment/floor contact;
- topology/normal failure that makes anatomy unreadable;
- a corrective that destabilises multiple unrelated regions.

**Effect:** blocks the affected candidate from progressing.

### HIGH

Clearly non-human anatomy visible at ordinary review distance, including:

- deep artificial axillary tunnel/pit;
- major pec/deltoid separation;
- obvious shoulder, groin, knee, elbow or wrist collapse;
- persistent shelf/lobe that should change with motion;
- severe popping between intermediate frames.

**Effect:** blocks acceptance of the affected region and must be repaired or
explicitly rejected before final Phase 5 anatomy acceptance.

### MEDIUM

Noticeable close-view problem that does not destroy the main silhouette, for
example a local crease, mild faceting or secondary form behaving incorrectly.

**Effect:** remains open in the defect ledger. It may not be silently ignored;
resolution or explicit disposition is required before production freeze.

### LOW

Minor tertiary/presentation issue with no meaningful silhouette, anatomical,
contact or motion consequence.

**Effect:** tracked for polish; does not by itself block regional progression.

Severity must describe the visual/anatomical defect, not how easy the fix is.

## Defect-ledger rule

Every observed issue receives an immutable defect ID and records:

- exact candidate revision and SHA-256;
- body region and side;
- movement family / pose;
- frame or motion percentage;
- camera/capture ID;
- severity;
- concise observed defect;
- expected human behaviour;
- reference observations;
- suspected cause, clearly labelled as a hypothesis;
- before evidence;
- status: `OPEN`, `FIX_IN_PROGRESS`, `FIXED_VERIFIED`,
  `ACCEPTED_LIMITATION` or `REJECTED_CANDIDATE`;
- fix candidate and after evidence when applicable;
- numerical regression/contact result after any fix;
- owner review state separately from engineering verification.

A defect is not `FIXED_VERIFIED` because one image looks better. The candidate
must pass the relevant motion sweep and regression/contact checks.

## Repair discipline

1. Diagnose whether the defect originates in rig motion, skin weights, topology,
   shape keys/correctives, normals, or a combination.
2. Declare the local edit scope before editing.
3. Preserve the direct parent.
4. Make the smallest mechanically justified change.
5. Re-render the affected motion sweep including intermediate frames.
6. Run existing numerical deformation/contact checks.
7. Compare against the direct parent, active epoch baseline and Phase 4 freeze.
8. Record any improvement and any regression separately.
9. Never weaken a threshold or re-pin a baseline to make a visual fix pass.
10. Never hide a body failure with clothing, lighting, crop or material changes.

## Exit rule

Whole-body motion realism is not complete until:

- every mandatory region has the required state coverage;
- every mandatory movement family has been exercised;
- every CRITICAL/HIGH defect is resolved or the affected candidate is rejected;
- MEDIUM defects are resolved or explicitly dispositioned;
- no fix introduces a new development blocker, contact failure or material
  predecessor regression;
- real renders are candidate-bound and reproducible;
- the final regional/whole-body owner review is recorded separately from
  engineering verification.

Passing this audit is still **not** production approval. Production approval
remains Phase 12 and requires all later gates.
