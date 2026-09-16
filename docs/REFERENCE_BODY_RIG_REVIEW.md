# Home Gym PT — Reference Body Rig Review

**Branch:** `chatgpt/absolute-retarget-imports`  
**Current candidate head before this handoff:** `f7f230cc506ea1d0ecc9de2c9d65d31c6feacab6`  
**Do not promote or merge.**

Read first:

- `docs/REFERENCE_BODY_MATCH.md`
- `docs/REFERENCE_BODY_MATCH_HANDOFF.md`
- latest `AI_CHANGELOG.md`

## Current candidate

| File | SHA-256 |
|---|---|
| `HomeGymPT_Male_REFMATCH_CANDIDATE.glb` | `19f350ad610536c9ebdc76aacba1f8ab22bbf8de3a6e691d327ae99463c52f4c` |
| `HomeGymPT_Male_REFMATCH_CANDIDATE_SHORTS.glb` | `309e751d421a88adc4464c36a20597173694516c442c9af6cfdf19b626a8e7ff` |

The geometry-only pass is useful and should be retained as the starting surface. It improved the torso taper, waist and lower-body match without changing topology, weights, skeleton, inverse binds, accepted motion or exercise definitions.

Do **not** promote it yet.

## Why the next step is skeletal

The reference-fit work established that the remaining dominant mismatch cannot be solved honestly by more surface inflation:

- reference shoulder width: **29.69% of body height**;
- v7 shoulder width: **26.24%**;
- current candidate: **25.74%** after correctly thinning the already-overlarge upper-arm radius;
- reference humerus axis: **10.64% of height from centreline**;
- v7 humerus axis: **8.23%**;
- attachment mismatch: about **2.41% of body height per side**.

The arm-radius measurements show v7 is already thicker than the reference through much of the upper arm. Closing the shoulder span with deltoid mass would require roughly 48 mm of extra radial surface on an already larger deltoid. Do not do that.

Shoulder slope is likewise still off:

- reference: **50.7°**;
- v7: **57.0°**;
- current candidate: **56.8°**.

The run is too short because the shoulder attachment is too far inboard. More shoulder sculpting is not the correct fix.

A second structural mismatch is arm reach: the reference hands hang materially lower in the locked neutral comparison. Treat that as a bone-length/proportion question, not a hand/forearm sculpting target.

## Task — investigation only first

Before changing the rig, quantify the **minimum anatomical skeletal correction** needed to bring the model substantially closer to the supplied reference.

Measure and report:

1. required clavicle/shoulder-joint widening per side in mm and as % total body height;
2. resulting shoulder-to-shoulder span;
3. whether the shoulder slope then reaches the reference within about 2° without further artificial yoke sculpting;
4. upper-arm bone-length mismatch against the locked reference;
5. forearm bone-length mismatch against the locked reference;
6. total arm-reach mismatch and where it comes from;
7. whether humerus/elbow/wrist centres would remain anatomically plausible inside the current refmatch surface after the proposed changes;
8. expected effects on hand position, dumbbell placement, push-up contacts, press, pull-up and curl geometry;
9. which systems/code/data would actually need to change if the proposal were retained.

Use the existing locked reference registration and orthographic comparison. Do not re-scale the photograph by shoulder width or arm length.

## Preserve during the investigation

Do not change yet:

- accepted curl motion or timing;
- global grip closure **85%**;
- elbow corrective **0%**;
- exercise definitions;
- skin weights;
- retargeting implementation;
- current promoted v7/v7-shorts;
- current refmatch candidate;
- v6 or proven v5 fallbacks.

Do not fake the result with deltoid inflation, hand translation, whole-arm mesh stretching or arbitrary exercise offsets.

## Downstream-impact review

A skeletal change is allowed to be considered, but it must be treated as a proportion correction with downstream consequences, not as an isolated cosmetic edit.

For the proposed shoulder widening / arm-length correction, identify what would need revalidation in at least:

- curl bottom / mid / peak;
- shoulder press bottom / overhead;
- push-up top / bottom;
- pull-up bottom / top;
- deepest squat for whole-character regression;
- dumbbell hand attachment and grip-centre stability;
- floor/bar/equipment contact locks;
- left/right symmetry;
- imported-character absolute retarget path;
- export/runtime agreement.

Preserve exercise **intent**. A later retained proportion change may require recalibration of contact/equipment positions, but do not rewrite movement simply to hide the altered proportions.

## Stop point

**Do not implement the skeletal change in this first pass.**

Return one concise proposal containing:

- exact shoulder-joint/clavicle movement proposed per side;
- exact upper-arm and forearm length changes proposed, if any;
- before → proposed joint-centre table;
- projected shoulder width and slope after the change;
- projected neutral hand height/reach;
- expected downstream files/systems affected;
- main risks;
- whether the current refmatch surface can be adapted cleanly or should be regenerated from v7 around the corrected rig.

Include a simple skeleton-over-reference overlay showing **current joints vs proposed joints** before implementation.

The goal is one measured rig decision, not another trial-and-error sculpting round.

**Do not merge. Do not promote.**
