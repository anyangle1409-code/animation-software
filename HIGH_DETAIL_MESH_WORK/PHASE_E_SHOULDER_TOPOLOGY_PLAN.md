# Phase E — shoulder / back / chest / armpit topology plan

## Gate

Dormant until the accepted hand and appearance source are known.

This is **mesh/topology work only** around the frozen shoulder girdle. Scapular
rhythm stays OFF and no exercise is changed to hide a mesh problem.

## Frozen structure

Target the structurally frozen:
- `hgpt_canonical_v3`
- 63 canonical bones
- freeze commit `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`
- scapula between clavicle and upper arm
- no canonical twist bones
- character-specific forearm twist remains outside the hierarchy

Do not move/add/re-parent canonical joints.

## Why this phase exists

The final mesh needs topology that can later deform around:
- deltoid cap;
- clavicle/acromion;
- upper chest/pec insertion;
- lat/upper back;
- scapular region;
- axillary fold/armpit.

The scapula structure is already present, but final scapula deform weighting has
deliberately been held until a candidate mesh can support it.

## Geometry goals

At rest:
- shoulder cap centred naturally around the humeral chain;
- no pointed/flat shoulder seam;
- believable anterior/posterior deltoid transition;
- continuous pec-to-deltoid and lat-to-arm topology;
- clean axillary fold with enough loops to compress/extend;
- upper-back topology capable of scapular deformation later;
- left/right symmetry unless measured anatomy justifies otherwise.

In pose:
- no armpit spike in press/pull-up/front/lateral raise;
- no chest/upper-arm interpenetration caused by the mesh;
- no collapsing deltoid at overhead elevation;
- push-up/bench/fly chest and shoulder surfaces remain believable.

## Current known body-level integration context

The accepted high-detail body already differs from production in arm/chest
clearance, and the current coordination report records:
- several small but positive arm-to-trunk gaps;
- an incline-curl dumbbell/thigh graze;
- bench support compression near its current limit.

Those are baseline context. A shoulder candidate must not silently worsen
unrelated body/equipment measurements.

## Candidate method

Work on a separate preserved candidate.

Prefer:
- connected anatomical edge flow;
- enough loops around deltoid/axilla/scapula to support deformation;
- local topology replacement rather than pose offsets;
- stable UV strategy;
- symmetry tools with explicit post-check.

Preserve accepted hand/knee geometry exactly outside the shoulder topology scope.

## Static validation

Before posing:
- no degenerate triangles;
- no >2-face nonmanifold edges;
- no accidental open holes;
- no unrelated vertex movement;
- left/right correspondence measured;
- rig/skin/material metadata unchanged for geometry-only trial.

## Pose review set

At minimum:
- neutral front / side / three-quarter / back;
- curl Bottom / Peak;
- shoulder press Bottom / Half / Overhead;
- seated shoulder press;
- pull-up Bottom / Top;
- front raise;
- lateral raise;
- push-up Top / Bottom;
- bench press;
- dumbbell fly;
- bent-over row.

Use matched camera/lighting and close-up axilla/deltoid/back views.

## Full integration

Run the latest-source character-switched gates and mesh coordination report.
Any new body/equipment regression is a candidate problem unless proven to come
from a newer source baseline measured on the same HEAD.

Do not re-record collision baselines merely to make a candidate pass.

## Stop conditions

Stop instead of compensating if:
- a joint must move;
- scapular rhythm is required just to make the static candidate look acceptable;
- an exercise/contact/equipment transform must change;
- unrelated hand/knee/body geometry moves;
- topology becomes clean only by deleting required deformation structure.

## Output

Record exact geometry scope, hashes, topology stats, current-source HEAD,
coordination measurements and matched shoulder/axilla boards.

No final weighting or motion activation yet.
