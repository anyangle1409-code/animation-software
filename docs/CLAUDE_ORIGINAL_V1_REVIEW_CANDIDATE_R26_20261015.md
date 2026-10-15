# ORIGINAL_v1 review candidate R26: hook beside the neck + deltoid cap (Claude, 15 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

## Why

Owner, on R25: "It's still not right". They circled the back of the shoulder at lockout and asked for both fixes ("Do both 1 and 2"):

1. remove the hook / curl next to the neck;
2. restore a rounded deltoid cap (R25 had made the arm root thin and flat).

## What was found

- **The hook.** Located by ray cast and by a sharp-edge scan of the target. It sits about 9.5 cm inboard, 7 cm behind and 3.5 cm below the posed shoulder joint. R25's pocket zone, at (−8, 3.3, −1.3) cm, missed it.
- **Smoothing does not remove it.** Wider smoothing, normal-only lift, and a thin-plate rebuild *before* the slide all still left it. The sharp-edge scan showed the surface-walking slide folds that patch back in.
- **A second fold.** A front armpit fold (dihedral up to 180°) sits at (−1.8, −6, 2.3) cm. It was also present in R25.

## What R26 is

R18 plus the S7 lockout corrective (keys 145/160/172 from 130°). The targets come from `build_original_skin_slide_targets_blender.py` with R25's recipe plus three additions. Recipe: `r26_targets_recipe.json`.

| Addition | Setting | What it does |
|---|---|---|
| `FAIR` | `-0.095,0.07,-0.035:0.055` | Rebuilds the hook zone as a thin-plate (bi-Laplacian) surface from the ring just outside it. |
| `POSTFAIR` | the same zone, plus `-0.017,-0.058,0.035:0.025` | Repeats the rebuild on the slid surface, and rebuilds the front armpit fold. This is what removes the hook. |
| `DELT_BUMP` | `0.03:0.04,0.0,0.06:0.11,0.07` | A 3 cm smooth swell over the outer and back faces of the arm root, along the vertex normal. The swell is an ellipsoid, 11 cm along the arm and 7 cm across it. |

I compared caps of 2, 3 and 4 cm against the owner's reference photos (kept outside the repo). 3 cm read closest without looking swollen.

## Results

**Targets:** collapse 0 and self-intersecting pairs 0 at every key. The bake matches the target to within **0.2 mm**.

**Press path** (`r26_build.json`):
- above 130°: collapse 0 and pairs 0;
- stretch at lockout: 314 (R18) → **112** (R25 91; the cap stretches the skin over it);
- volume at lockout: **−2.21 %** (R25 −2.81 %).

**Sharp folds at lockout** (right shoulder, 20 cm region): R18 164 → R25 92 → **R26 64**.

**Benchmarks** (`r26_validation.json`): the same as R25 for 12 of 13. shoulder_press volume improves (−2.72 → −2.14 %).

**Visual** (`renders/lockout_r25_r26.jpg`, `press/shoulder_press_r26_views.mp4`):
- the hook beside the neck is gone (close-up and three-quarter views);
- the arm root has a rounded deltoid cap (back and side views).

**Tests:** `test_original_review_candidate_r26.py` 3/3. R25's tests still pass.

## Still to watch

- A faint line on the upper arm, near the armpit, in the close-up.
- A small dimple where the neck pocket bottoms out.
- The front chest fold lines (unchanged).
