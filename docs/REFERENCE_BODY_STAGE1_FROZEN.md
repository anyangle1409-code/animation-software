# Stage 1 — frozen

Per `docs/REFERENCE_BODY_ONE_PASS_COMPLETION.md`, Stage 1 is **frozen** as the
baseline for Stage 2. Nothing promoted or merged.

| Asset | SHA-256 |
|---|---|
| `HomeGymPT_Male_STAGE1_CANDIDATE.glb` | `c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb` |

Retained:

- forearm proportion corrected to 14.86% of figure height, with the bind and
  surface correction;
- character-specific `handleGripOffsets`;
- renderer/exporter grip placement agreement (0.0000 mm);
- curl neutral rebase, `startPose.upperarm_l/r.x = 4.3°` and
  `peakPose.upperarm_l/r.x = 8.3°`, the relative curve unchanged by exactly
  +4.3° throughout;
- curl Bottom/Return dumbbell-to-thigh contact cleared to +1.74/+1.82 mm with
  zero vertices inside;
- elbow flexion, supination, timing and easing, clavicle behaviour and 3°
  abduction otherwise unchanged;
- grip closure 85%, elbow corrective 0%.

The solver/canonical-space limitation is accepted for Stage 1 under the existing
diagnostic allowance.

# Phase 1 — full-fist grip: diagnosed, not locked

Work in progress, nothing retained. The measurements below are recorded because
they narrow the problem considerably, and because two of my own harnesses
disagreed and that is worth writing down rather than repeating.

## What is established

**The handle intersects the hand at every placement and every closure.**
Searching the whole hand-local grid for the handle centre that minimises
penetration while keeping at least 300° of wrap, the best available is:

| | value |
|---|---|
| best centre (hand-local, left) | (19.0, 55.0) mm |
| deepest penetration, whole hand | 6.76 mm, 29 vertices |
| deepest penetration, fingers only | 4.61 mm, 2 vertices |
| wrap coverage | 344° |

The current shipped offset is (17.4, 54.2) mm — within 2 mm of that optimum. So
the handle placement is close to as good as this hand allows.

**The binding constraint is the palm, not the fingers.** The 29 penetrating
vertices are palm-weighted, and the palm does not move with closure, which is
why sweeping closure from 0.45 to 0.85 leaves the penetration figure unchanged
at 6.76 mm. A handle sunk a few millimetres into the palm is normal and reads as
a firm grip; fingers passing through it is what reads badly, and only 2 finger
vertices do.

**Closure does reach the character.** Traced end to end: canonical
`middle_02_l.z` goes 38.00° → 80.75° between closure 0.4 and 0.85, the
character's own bone moves 23 mm and a surface vertex dominated by that bone
moves 41 mm. Earlier sweeps that appeared closure-invariant were measuring the
palm.

## Why it is not locked

My measurements are not yet trustworthy enough to tune against:

- classifying a vertex by its *dominant* bone reports the middle phalanges
  13.5 mm inside the handle; classifying by *summed finger weight* reports
  4.6 mm and two vertices. Those cannot both be right, and the grip verdict
  depends on which is used;
- an earlier "largest inscribed cylinder" solve returned 18.1 mm of clearance at
  (12.0, 39.0), which the direct penetration measurement contradicts — that
  solve used a narrower z slab and a different vertex filter;
- a sweep of five different per-joint finger profiles returned byte-identical
  results, which is a harness fault rather than a finding about the hand.

Tuning a reusable grip profile against a measurement that changes answer with
its own vertex filter would produce a number that looks converged and is not.
The next step is to settle the vertex classification and slab once, validate the
harness against a render at high zoom, and only then tune the profile.

## Status

Phases 2 to 5 — Stage 2 shoulder widening, the full validation pass, the push-up
wrist and forearm package, and the review pack — have **not** been started.
Nothing was promoted or merged and the tracked tree is clean.
