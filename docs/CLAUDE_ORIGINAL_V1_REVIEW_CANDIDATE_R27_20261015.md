# ORIGINAL_v1 review candidate R27: straight arm column at the press lockout (Claude, 15 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

## Why

Owner feedback on R26:
- "Can you check the shape of the arm in the upright position?"
- "The bicep should flow into the forearms without a big dip between."
- "I don't understand why it's all bumpy." (They drew the outline: one smooth column from the forearm into the back.)

The owner then supplied a reference photo of a dumbbell press from behind. It is kept outside the repo. "This is the shape the model should be in."

## What was measured (R26, right arm, lockout)

**Radius from the arm's centre line, cm from the elbow** (negative means towards the shoulder):

| Position | Radius |
|---|---|
| deltoid | 5.7 cm |
| −21 to −18 cm | **4.4 cm** (a pinch; at rest this skin is 5.8 cm) |
| −12 cm (lower biceps) | 5.2 cm |
| elbow | 4.5 cm |

The biceps (vertices bound about 0.91 to upperarm_r) juts about 4 cm towards the head, then cuts in to the elbow. From the front the widths are 12.7 cm (biceps), 8.7 cm (elbow) and 9.7 cm (forearm).

**This shape is in the raw skinning too.** The body was sculpted with the arms down. Raising the arm pinches the skin below the deltoid, and the biceps is left as a bulb.

In the reference photo, each arm is a straight column that widens steadily from the wrist into the shoulder.

**Tried and rejected (measured, with renders):**

| Attempt | Why rejected |
|---|---|
| Even radial fill | Ripples. |
| Removing the S5 bake mid-arm | Reopened the crumples S5 smooths. |
| Gaussian / hull fairing of the radius profile | Too weak. |
| Polynomial / Fourier fit of the whole arm | Kept the bulb. |
| Restoring the smoothed rest shape | Crinkled the elbow. |
| A single-centre tube | Leaned outwards. |

## What R27 is

R18 plus the S7 lockout corrective (keys 145/160/172 from 130°). The targets come from `build_original_skin_slide_targets_blender.py`. Recipe: `r27_targets_recipe.json`.

**Kept from R26:** the hook rebuild beside the neck (FAIR / POSTFAIR) and the front armpit fold.

**Deltoid swell:** 1.5 cm (R26: 3 cm). The full swell left a knot at the arm root.

**New: the arm column** (`ELBOW_MODE=tube`):
- **Four straight lines.** The outer, inner, back and front edges of the arm run in straight lines from a forearm slice (14–20 cm past the elbow) to the arm root (−23 to −19 cm). They are measured from the shoulder–wrist line.
- **Fitting the skin.** Every arm vertex in the window (−27 to +22 cm) is moved onto that column along its direction from the line. This is repeated 3 times, then the arm zone is Taubin-smoothed with 80 passes (the squeeze crumpled the biceps skin otherwise).
- **Fill-only near the root.** Fill-only below −18 cm, blending out by −12 cm. Squeezing the deltoid edge made a knot.
- **A second skin slide** of 30 steps after the fit. The fit had left 3 crushed triangles and 2 crossing pairs.
- **Half strength at 145°.** Full strength there crossed the skin: 196 pairs. Caught by the R27 test and kept as a genuine failure until fixed.

## Results

**Targets:** collapse 0 and pairs 0 at every key. The bake matches the target to within **0.2 mm**.

**Press path** (`r27_build.json`):
- above 130°: pairs 0; collapse 0 except 1 at 161° (R18 has 2 there);
- stretch at lockout: 314 → **90** (R26 112);
- volume at lockout: **−3.89 %** (R26 −2.21 %). This is the biceps jut removed on purpose, and is recorded.

**Sharp folds at lockout:** 70 (R26 64).

**Benchmarks vs R26** (`r27_validation.json`): 12 of 13 are identical. shoulder_press improves on collapse (7 → 3), with volume −2.14 → −3.77 %.

**Visual** (`renders/lockout_r26_r27.jpg`, `press/shoulder_press_r27_views.mp4`): the arms are straight, smooth columns into the shoulder, with no biceps bulb and no elbow dip.

**Tests:**
- `test_original_review_candidate_r27.py` passes 3/3.
- **Test change, documented:** the lockout volume floor is −4.5 % (R26's test used −3.0 %) because the volume loss is intentional.
- R26's tests still pass.

## Still to watch

- **The neck corner.** At the base of the neck the reference shows a soft, rounded U where the trapezius meets the arm. R27 is still a narrower V.
- **Arm thickness.** The upper arms near the shoulder are thinner than the reference's.
- A faint line on the far arm in the three-quarter view.
