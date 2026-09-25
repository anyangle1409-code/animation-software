# Phase G — activate palm, thumb and scapular movement

## Gate

Dormant until Phase F final binding/weights is accepted and neutral equivalence
is proven.

This phase is **source-side motion work**. It must occur in an isolated branch
from the then-current `chatgpt/absolute-retarget-imports`.

Do not merge source into the mesh review branch.

## Frozen hierarchy remains frozen

No new bones, renames or re-parenting.

Only drive capabilities that already exist:
- metacarpal/palm cupping;
- thumb opposition/pronation/twist within current limits;
- scapular rotation/tilt where the final mesh is weighted for it.

## Activation order

### G1 — palm cupping

Start with very small metacarpal motion in grips that benefit from it.

Requirements:
- no change to open/rest hand;
- no push-up floor-contact regression;
- no grip family gets per-exercise magic numbers;
- metacarpal motion stays inside the frozen joint limits.

Re-run grip certification after activation.

### G2 — thumb opposition / twist

Use the existing thumb-base axes and limits.

Requirements:
- opposition improves pad/handle relationship rather than merely hiding
  penetration;
- both hands mirror correctly;
- no regression to open hand or floor hand;
- current grip solver remains character-scoped where required.

### G3 — scapular rhythm

Activate only after shoulder/scapula weights and topology are proven.

Derive rhythm from arm elevation, not exercise IDs.

Start with a conservative shoulder-elevation mapping and validate:
- press;
- pull-up;
- front/lateral raise;
- fly/bench;
- push-up;
- row.

The scapular contribution must be continuous and reversible through the full
loop; it must not create an armpit spike or detach the arm.

Do not reduce upper-arm range merely to make bad weighting look acceptable.

## Baseline guarantees

At zero/new-feature-off state, every exercise must remain equivalent to the
pre-activation final-bound baseline.

Each activation slice must have an explicit feature switch or revert commit
until accepted.

## Validation per slice

- frozen hierarchy unchanged;
- full current source suite;
- all current exercises;
- bone/equipment/contact comparison outside intended bones;
- self-collision/equipment clearance;
- grip metrics;
- technique rules;
- closed loop;
- exported playback;
- matched close-up visual review.

## Generalisation requirement

The user's end goal is prompt-driven exercise creation. New deformation/motion
logic must therefore be family/biomechanics driven, not hard-coded to individual
exercise IDs wherever a general relationship exists.

Examples:
- scapular rhythm from humeral elevation/plane;
- palm cupping from grip/contact intent;
- thumb opposition from grip family/contact geometry.

## Final acceptance

Only after G1/G2/G3 are individually accepted should they be enabled together.
Run one final full-library integration pass and re-certify prompt-generated
families against the final character.

Keep independent revert points for each activation slice.
