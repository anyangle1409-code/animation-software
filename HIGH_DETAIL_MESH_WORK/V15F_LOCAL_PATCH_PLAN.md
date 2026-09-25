# V15f — local ring/pinky patch reconstruction plan

## Purpose

V15a–e are preserved negative/diagnostic trials. None is accepted.

V15f must **not** repeat:
- V15a's broad radial reconstruction + hundreds of diagonal redirects;
- V15b's whole-hand conservative radial pass;
- V15c/d tracking/BMesh-handle failures;
- V15e's "add more PIP/DIP vertices" strategy.

The evidence now isolates the first modelling target to **ring and pinky**.

## Why ring/pinky first

V15b is the most informative completed trial:

- index L/R >35° sharp-length ratio improved vs V13e;
- middle L/R >35° sharp-length ratio improved vs V13e;
- ring L/R worsened;
- pinky L/R worsened slightly;
- severe >100° fold regression was concentrated in ring.

V13e reference values:

| Digit | >35° sharp-length ratio | >100° fold edges |
| --- | ---: | ---: |
| ring_L | 0.0439085154 | 0 |
| ring_R | 0.0450208767 | 1 |
| pinky_L | 0.0519495243 | 2 |
| pinky_R | 0.0498542961 | 0 |

V15b introduced:
- ring_L: +0.0006904 sharp ratio and +3 severe folds;
- ring_R: +0.0005929 sharp ratio and +1 severe fold;
- pinky_L: +0.0005366 sharp ratio while reducing one severe fold;
- pinky_R: +0.0006873 sharp ratio.

V15e made all four ring/pinky >35° ratios materially worse again.

Therefore **Stage A is ring/pinky only**. Do not touch index/middle until the
ring/pinky topology gate clears.

## Starting point

Always start V15f from **V13e**, never from V15b/e.

Use:

`PREPARE_V15F_LOCAL_PATCH.bat`

This:
1. runs the existing V15 preflight;
2. creates `v15f_deep_hand_rebuild` from V13e if it does not exist;
3. adds non-destructive ring/pinky hotspot groups and guides;
4. opens Blender with the existing V15 Hand sidebar.

No vertex position is changed by the hotspot preparation.

## Diagnostic groups

The V15f hotspot preparation adds, per ring/pinky and side:

- `V15F_<DIGIT>_<SIDE>_GT35`
- `V15F_<DIGIT>_<SIDE>_GT50`
- `V15F_<DIGIT>_<SIDE>_GT75`
- `V15F_<DIGIT>_<SIDE>_GT100`
- `V15F_<DIGIT>_<SIDE>_PIP_HOT`
- `V15F_<DIGIT>_<SIDE>_DIP_HOT`

These are diagnostic selection groups only.

The guide collection `V15F_HOTSPOT_GUIDES` marks the strongest local folds.

## Stage A — ring/pinky topology only

For each side, work in this order:

1. ring;
2. pinky.

Do **not** apply a whole-core radial reshape.

Do **not** globally subdivide the PIP/DIP zones.

Do **not** chase the fold metric by flattening anatomy.

Instead:

- inspect the actual surface around the GT50/GT75/GT100 clusters;
- use the existing V15 CORE/ANCHOR/PIP/DIP groups as the allowed local envelope;
- keep every original tracked vertex;
- reconstruct **faces/edge flow** around the retained vertices;
- prefer clean longitudinal/circumferential flow through the shaft and joint;
- add only the minimum local control vertices needed to support that flow;
- keep anchor transitions fixed;
- preserve surface volume rather than projecting the entire digit to an ellipse;
- preserve visible knuckle volume but remove accidental planar bands/creases.

The editable topology may use quads/ngons. Export triangulation is already
handled later by the prepared pipeline.

## Early gate — before index/middle

After ring/pinky are rebuilt, stop geometry editing and run the Blender audit.

V15f may proceed to index/middle only when all of these are true:

- all original source IDs present;
- all 682 protected contacts exact;
- non-digit geometry/weights exact;
- no new nonmanifold/boundary/degenerate defects;
- total >100° digit folds **<= V13e's 3**;
- ring_L >35° ratio <= 0.0439085154;
- ring_R >35° ratio <= 0.0450208767;
- pinky_L >35° ratio <= 0.0519495243;
- pinky_R >35° ratio <= 0.0498542961;
- matched local Blender inspection shows no new pinching.

The numerical limits are "do not get worse than V13e", not an anatomy approval.

If Stage A misses these gates, repair ring/pinky before touching index/middle.

## Stage B — index/middle only after Stage A passes

V15b proved that a conservative change can reduce index/middle >35° sharpness,
but the full-hand visual result still looked segmented.

Therefore:
- checkpoint the successful ring/pinky state first;
- inspect index/middle directly;
- rebuild only visible problem patches;
- do not blindly rerun the V15b whole-core script;
- audit again before export.

## Export/review gate

Only after the complete Blender audit is clean:

`RUN_V15_POST_EDIT_ALL.bat v15f_deep_hand_rebuild`

Then:

`OPEN_V15_REVIEW.bat v15f_deep_hand_rebuild`

Acceptance still requires:
- technically clean frozen lane;
- current-source integration lane;
- no seam/fold regression;
- visible improvement vs V13e;
- clear improvement beyond rejected V14e;
- explicit visual anatomy acceptance.

Phase C grip work remains held until that point.

## Stop conditions

Preserve/reject V15f instead of compensating if:
- ring/pinky need another whole-core radial projection to look round;
- extra subdivision increases sharp ratios/folds;
- protected or non-digit geometry must move;
- stable source vertices would need to be deleted;
- a validation threshold would need to be loosened;
- exercise/grip/rig/equipment mechanics would need to change.

The purpose of V15f is a **different local topology strategy**, not a stronger
version of V15a–e.
