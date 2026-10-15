# ORIGINAL_v1 review candidate R28: fuller upper arm at the press lockout (Claude, 15 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

## Why

Owner: "Ok please continue", after R27. The two items left open in R27 against the owner's reference photo (dumbbell press from behind; the photo is kept outside the repo):

1. a soft, rounded U at the base of the neck;
2. upper arms thicker near the shoulder.

## Item 1: rounded U at the base of the neck — no change

**Measured on R27.** Between the neck and the arm, the top outline seen from behind has:
- a flat floor about 1.7 cm below the shoulder joint, 8–11 cm out from the midline;
- a steep neck wall about 7.5 cm out;
- a steep arm wall 16–18 cm out.

**Tried (`POSTZONES`).** As a last step, concave skin in a zone at the base of the neck was lifted along its normal only, so the corners would fill.

| Variant | Result |
|---|---|
| One-ring umbrella | 800 passes moved the corner by less than 0.5 mm. It only sees creases a few millimetres across. |
| 2–3 cm neighbourhood | Spiky corners where the arm meets the trapezius: 19, 72 and 78 crossing pairs. |

**Rejected.** In the reference camera view R27 already reads as a rounded U close to the photo, so R28 makes no change here. The `POSTZONES` code stays, off by default, for the record.

## Item 2: fuller upper arm — R28

R28 is R27's recipe with the arm column's root end widened 20 % (`TUBE_ROOT_SCALE=1.2`). The column's straight edge lines now start 20 % further out at the arm root and run to the same forearm slice. The recipe is in `r28_targets_recipe.json`.

**Variants compared** (172° target):

| Root width | Collapse / pairs | Verdict |
|---|---|---|
| +10 % | 0 / 0 | |
| +20 % | 0 / 0 | Closest to the photo |
| +30 % | 1 / 1 | Rejected |

## Results

**Targets:** collapse 0 and pairs 0 at 145/160/172°. The bake matches the target to within **0.2 mm**.

**Press path** (`r28_build.json`):
- above 130°: pairs 0; collapse 0, except 1 at 161° (R18 has 2 there);
- stretch at lockout: 314 → **96** (R27 90);
- volume at lockout: **−2.79 %** (R27 −3.89 %, R26 −2.21 %).

**Sharp folds at lockout:** 94 (R27 70). Mostly the faint line on the far arm in the three-quarter view, which is slightly more visible.

**Benchmarks vs R27** (`r28_validation.json`): all identical, except shoulder_press volume −3.77 → −2.61 %. Collapse is still 3, pairs still 0.

**Visual** (`renders/lockout_r27_r28.jpg`, `press/shoulder_press_r28_views.mp4`): the arms are still straight, smooth columns, now fuller near the shoulder.

**Tests:** `test_original_review_candidate_r28.py` passes 3/3, with the same thresholds as R27. R27's tests still pass.

## Still to watch

- The faint line on the far arm (three-quarter view).
- Sharp folds 94 against R27's 70.
