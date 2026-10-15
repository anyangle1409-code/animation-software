# ORIGINAL_v1 review candidate R25: press-lockout arm-root crease (Claude, 15 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

## Why

Owner, on R24: "No it's still creasing in that same point". This is the arm root in the three-quarter view.

## What was still there in R24

Located by concavity and marked on R24 at lockout (`renders/r24_corner_and_pocket_located.jpg`), there were two features:

1. **A corner on the back of the upper arm,** about 8 cm up the arm from the shoulder joint. The arm's outline kinks there, where full-follow arm skin meets the half-follow deltoid skin. R24 faired a zone behind and below the joint and did not reach it.
2. **A pinched pocket** between the arm and the neck.

## What R25 is

R18 plus the S7 lockout corrective (keys 145/160/172 from 130°), with targets from `build_original_skin_slide_targets_blender.py`. Recipe: `r25_targets_recipe.json`.

R24's recipe (light Taubin smoothing, fairing the ball, surface-walking slide) is kept, with these additions:

| Addition | What it does |
|---|---|
| Corner zone | Umbrella smoothing, 250 passes, centred (3, 2.5, 8) cm from the joint. Smoothstep fade from 3 to 11 cm. (A linear fade left a crease ring.) |
| Pocket zone | The concave floor is lifted along its normal only, 300 passes, centred (−8, 3.3, −1.3) cm. Plain smoothing pulled the pocket walls together into a hole. |
| Blend | A light Taubin blend over the region (20 passes), so the zone edges leave no seam. |
| Crush penalty in the slide | Triangles below 30 % of rest area get a strong extra push open (`crush_w` 100). The slide's guard now lets a step through when it enlarges an already-crushed triangle. |
| Slide length | 100 steps. |

**Why the crush penalty was needed.** The first two R25 bakes left 46, then 12, crushed triangles in the target. The bake's guard cut the correction back around them, which left spikes and fins at the arm root: the baked surface was up to 15 mm off the target in a small patch at the back-top of the deltoid.

With the crush penalty, the targets have **0 crushed triangles and 0 self-intersecting pairs at every key**. The baked surface matches the target to within **3.1 mm** (p99 0.1 mm).

## Results

**Press path** (`r25_build.json`):
- above 130°: collapse 0 and pairs 0;
- stretch at lockout: 314 (R18) → **91**;
- body volume at lockout: −2.81 % (R18 −1.11 %; recorded): the faired ball, corner and pocket.

**Sharp folds at lockout** (right shoulder, 20 cm region): R18 164 → R24 140 → **R25 92**.

**Benchmarks vs R18** (`r25_validation.json`): all equal, except shoulder_press, which improves (collapse 20 → 7, stretch 150 → 118).

**Visual** (`renders/lockout_r18_r24_r25.jpg`, `press/shoulder_press_r25_views.mp4`):
- the arm runs straight into the shoulder, with no corner (close-up and three-quarter views);
- no ball behind the shoulder (side view);
- the shoulders flow into the arms (back view);
- the switch-in over 129–166° is smooth (`renders/r25_transition_129_to_166deg.jpg`).

**Tests:** `test_original_review_candidate_r25.py` 3/3.

## Still to watch

- A small curl where the pocket ends, next to the neck.
- Faint surface texture on top of the shoulder.
- The front chest/armpit fold lines (unchanged).
- The −2.8 % volume at lockout.
