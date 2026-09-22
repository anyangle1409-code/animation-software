# Shoulder alignment — true-fix candidate

**Branch:** `chatgpt/absolute-retarget-imports`
**Executed from:** `b6bacf6`
**Candidate for review. Nothing promoted, nothing merged. The accepted character and curl remain
available as rollback — see "Rollback" below.**

Executes §7 of `SHOULDER_ALIGNMENT_DIAGNOSIS.md`: correct the shoulder/upper-arm **rest alignment**
so the deltoid cap stacks over the humerus and the arm hangs from underneath it, then re-solve the
curl around the corrected chain. No mesh-only shift, and the temporary −4° clavicle pose workaround
is not retained.

## Headline result

| Measure | Accepted | Corrected | Reference target |
|---|---:|---:|---|
| Shoulder forward of `spine_03` / ribcage mid-depth | +56.8 mm | **+19.6 mm** | near mid-depth |
| Humerus sagittal tilt at Bottom | 3.87° | **3.22°** | closer to vertical |
| Dumbbell ↔ shorts at Bottom | +0.48 / +0.64 mm | **+1.99 / +2.15 mm**, 0 inside | positive |
| Grip contacts (fingers / palm / thumb) | −10.75 / −2.54 / −10.35 | **identical** | unchanged |
| Finger wrap | 343° | **343°** | unchanged |
| Renderer vs exporter grip frame | 0.0000 mm | **0.0000 mm** | unchanged |
| Bare ↔ dressed posed equivalence | 0.0000 mm | **0.0000 mm** | unchanged |
| Technique rules / loop | none, closed | **none, closed** | unchanged |

The forward offset is cut by 65%, the humerus ends up *more* vertical than before, and clearance —
the thing that blocked every earlier attempt — is four times better rather than spent.

## Why the asset could not carry the fix

The obvious route was to edit the imported rest pose: move `DEF-upper_arm.{L,R}` posteriorly in the
GLB. That was built (`scratchpad/repair/armroot.mjs`) and is surgical — BIN chunk byte-identical,
only two node matrices changed, skins/extras/meshes untouched — and the rest pose does move:
`upper_arm.L` local z goes −26.70 → −66.70 mm for a 40 mm shift.

**It does not reach the posed character.** Measured Jacobian, 50 mm of rest-space shift along each
axis, against the posed arm root:

| Rest shift | Posed Δx | Posed Δy | Posed Δz |
|---|---:|---:|---:|
| +50 mm x | +40.10 | +0.89 | −2.58 |
| +50 mm y | +0.83 | +0.02 | −0.05 |
| +50 mm z | −13.24 | −0.30 | +0.85 |

That matrix is rank ≈ 1: every rest direction produces posed motion along one world axis (lateral).
A rotation would be rank 3. What survives is only the *magnitude* of the clavicle→shoulder rest
offset — predicted +40.9 mm for the x probe against +40.10 measured, +1.2 against +0.83 for y. The
posed arm root is placed from the **canonical clavicle's frame** at the imported clavicle→shoulder
distance, so the imported rest pose's *direction* is absorbed. A 40 mm posterior asset edit moved
the posed shoulder 1.0 mm.

Confirmed by the forward model: posed clavicle z +28.4, distance 178.4 mm, canonical clavicle
direction z-component −0.079 → 28.4 − 14.1 = **+14.3 mm** predicted against **+15.2 mm** measured.

## What the fix actually is

The canonical clavicle was anatomically wrong. `src/rig/humanoid.ts` ran it from
`head (-0.02, 1.42, 0.012)` to `tail (-0.17, 1.44, 0)` — **4.5° of posterior angle**. A real
clavicle angles back 15–20° from the sternoclavicular joint to the acromion. Running almost straight
out put the whole shoulder girdle, and the arm with it, in front of the ribcage.

The tail moves to `(-0.17, 1.44, -0.035)` — **17.5°** — and the arm chain below follows it so the
chain stays connected and every arm bone still hangs vertical:

```
clavicle_l  tail  (-0.17, 1.44, -0.035)   <- the correction: 4.5deg -> 17.5deg posterior
upperarm_l  head/tail  z = -0.035          <- follows, still vertical
forearm_l   head/tail  z = -0.035
hand_l      head/tail  z = -0.035
```

The five finger knuckles are **absolute world rest positions**, so they move with the chain too.
Leaving them behind tilts the hand's measured axis by `atan(0.035 / 0.09) = 21.3°`, because the palm
axis is derived from the mean knuckle position rather than the hand bone's tail — that was 4 of the
13 test failures the first attempt produced, including all three movement certifications.

This is a rest-alignment change, applied once in the rig every character retargets through. It is
not a mesh shift and not a pose workaround.

## Re-solving the curl around it

Pulling the arm root back carries the hand back, which costs dumbbell clearance. The accepted curl
bought clearance by tilting the humerus forward 4.55° — but doing that again would reinstate exactly
what the correction removes. Abduction was re-tested rather than inherited, and still fails:
every abduction ≥ 0 breaks `upper_arm_clear_l/r`, so the original author's finding holds.

The lever that works is the **elbow**. Bending it at the bottom lifts the plate off the leg without
tilting the humerus at all:

| clavicle z | flexion | elbow start | sh−spine | tilt | clearance (body) |
|---|---:|---:|---:|---:|---:|
| accepted (0) | 4.55 | 6 | +56.8 | 3.87° | +4.7 |
| −0.035 | 4.55 | 6 | +19.6 | 4.77° | −7.6 |
| −0.035 | 4.55 | 12 | +19.6 | 4.77° | +3.9 |
| −0.035 | 3 | 14 | +19.6 | 3.22° | +2.2 |
| **−0.035** | **3** | **16** | **+19.6** | **3.22°** | **+9.7** |

Retained: `upperarm x 4.55 → 3` (Bottom) and `8.55 → 7` (Peak, keeping the authored 4° late drift),
and the elbow's Bottom angle `6° → 16°`. A soft elbow at the bottom of a dumbbell curl is what a
lifter actually does; locking out is the exception. Range becomes 16° → 126°.

## Validation

All curl-scoped checks pass, on the accepted `CORNER_FINAL_SHORTS`:

```
DUMBBELL_CLEARANCE Bottom  l: 1.99 mm (0 in)   r: 2.15 mm (0 in)
GRIP metric Bottom: fingers -10.75/46  palm -2.54/2  thumb -10.35/24  wrap 343
VIOLATIONS: none        LOOP CLOSED: true
DRIFT Bottom l 0.000000  r 0.000000  elbow 16.000
DRIFT Peak   l 4.000000  r 4.000000  elbow 126.000
DRIFT Return l 0.000000  r 0.000000  elbow 16.000
GRIP_AGREE t=0/2/4 l+r: rendered vs exported 0.0000 mm
EQUIV posed hand 0.0000 mm; posed body 0.0000 mm over 10839 vertices
```

The grip is untouched because it is defined in the hand's own frame: moving the arm root translates
the hand frame and the fist with it, so every contact figure is identical to the accepted values.

Project suite: **290 passed, 8 failed, 1 skipped**.

## The 8 failures — the measured cost, all outside the curl

This is the blast radius of correcting a rig every character shares. None is in the curl; all are
recorded rather than papered over.

| Test | Failure | What it is |
|---|---|---|
| `exercises > Push-Up` ×3 | 2 technique rules, 22 IK targets, `hand_l` contact 0.0056 > 0.005 | hands plant on the floor; the arm root moved 35 mm, so the authored targets no longer reach |
| `body/ecorche` ×2 | biceps patch 94 < 100; 108 inverted triangles > 80 | the écorché sculpt is built around the old arm position |
| `body/shoulder` | 6.77 > 5.5 | procedural-body shoulder metric, authored against the old chain |
| `muscles` | `deltoid_anterior_l` 0.0022 > 0.001 outside the skin | muscle belly fitted to the old arm |
| `editor/review` | two-hand grip-socket gate false | barbell sockets authored against the old hand positions |

Fixing these means re-authoring the push-up's targets, the procedural body, the muscle bellies and
the two-hand equipment sockets. `MODEL_APPEARANCE_PHASE.md` is explicit that non-curl exercises
"may be used only as regression checks… Do not improve, tune or redesign them", so they are reported
here for your decision rather than retuned.

One test *was* updated, because it is part of this change rather than collateral:
`animation.test.ts > curls through the authored range` hard-coded `6` and `126`. It now reads the
authored values from `bicepCurl.jointTargets`, so it still asserts the clip reaches what the
exercise authored without duplicating the numbers.

## Visual evidence

Rendered in the app on `CORNER_FINAL_SHORTS`, proven loaded (`import` active), `light` backdrop,
canvas-only frames, identical camera and frame in both columns. All 12 before/after pairs differ.

- `shoulder_side_bottom_ab.png` — the headline. The forward deltoid ledge is gone; the cap sits over
  the arm and the arm hangs from underneath it, as in the supplied reference.
- `shoulder_side_peak_ab.png`, `shoulder_tq_bottom_ab.png`, `shoulder_tq_peak_ab.png`
- `hip_clearance_ab.png` — the dumbbell visibly clear of the shorts.
- `side_full_bottom_ab.png` — whole figure.
- `loop_front.png`, `loop_three_quarter.png`, `loop_left.png` — Bottom → Mid → Peak → Return.

Honest note: at Peak in 3/4 the two states are very close, because the correction is a rest
alignment and the Peak pose already carried the arms forward. The difference is clearest at Bottom
and in side view, which is where the defect was reported.

## Rollback

The candidate is **code-only** — `src/rig/humanoid.ts` and
`src/exercises/definitions/bicepCurl.ts`. The character binaries are unchanged, so
`HomeGymPT_Male_CORNER_FINAL.glb` / `_SHORTS.glb` are simultaneously the accepted character and the
candidate's character. Reverting those two source files restores the accepted alignment exactly;
`git revert` of this commit is the whole rollback.

The Stage 1 muscle layer from `BICEP_CURL_REALISM_STAGE1.md` is unaffected and still active.

## Status

True-fix candidate built, measured and rendered. Curl guards re-established and clearance improved.
Stopped for review, with the 8 out-of-scope failures above as the open decision.

**Not promoted. Not merged.**
