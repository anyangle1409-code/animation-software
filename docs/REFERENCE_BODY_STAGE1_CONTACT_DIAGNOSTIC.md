# Stage 1 — curl Bottom/Return contact root-cause diagnostic

**Branch:** `chatgpt/absolute-retarget-imports`  
**Starting head:** `eb474d9a5ea6633dd86837d69d06fab9f6254932`  
**Do not promote, merge, freeze Stage 1, or start Stage 2 yet.**

Current candidate remains:

- `HomeGymPT_Male_STAGE1_CANDIDATE.glb`
- SHA-256 `c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb`

The Stage 1 forearm correction is retained. The new character-specific `handleGripOffsets` work is also retained in principle: renderer and exporter now agree exactly and the handle sits correctly inside the 85%-closed fist. The solver remains in canonical space because equipment is resolved before the character pose is applied; do not restructure that pipeline unless this diagnostic proves an actual error caused by it.

The remaining blocker is the real dumbbell/body penetration at **Curl Bottom and Return**. Do not attempt another fix until the root cause is measured.

## What is already known

With the retained character-aware handle offset:

| Frame | plate/body L / R |
|---|---|
| Bottom | -13.59 / -13.73 mm |
| Mid lift | +174.56 / +174.62 mm |
| Peak | +189.41 / +189.41 mm |
| Mid lower | +200.07 / +200.13 mm |
| Return | -13.59 / -13.73 mm |

The current 3° curl abduction is not an obvious control for this collision. A sweep through 5°, 6°, 7°, 8°, 9° and 11° did not produce a monotonic increase in clearance and no tested angle cleared the contact. Nothing from that sweep was retained.

The hand itself is already close to the body at Bottom/Return. The earlier hand-to-leg surface distances were only a few millimetres, while the inboard dumbbell plate extends about 92.5 mm from grip centre. Therefore the next step is to determine exactly **what body region is colliding and why the expected shoulder-abduction change does not translate the held weight cleanly away from it**.

## Diagnostic only — no retained motion change yet

Use the existing real-character diagnostic and real dumbbell geometry. At **Bottom and Return**, and for a small comparison sweep including at least the current 3° plus representative values from the prior sweep, record the following on both sides:

1. shoulder joint world position;
2. elbow joint world position;
3. wrist/hand joint world position;
4. resolved character hand-frame origin;
5. character `handleGripOffset` world position / true grip centre;
6. dumbbell world transform and centre;
7. inboard plate centre, axis/orientation and nearest plate surface point;
8. exact closest body surface point/triangle to the inboard plate;
9. identity of the body region owning that triangle:
   - upper thigh;
   - hip/pelvis;
   - groin/upper-thigh transition;
   - glute or another region;
10. signed closest plate-to-body distance;
11. signed/unsigned grip-centre-to-body-surface distance;
12. lateral world-space displacement of shoulder, elbow, hand, grip centre and plate centre relative to the current 3° pose;
13. change in dumbbell orientation relative to the hand and world axes.

Do not summarise the collision as "thigh" unless the closest triangle actually belongs to the thigh region. Identify the real geometry that is being penetrated.

## Trace the kinematic data flow

Explain why changing curl abduction from 3° to the tested values does **not** monotonically move the hand/weight clear.

Trace, in order, the values/rules that determine the Bottom pose through:

- authored curl shoulder/clavicle/upper-arm values;
- retarget/application order;
- elbow and forearm orientation;
- wrist/hand transform;
- `gripFrameOffsets` palm-contact frame;
- `handleGripOffsets` held-handle centre;
- equipment attachment transform.

For each boundary, compare the input and output transform. Find where the expected lateral displacement is being reduced, rotated, cancelled, or redirected.

Do not change multiple variables to see what "looks better". This is a root-cause investigation.

## Classify the root cause before fixing anything

The diagnostic should finish by assigning the blocker to one of these evidence-backed categories, or a more precise category if the data demands it:

### A. Hand path too close to body

The grip centre itself remains too close to the real hip/thigh surface at Bottom/Return. If so, quantify the **minimum lateral hand/grip translation** required for the real inboard plate to clear with a small safety margin.

Do not yet decide which joint should create that translation.

### B. Dumbbell orientation causes the collision

The hand/grip moves outward but the dumbbell rotates so its inboard plate remains or becomes embedded. If so, identify the exact attachment/orientation rule responsible and quantify the difference between expected and actual plate motion.

Do not change the arm motion to compensate for an equipment-orientation error.

### C. Collision is actually hip/pelvis/groin, not thigh

If the nearest penetrating geometry is above the thigh, report the true region and the required spatial clearance around it. A generic shoulder-abduction adjustment may be the wrong anatomical control.

### D. Curl pose coupling cancels the intended abduction

If the authored abduction is subsequently counteracted by clavicle, shoulder, elbow, retarget or contact logic, identify the exact transform/rule where this happens and quantify how much lateral movement is lost.

Fix the responsible rule rather than adding a larger arbitrary angle upstream.

## Evidence required

Produce a concise table for each tested Bottom pose with at least:

- authored abduction;
- shoulder x/z;
- elbow x/z;
- grip-centre x/z;
- inboard plate-centre x/z;
- nearest body region;
- hand/grip-to-body distance;
- plate-to-body clearance/penetration;
- dumbbell orientation change versus 3°.

Also provide one diagnostic image for the retained 3° pose showing:

- shoulder, elbow, wrist/hand and grip-centre markers;
- dumbbell and inboard plate;
- highlighted closest body triangle/region;
- line/segment connecting the closest plate/body points.

A second image may be used only if it materially helps explain the non-monotonic abduction sweep.

## Hard guardrails

During this diagnostic:

- retain the corrected 14.86% forearm proportion;
- do not move the shoulder chain;
- do not change Stage 2/canonical shoulder width;
- do not change grip closure from 85%;
- do not change elbow corrective from 0%;
- do not alter elbow-flexion timing/profile;
- do not alter supination timing/profile;
- do not alter accepted clavicle behaviour;
- do not change dumbbell geometry;
- do not nudge the dumbbell by eye;
- do not retain a new abduction value just because one sampled frame numerically improves;
- do not weaken tests or validation thresholds;
- do not fix the push-up yet.

Temporary diagnostic instrumentation/scripts are fine; remove or clearly isolate them before the final retained change later.

## Stop point

**Stop after identifying and proving the root cause. Do not implement the contact fix in the same pass unless the root cause is unambiguous, the required change is singular/minimal, and the existing guardrails explicitly permit it. Otherwise report the diagnosis first.**

Return with:

- branch HEAD;
- root-cause category and evidence;
- exact closest body region at Bottom/Return;
- transform table across the abduction sweep;
- why the previous sweep was non-monotonic;
- minimum geometric clearance required at the grip/plate level;
- the single smallest next change you would test, without bundling other changes;
- confirmation Stage 1 is still not frozen and Stage 2 has not started.

**Do not promote or merge.**
