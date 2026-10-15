# ORIGINAL_v1 review candidate R18: shoulder/armpit mesh rebuild, stage 1 (Claude, 15 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

## Why

- Owner, circling the arm root at the top of the press: "This highlighted areas shouldn't be crinkled."
- Then "Yes please" to rebuilding the shoulder/armpit mesh.

## Where the skin goes wrong at lockout (R15)

Map: `renders/r15_lockout_stretch_squash_fold_map.jpg`. Region: right shoulder, 20 cm around the joint.

| Condition | Vertices / edges | Where |
|---|---|---|
| Stretched more than 1.5× | 457 vertices | side of the chest and back below the armpit, front chest wall below the armpit |
| Squashed below 0.6× | 658 vertices | deltoid, arm root, top of the shoulder |
| Sharp folds (posed dihedral > 30°, and > 15° more than at rest) | 285 edges | on the boundary between the two: the crinkles |

**Why the fold looks crinkled.** On this all-triangle mesh the fold crosses triangle diagonals, so it shows as a zig-zag.

## R18: edges re-routed along the folds

`scripts/build_original_shoulder_fold_flip_blender.py`

**What it is.** R15 with 1,482 edge flips per side, mirrored exactly on the left.
- Same 21,600 vertices.
- Every vertex position, weight and shape key is identical to R15 (the test checks this).
- Only the triangulation changes.

**How the flips are chosen.** An edge is flipped when that lowers the weighted posed bending (sum of squared dihedral angles) over:
- the rest pose;
- the press at 121, 145, 160 and 172°;
- the bent-over-row end;
- the push-up bottom.

**Guards:**
- rest minimum angle ≥ 12°;
- rest dihedral of the new diagonal ≤ 20°;
- no posed triangle flips orientation.

**Sharp folds, R15 → R18** (`r18_build.json`):

| Pose | Sharp folds | Bending |
|---|---|---|
| Lockout 172° | 285 → **162** | −40 % |
| 160° | 244 → 131 | |
| 145° | 157 → 92 | |
| 121° | 100 → 52 | |
| Row end | 40 → 32 | |
| Push-up | 9 → 8 | |
| Rest | 0 → 0 | smoother: rest edges > 20° 108 → 92 |

**Benchmarks vs R15** (`r18_validation.json`): nothing worse.
- shoulder_press collapse 16 → 20, within the test's +4.
- push_up collapse 3 → 1.

**Visual** (`renders/lockout_shoulder_closeup_r15_vs_r18.jpg`):
- The crease where the arm meets the back is softer.
- The front armpit fold is smoother.
- The lump behind the shoulder is unchanged. This stage changes how folds look, not where the skin is.

**Tests:** `test_original_review_candidate_r18.py` 3/3.

## Tried in this stage and not adopted

**"Spare skin": the armpit vault deepened in the rest shape.**
- Change: 644 vertices moved toward the joint, every shape key moved with them.
- Lockout stretch got worse: 300 → 350 (15 mm) and 370 (30 mm).
- Reason: with linear blend skinning the extra area is pulled open with the arm and stretches the side of the chest more.

**R19: R18 with the press S5 shapes re-baked on the new triangulation.**
- Lockout sharp folds 315 vs R18's 162; stretch 404.
- The re-bake brings back the folds the flips removed.

**Deltoid lift on R18: shoulder-cap fraction ramp.** Measured at lockout:

| End fraction | Collapse | Pairs |
|---|---|---|
| 0.5 | 4 | 0 |
| 0.6 | 64 | 0 |
| 0.7 | 98 | 128 |
| 0.8 | 87 | 190 |

- This is the same crushing as on R15: re-routing edges does not change where the skin must hinge.

**Deflating the squashed skin at lockout** (`build_original_review_candidate_r17_blender.py`, `S7_DEFLATE_M`): an inward move along the normal, scaled by the squash and smoothed.

| Setting | Peak move after smoothing | Effect |
|---|---|---|
| 12 / 20 mm | 9 / 15 mm | small effect |
| 40 / 60 mm | 29 / 44 mm | the whole upper arm thins and the deltoid pinches (`renders/rejected_deflate_targets.jpg`) |

## What is left

- **The lump behind the shoulder at lockout.** It is excess skin over a shortened deltoid, sitting at about arm-out-sideways.
  - Every automatic route on this rest mesh has now been measured, and each moves the problem rather than removing it: helper fraction, weight hand-backs, lift corrective, deflate corrective, re-triangulation and rest-vault spare skin.
- **What remains, for the owner:**
  1. **A hand-sculpted lockout corrective** (artist, in Blender), the standard production fix.
  2. **Re-binding the body mesh in a raised-arm (A-pose) rest shape**, so the shoulder's skin is distributed for the overhead range.
  - Both are owner decisions. The second is a runtime-contract change.

## After R18: option 2 and the arm-root kink (all measured, none adopted yet)

**Owner's input.**
- "I don't have an artist so maybe option 2. I want it fixed."
- Then, circling the inner arm root in the three-quarter view: "Why is it deforming here? This should not be creating this."

**Why the arm root kinks** (`renders/follow_map_r18_vs_handover.jpg`):
- The follow map shows how much of the arm-vs-scapula turn each vertex makes.
- On the upper arm the skin follows 100 %. Over the deltoid it follows about 50 % (the shoulder_cap helper and the girdle).
- The change happens within a few centimetres at the arm root, so the arm's outline bends there.
- The lagging skin is also the ball behind the joint.

**Option 2: raised-arm (A-pose) bind** (`renders/rejected_raised_arm_bind.jpg`). **No-go.**
- How it was done: a hidden bind rig copies the main rig every frame; the body is re-rested on the A-pose skinned surface, and the keys are converted with the A-pose linear part.
- **At 45°:** raw lockout matches R18 (stretch 1,271 vs 1,230; the ball is unchanged). Arms-down drift is up to 12 mm.
- **At 90°:** the same at lockout. Arms-down drift is up to 38 mm, with a visible dent.
- Why: an LBS-generated A surface carries no new information. A real A-pose bind needs a separately modelled A-pose body.

**R20: deltoid hand-over** (`original_v1_deltoid_handover.assign`, outer/back faces, -2..16 cm, 40 % of the girdle share).
- Raw: the ball is smaller.
- With R18's S5 shapes: 44 collapse / 128 pairs at lockout.
- **R21** (S5 re-baked on R20): 4 collapse / 0 pairs, but the S5 shapes crumple the back of the armpit.

**R22: continuous follow profile** (`assign_profile`, from the old value at 4 cm above the joint up to 100 % at 16 cm down; `renders/circled_area_r18_vs_r22.jpg`).
- The arm-root kink is softer.
- Raw collapse at lockout is 32 (R18: 3).
- **R23** (S5 re-baked): 30 collapse (tiny, inside the crease on top of the shoulder), 0 pairs, stretch 624. In the three-quarter view the arm root still crumples (`renders/r18_vs_r23_lockout.jpg`).

**Rejected outright:**

| Attempt | Result |
|---|---|
| A target jump to a fixed follow value | tears where raised and unchanged vertices meet |
| Starting the profile at the joint or 2 cm below it | 28–46 collapse |
| Dual-quaternion skinning, with or without a cap ramp | body volume +9–10 %; armpit wings and front folds (`renders/rejected_dual_quaternion.jpg`) |
| Relaxing the lockout skin toward its rest edge lengths | the squashed deltoid skin buckles; 1,205–1,807 pairs (`renders/rejected_relaxed_skin.jpg`) |

**What this establishes.**
- Over the deltoid at lockout there is more skin than the shape holds. Squeezing it crushes it, relaxing it buckles it, deflating it thins the arm, and lifting it folds it elsewhere.
- Meanwhile the armpit and the side of the chest are short of skin (`renders/r15_lockout_stretch_squash_fold_map.jpg`).
- Real skin slides from the one to the other.
- The remaining procedural route is a lockout corrective that slides the skin along a smoothed shoulder shape from the squashed deltoid into the stretched armpit.
