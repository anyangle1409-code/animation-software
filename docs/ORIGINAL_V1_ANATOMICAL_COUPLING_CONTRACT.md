# ORIGINAL v1 anatomical coupling contract

This contract implements a non-negotiable requirement of the ORIGINAL-v1 human
body plan:

> **When a skeletal segment moves, every anatomically connected muscle/soft-tissue
> system that should respond must respond coherently, while tissue that should
> remain rooted must remain rooted.**

A visually plausible endpoint is not enough. The connection must remain human-like
through the entire motion and return path.

The machine-readable authority is
`ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json`.

## Why this exists

The r95 shoulder/chest/axilla failure demonstrated that a model can pass numerical
deformation gates while the underlying surface ownership is anatomically wrong.
In r95, the base weights pull a broad lateral torso/axilla surface toward the arm,
then corrective keys partly hide that error by creating a membrane/trench/pec
collapse.

This contract prevents the same class of error elsewhere in the body.

## Shared-tissue principle

A muscle or soft-tissue chain that spans two or more attachment regions may not be
treated as if it belongs only to the most mobile bone.

Examples:

- the pectoral chain remains rooted to chest/clavicle while its humeral insertion
  follows the upper arm;
- the posterior axillary chain remains supported by trunk/scapular anatomy while
  its distal side follows the humerus;
- the deltoid is coupled between clavicle/acromion/scapular spine and humerus;
- the rectus femoris responds to both hip and knee state;
- hamstrings respond to the combination of hip and knee state;
- gastrocnemius responds to both knee and ankle state and remains continuous into
  the Achilles/calcaneus chain;
- flexor tendons/finger surface remain coupled from palm/forearm through the
  phalanges rather than behaving as isolated hinge cylinders.

## Required proof for every coupling system

Each coupling system must be validated using an exact candidate SHA and must show:

1. **both attachment sides** and any intermediate surface path;
2. **weights-only deformation** before corrective masking;
3. outbound intermediate samples;
4. end state;
5. return samples;
6. relevant whole-body and close regional views;
7. local and whole-body numerical regression checks;
8. contact/load checks where applicable;
9. explicit links to any Critical/High defects;
10. engineering disposition and owner-review state kept separate.

No static pose or endpoint-only image can close a coupling system.

## Universal invariants

### Attachment continuity
The surface immediately around each anatomical attachment remains continuous with
the bone/region it belongs to.

### Shared ownership
Influence transitions between attachment sides are gradual. A weight map must not
create an artificial ownership seam that becomes a shelf, notch, trench, pit,
membrane or pinch.

### Lengthening/compression
When joint configuration lengthens a multi-joint chain, the visible path must
lengthen/flatten/redistribute plausibly. When the chain shortens/compresses, the
visible form may thicken or fold, but may not collapse or teleport.

### Volume redistribution
Volume is allowed to change shape. It is not allowed to vanish from one end and
reappear at another, balloon abruptly, or be dragged wholesale by one joint.

### Fold logic
Folds are mechanical consequences of compression. They must change continuously
and relax when the compression is removed.

### Corrective discipline
Correctives refine a plausible weights-only result. A corrective that merely hides
a bad foundation fails even if the final endpoint image looks better.

### Reversibility
Returning through the same motion must remove transient folds/deformations and
return to the neutral surface within declared tolerance.

### Bilateral consistency
Equivalent mirrored inputs must produce equivalent anatomical coupling unless an
intentional asymmetry is declared.

### Contact/load propagation
A load at the hand or foot must remain visually/mechanically connected through the
wrist/forearm or ankle/calf chain.

## Coupling systems

The machine map currently defines fourteen whole-body coupling systems:

1. cervical → trapezius → shoulder girdle;
2. pectoralis major / anterior axillary chain;
3. latissimus/teres / posterior axillary chain;
4. deltoid shoulder yoke;
5. upper-arm/elbow multi-joint chain;
6. forearm/wrist/hand load chain;
7. finger flexor/tendon/skin chain;
8. ribcage/abdomen/lumbar/pelvic cylinder;
9. glute/pelvis/femur/lateral-thigh chain;
10. pelvic/adductor/groin/thigh chain;
11. quadriceps/rectus/patella chain;
12. hamstring/pelvis/thigh/popliteal chain;
13. gastrocnemius/soleus/Achilles/calcaneus chain;
14. ankle/hindfoot/arch/forefoot contact chain.

Together they cover every mandatory body region and every movement family in the
human-body master plan.

## Acceptance consequence

An unresolved Critical/High failure in any required coupling system blocks:

- that regional foundation;
- dependent whole-body movement proof;
- high-detail anatomy for that region;
- production deformation validation;
- final production freeze.

A numerical phase checkpoint or attractive material/render cannot override this.

## Current priority

The first coupling systems to execute are:

- `CP-PEC-AX-002`
- `CP-POSTAX-003`
- `CP-DELTOID-004`
- `CP-NECK-TRAP-001`

because r95 already has Critical/High shoulder/chest/axilla defects.

The shoulder-layer diagnostic should be run before editing so the first failing
weights/support boundary can be identified. The new candidate must prove its
weights-only elevation sweep before new corrective fitting.
