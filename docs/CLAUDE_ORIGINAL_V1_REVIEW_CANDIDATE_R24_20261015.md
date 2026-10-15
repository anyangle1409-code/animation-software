# ORIGINAL_v1 review candidate R24: press-lockout skin slide (Claude, 15 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

## Why

- Owner, circling the arm root and the ball behind the shoulder at the top of the press: "You need to address the circled area shown. Why is it deforming here? This should not be creating this."
- After the routes in `CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R18_20261015.md` failed, the owner chose option "2": keep researching an automatic skin slide.

## What R24 is

R18, unchanged, plus a pose-space corrective family `HGPT_S7_DELT_<s>_145/160/172`. It is driven by arm elevation from 130° (`original_v1_review_candidate_drives.S1_FAMILIES`). Off below 130°, so every lower pose and every other movement is untouched.

**Targets** (`scripts/build_original_skin_slide_targets_blender.py`; recipe in `r24_targets_recipe.json`), built for each key pose from R18's posed surface (all keys on):

1. **Light Taubin smoothing** of the shoulder region (10 passes): removes small creases.
2. **Fairing the ball:** umbrella smoothing, 200 passes, in a zone centred 4 cm behind and 2 cm below each shoulder joint. Free within 6 cm, fading out by 10 cm. This flattens the ball behind the joint. Taubin alone does not, even at 40 or 80 passes, because the ball is a broad shape.
3. **Skin slide** (`scripts/original_v1_skin_slide.py`):
   - Every vertex lives on that shape as (triangle, barycentric) and moves by walking across triangle edges, so it can never jump through a crease.
   - The energy is Σ (area / rest area − 1)², so skin moves from the squashed deltoid into the stretched armpit and side of the chest.
   - A step is undone if an incident triangle would turn over or drop below 15 % of its rest area.

**Bake.** The targets are baked into rest-space keys with the S5 machinery: target-interpenetration mask, LBS-inverse, smooth guard along the press, and the shoulder-press benchmark path (`build_original_review_candidate_r17_blender.py --bake`, `S7_NAME=R24`).

## Results

**Targets** (vs R18 posed surface; 0 self-intersecting pairs at every key):

| Key | Stretched > 2 | Stretched > 1.5 | Collapse |
|---|---|---|---|
| 145° | 140 → 8 | | 0 → 0 |
| 160° | 210 → 28 | | 2 → 4 |
| 172° | 255 → 45 | 1,137 → 621 | 0 → 6 |

**Press path** (`r24_build.json`, R18 → R24):

| Measure | Result |
|---|---|
| Collapse above 130° | 0 everywhere (R18: up to 2) |
| Self-intersecting pairs | 0 everywhere |
| Stretch at lockout | 314 → **100** |
| Stretch at 150° | 167 → 24 |
| Body volume at lockout | −1.11 % → −2.16 % (the faired ball; recorded) |

**Benchmarks vs R18** (`r24_validation.json`): all equal, except shoulder_press, which improves (collapse 20 → 7, stretch 150 → 118).

**Visual** (`renders/lockout_r18_vs_r24.jpg`, `press/shoulder_press_r24_views.mp4`):
- the ball behind the shoulder is gone (side view);
- the arm-root kink the owner circled is mostly gone (three-quarter view);
- from behind, the shoulders flow into the arms (the Y);
- arms down is unchanged;
- the switch-in over 129–161° is smooth, with no popping (`renders/r24_transition_129_to_161deg.jpg`).

**Tests:** `test_original_review_candidate_r24.py` 3/3.

## Still to watch

- A faint ring line around one upper arm at 156–161°.
- A small notch right at the armpit in the three-quarter view.
- The chest/armpit fold lines in the front view (unchanged from R18).
- The −2.2 % volume at lockout.
