# Side-view shoulder alignment — diagnosis

**Branch:** `chatgpt/absolute-retarget-imports`
**Executed from:** `be1ad21`
**No geometry, pose, rig or asset change was made. Nothing promoted, nothing merged.**

The brief was to determine whether the anterior shoulder reading comes from the shoulder/upper-arm
joint pose, the deltoid mesh shape, or both, and then make the smallest correction needed to centre
the cap over the upper arm. The measurements say it is the **joint pose, in two separable parts**,
that the **mesh is not at fault**, and that the smallest correction to centre the cap is **zero** —
it is already centred. The part that would change the appearance is blocked by a clearance budget of
less than a millimetre, so it is reported here as a decision rather than taken.

## Conventions

`+z` is the model's front; the character's **left arm is at +x**. All figures in mm, world space, on
the accepted `CORNER_FINAL_SHORTS`. Sides are selected by the dominant bone's own `L`/`R` suffix.

## 1. It is not the curl

`clavicle_l` and `upperarm_l` sit at **identical z at Bottom, Mid and Peak** (28.4 and 15.2 mm).
The shoulder joint does not move through the rep at all, so nothing in the curl's timing or
blending creates the protrusion — consistent with it being visible at both ends of the movement.

Only the elbow moves forward, 35.3 → 55.8 mm, which is the authored 4° late drift for the squeeze.

## 2. It is not the deltoid mesh

Measured as the cap's cross-section **around the humerus axis** (a z-range over shoulder-weighted
vertices is useless here: that set reaches back over the scapula to −113 mm, which drags a centroid
posterior and says nothing about whether the deltoid bulges forward).

Deltoid sleeve, vertices within 70 mm of the axis, sliced along the humerus at Bottom:

| Slice from the joint | n | Centroid forward of axis | Anterior reach | Posterior reach |
|---|---:|---:|---:|---:|
| −5..15 mm (acromion) | 22 | +13.1 mm | +52.4 | **−52.3** |
| 15..33 mm | 20 | +8.5 mm | +51.4 | −56.7 |
| 33..51 mm | 14 | +8.8 mm | +44.4 | −49.9 |
| 51..70 mm | 22 | +6.1 mm | +39.9 | −56.1 |
| whole sleeve | 78 | +9.2 mm | +52.4 | −56.7 |

The **envelope is symmetric about the humerus** — 0.1 mm asymmetry at the acromion, −4.3 mm over
the whole sleeve, and what asymmetry there is leans *posterior*, not anterior. The mass carries a
forward bias that decays smoothly from +13.1 to +6.1 mm down the arm. That is a gentle gradient, not
a bulge, and a fuller anterior head over a flatter posterior one is what a real deltoid does.

**Nothing in this phase's work created it.** The figures are identical, to 0.1–0.5 mm, in:

| Asset | Sleeve centroid | Shoulder z | Humerus tilt |
|---|---:|---:|---:|
| `CORNER_FINAL_SHORTS` (accepted) | +9.2 mm | 15.2 | 3.87° |
| `BASELINE_v9_CANDIDATE_SHORTS` (Phase A) | +9.6 mm | 15.2 | 3.87° |
| `BASELINE_v8_SHORTS` (promoted production) | +9.6 mm | 15.2 | 3.87° |

So the Phase A normals repair, the skin pass, the round 2–5 torso/pec/shoulder work, the face
candidate and the Stage 1 muscle layer are all exonerated. Left and right agree to 0.3 mm.

## 3. It is the joint pose — and it is two things, one inherited, one deliberate

### 3a. The arm root sits forward of the torso, in the imported rest pose

The canonical rig (`src/rig/humanoid.ts:164`) places the chain on the sagittal midline:

```
spine_03    head (0, 1.27, 0)        tail (0, 1.42, 0)
clavicle_l  head (-0.02, 1.42, 0.012) tail (-0.17, 1.44, 0)
upperarm_l  head (-0.17, 1.44, 0)     tail (-0.17, 1.14, 0)   <- z = 0, humerus vertical
```

The imported character's derived rest pose does not:

| | Canonical | Imported (measured) |
|---|---:|---:|
| `spine_03` z | 0 | −41.5 mm |
| `upperarm_l` z | 0 | **+15.2 mm** |
| Shoulder forward of `spine_03` | **0 mm** | **+56.7 mm** |
| Shoulder forward of ribcage mid-depth | — | **+56.8 mm** |

The ribcage near the midline at chest height runs from a sternum at +85.7 to a back surface at
−168.8, so its mid-depth (−41.6) coincides with `spine_03`. The glenohumeral joint therefore sits
**57 mm anterior of the ribcage's mid-depth, 45% of the way to the sternum skin**. That is the
"not in line with the torso" the eye is reading, and it comes from the GLB's own node hierarchy via
`readCharacter`, not from anything authored here.

### 3b. The humerus hangs 3.87° forward at Bottom — deliberately, and load-bearing

`src/exercises/definitions/bicepCurl.ts:53` authors `upperarm_l: { x: 4.55, z: -3 }` at Bottom, and
says why:

> Upper arms hang just clear of the torso. On broad imported shoulders extra abduction reads as a
> shrug at the bottom, so the clearance the hanging dumbbell needs is taken forward instead […]
> 4.3° is the smallest value measured to lift the plate clear (+1.74/+1.82 mm, nothing inside);
> 4.0° still buried it.

So the forward lean is not an oversight. It is the mechanism by which the hanging dumbbell clears
the thigh, chosen over abduction precisely because abduction read as a shrug, and tuned to the
tenth of a degree in an already-accepted round.

## 4. Why the correction that would work is blocked

The anatomically correct lever for a forward shoulder is clavicle retraction. Swept on all three
axes, in the curl's start and peak poses, measured at Bottom:

| Clavicle | Shoulder z | Elbow z | Hand z | Dumbbell↔leg (body only) | Technique |
|---|---:|---:|---:|---:|---|
| **accepted** | 15.2 | 35.3 | 79.8 | **+4.7 mm** | none |
| x −4° | **+1.0** | 23.9 | 70.9 | **−0.7 mm** | none |
| x −8° | −13.1 | 12.6 | 61.8 | **−6.7 mm** | none |
| y ±4°, ±8° | 15.2 (no effect) | 35.3 | 79.8 | +4.7 | none |
| z −4° | 15.4 | 34.1 | 77.5 | +8.0 | ✗ `dumbbells_aligned` |
| z −8° | 15.7 | 33.1 | 75.3 | +11.0 | ✗ `shoulder_relaxed_l`, `dumbbells_aligned` |

`x` is the protraction/retraction axis, worth **3.6 mm of shoulder z per degree**. `y` is the twist
along the bone and does nothing. `z` is elevation: it barely moves the joint and breaks technique.

The problem is that the arm root and the hand are rigidly coupled — retracting the shoulder carries
the hand back with it. Against the garment, measured on the real assets:

| | Dumbbell ↔ shorts at Bottom |
|---|---|
| **accepted** | **+0.48 / +0.64 mm, 0 vertices inside** |
| clavicle x −4° | **−1.14 / −0.69 mm, 2 vertices inside each side** |

The whole budget is half a millimetre. Any retraction large enough to be seen spends it and drives
the dumbbell into the shorts. Reducing 3b instead runs into the curl's own measurement: 4.0° "still
buried it".

## 5. Conclusion and what I did not change

- **Deltoid mesh shape: not the cause.** The cap is already centred on the humerus — 0.1 mm
  envelope asymmetry at the acromion, −4.3 mm over the sleeve, leaning posterior. The smallest
  correction needed to centre it is therefore **zero**, and the 6–13 mm forward *mass* bias is
  normal anterior-deltoid fullness, not a defect.
- **Joint pose: the cause**, split between an inherited rest pose 57 mm forward of the ribcage
  mid-depth (3a) and a deliberate 4.55° of shoulder flexion that keeps the dumbbell off the thigh
  (3b).
- **No correction was made.** Both terms need the bind/rest pose or the accepted curl mechanics to
  change, which `MODEL_APPEARANCE_PHASE.md` explicitly reserves for the user: *"If matching a visual
  feature would require changing rig proportions, weights, topology, bind/rest pose or accepted curl
  mechanics, stop and show the trade-off before doing it."* Shipping a 6 mm cap shift instead would
  have risked the accepted armpit and clavicle work to change the silhouette by almost nothing,
  while implying the protrusion had been fixed.

## 6. Options, with their costs

1. **Leave it.** Zero risk. The shoulder keeps reading forward in side view.
2. **Give the dumbbell room, then retract the clavicle.** The blocker is 0.48 mm of garment
   clearance. Widen the shorts' thigh taper or shorten the plate's inboard offset, then spend the
   freed budget on clavicle retraction. ~4° buys 14 mm of shoulder z. Touches the garment and the
   equipment attachment, not the rig or the curl's arm angles.
3. **Correct the rest pose and re-solve.** Move the imported arm root ~30–55 mm posterior and
   re-solve the grip against the new rest pose. This is the only change that fixes the cause. It
   invalidates the solved-grip metadata, the 252° wrap and the elbow path, so it means redoing the
   grip solve and re-validating the curl end to end.
4. **Mesh-only cosmetic shift** of the cap mass 6–13 mm posterior. Cheap and safe for the curl, but
   it does not move the joint, so the shoulder still sits forward; and it risks the accepted armpit
   and clavicle-shelf work for a change measured in millimetres. Not recommended on this evidence.

## Visual evidence

Rendered in the app on the accepted `CORNER_FINAL_SHORTS`, proven loaded (`import` active), `light`
backdrop, canvas-only frames, same camera and frame in both columns. The "after" column is the
**clavicle −4° candidate**, produced by a temporary edit to `bicepCurl.ts` that was reverted
immediately after capture (`git status` clean, verified).

- `01_left_bottom_ab.png`, `02_left_peak_ab.png` — side, shoulder and upper arm.
- `03_three_quarter_bottom_ab.png`, `04_three_quarter_peak_ab.png` — 3/4, shoulder and upper arm.
- `05_left_bottom_hip_ab.png` — the cost: the plate clear of the shorts in the accepted curl, and
  cutting into them at −4°.

The −4° column does visibly pull the deltoid back over the arm and flatten the forward shoulder
line, which is the useful part of this exercise: it shows the correction is real and shows exactly
what it costs.

## 7. User-supplied anatomical visual target

The user has now supplied a side-view photograph of a muscular person performing a dumbbell curl.
Use that image as a **relationship / alignment reference only**, not as an identity or body-shape
copy target. The same image should be attached to the execution prompt whenever this correction is
worked on, because the important requirement is visual.

The key relationship shown by the reference is:

- the rounded deltoid cap sits **over the humeral/upper-arm axis** rather than visibly ahead of it;
- the upper arm appears to **hang from underneath the shoulder cap**, so shoulder → upper arm reads
  as one stacked anatomical chain;
- the deltoid may have normal anterior fullness, but there is no separate forward shoulder ledge
  with the arm visually trailing behind it;
- the elbow can move slightly forward during flexion without carrying the entire shoulder girdle
  forward;
- at rest/Bottom the upper arm should still read as naturally suspended under the shoulder rather
  than displaced anteriorly to manufacture dumbbell clearance.

This visual target supports fixing the **rest-pose / joint-chain alignment** rather than shifting the
deltoid mesh cosmetically. Do not copy the reference person's exact physique, skin, face, equipment,
or camera perspective.

### User decision after seeing the trade-off

The user has authorised pursuing the **true-fix candidate** rather than retaining the temporary
clavicle/curl workaround:

1. keep the current accepted character + curl completely intact as rollback;
2. create a separate candidate that moves the imported shoulder/upper-arm rest alignment toward an
   anatomically stacked position, using the smallest posterior correction that removes the obvious
   anterior shoulder protrusion when compared with the attached reference;
3. do **not** use a mesh-only cosmetic shift;
4. do **not** keep the temporary −4° clavicle curl edit as the solution;
5. after changing the rest alignment, re-solve the grip/curl against the corrected chain rather
   than preserving the old forward-biased shoulder merely to protect clearance;
6. re-establish grip quality, neutral wrist, natural elbow path, dumbbell/shorts clearance, loop
   continuity and all relevant guards before proposing retention;
7. show matched Bottom/Mid/Peak/Return plus side and 3/4 shoulder close-ups against the attached
   visual target; stop for user review before promotion.

The target is **anatomical stacking first, then re-solving the exercise around it** — not moving the
arm backward blindly and not sacrificing the accepted mechanical quality without evidence.

## Diagnostic harnesses

Gitignored, under `scratchpad/repair/`: `shoulderz.test.mts` (joint chain, ribcage reference),
`capsector.test.mts` (cap cross-section by sector and by slice), `clavsweep.test.mts` (clavicle axis
and angle sweep with clearance and technique).

Two measurement errors were made and corrected on the way, both recorded so the numbers above are
read with the right provenance: the first cap measurement selected the **right** arm's vertices
against the **left** arm's joint frame (`upperarm_l` is at +x, not −x), and the first "torso at
shoulder height" band landed on the **neck and trapezius** rather than the ribcage, which made the
shoulder look 8 mm proud of the chest when it is 70 mm behind the sternum.

## Status

Diagnosis complete. Accepted geometry, rig, curl and assets untouched; `CORNER_FINAL` and the Stage
1 layer are exactly as they were. Stopped for a decision between the options above.

**Not promoted. Not merged.**
