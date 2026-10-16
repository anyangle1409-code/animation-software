# ORIGINAL_v1 review candidate R33: straight upper arm while raising, rounder elbow, smoother arm root (Claude, 16 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

## Why

Owner, on R31 press frames (reference stills are kept outside the repo):
- "This is the closest to what I want apart from the highlighted sections. It's just the skin crumbling at this point really." (circled: behind the armpit, where the upper arm meets the back);
- at arm elevation 132° and 145°: "The arms as it's raising up should be in a straight line. There shouldn't be the dent when it's raising up. Also the bend at the elbow is too sharp and not subtle at all."

## What was measured on R31

1. **Crumple behind the armpit.**
   - Sharp edges near the right arm root (dihedral > 30° and 15° above rest, within 18 cm of the joint): 32 / 52 / 56 / **80** / 43 / 54 at 120 / 130 / 139 / **145** / 151 / 156°.
   - The 145° key's own target held 27 edges above 45°, up to 86°. R31's clean-up only rebuilt folds above 90°, so it left them.
2. **Kink above the elbow at 132–145°.**
   - It is absent with S7 off (render: `renders/rejected_elbow_weights_noS7.jpg`, top row).
   - **Cause:** the S7 arm column ran from the *wrist* to the arm root. At the 145° key the elbow is still bent 30°, so a straight wrist-to-root column cuts across the elbow and kinks the upper arm. R31 applied it at half strength there, and that left the kink.
   - Elbow bend at each key: 67 / 30 / 15 / 0° at 120 / 145 / 156 / 166°.
3. **Sharp elbow.**
   - Along the arm skin, the upper-arm weight share falls 0.83 → 0.60 → 0.39 → 0.16 → 0.05 at −4 / −2 / 0 / +2 / +4 cm from the elbow joint. The whole hand-over happens within about 3 cm either side of the joint.

## What R33 is

Same base as R31: B5, which has the upper arm re-bound to the humerus and S5 rebuilt; weights are identical (checked by the test). S7 is rebuilt with `build_original_skin_slide_targets_blender.py`, keys 120/145/156/166, fade-in from 95°, lockout 166°. Recipe: `r33_targets_recipe.json`; commands in `stages/`.

**1. Upper arm straightened along its own bone at bent-elbow keys (`TUBE_UPPER -38,-26,-7,-3`, `TUBE_UPPER_A -9,-5`).**
- Applies when the key's elbow bend is above 8°.
- The column's axis is shoulder → elbow. Its far anchor is the slice 5–9 cm above the elbow, and the window ends 3 cm above the elbow.
- Only upper-arm skin is moved (rest position more than 1 cm above the elbow).
- Now applied at full strength at 120° and 145° (R31: 0 and 0.5).

**2. Elbow rounding (`ELBOW_ROUND 10:20:30`).**
- Volume-keeping (Taubin) smoothing of the skin within 10 cm of the posed elbow joint, 20 passes.
- Strength scales with the elbow bend, full at 30°.

**3. More back fill under the arm while raising (`LAT_KEY_GAIN 120:0.5,145:0.6,156:0.6`; R31 0 / 0.3 / 0.6).** Base strength stays at 0.35, so the back at lockout is as light as R31's.

**4. Fold clean-up threshold lowered at the bent keys (`UNCROSS_FOLDS 40,20`; R31 90,45), set per key:**
- **156°: `55,25`, with the patch radius capped at 6 cm (`UNCROSS_RMAX`).** At 40,20 the clean-up rounds never settled: the patches grew to 12 cm and left a knot on the trapezius by the neck, visible at 151–160°.
- **166°: `90,45`, as in R31.** At 40,20 the clean-up rebuilt the natural armpit fold at lockout and crushed 122 triangles.
- **How the keys were built:** 120/145 come from one run; 156 and 166 come from single-key runs with these settings. The four were merged; the recipe's `note` says so.

**Tried and rejected: spreading the elbow weight hand-over** (`scripts/build_original_elbow_blend_weights_blender.py`, ±7 cm). It flattened the outside of the bent elbow into a notch, a chord across the corner (render: `renders/rejected_elbow_weights_noS7.jpg`, bottom row). The script stays for the record; R33 does not use it.

## Results

**Sharp edges near the arm root:**

| Elevation | 120° | 130° | 139° | 145° | 151° | 156° |
|---|---|---|---|---|---|---|
| R31 | 32 | 52 | 56 | 80 | 43 | 54 |
| **R33** | **22** | **47** | **27** | **34** | **17** | **45** |

**Targets:** crossing pairs 0 and crushed triangles 0 over the whole body at every key. R31 had 4 crushed at 156°.

**Press path** (`r33_build.json`):
- above 95°: crossing pairs 0 and collapse 0;
- **at 156°:** stretch 169 → **50**;
- **at lockout:** stretch 47 → 80 and volume +1.60 %, both higher than R31 (recorded);
- **mid-press (97–145°):** stretch 87–122, against 1–46 in R31. The arm and back now actually move toward their shape at 120°, where R31 left them alone. Still below the press without S7 (100–164).

**Bake fit:**
- 166°: p99 0.1 mm.
- 120° and 145°: p99 2.7 / 3.0 mm, max 21–23 mm. The misses are a small patch inside the front of the armpit, 2–3 cm in front of and below the shoulder joint. The bake's guard against skin passing through the body holds that skin back.
- The same spot carries the sharpest edge at 130° (132°). It is not visible in the back views the owner reviews.

**Benchmarks vs R31** (`r33_validation.json`): 12 of 13 identical. shoulder_press: collapse 0 → 2 (recorded), stretch 130 unchanged, pairs 0.

**Visual:**
- `renders/press_r31_r33.jpg`: back and three-quarter at 118 / 132 / 145 / 156°. The upper arm is straight while it rises, the elbow is rounder, and there is no kink or dent.
- `renders/armroot_151_160_r31_r33.jpg`: the arm root from behind, smoother than R31.
- `renders/target145_posed_r31_r33.jpg`: the 145° target.
- `press/shoulder_press_r33_views.mp4`.

**Tests:** `test_original_review_candidate_r33.py` passes 3/3:
- the same base as R31 (lineage and identical weights);
- the recipe and the clean targets;
- the press path, including collapse 0 above 95° and 156° stretch < 100;
- benchmarks vs R31, with the shoulder_press +2 collapse recorded.

## Still to watch

- **The front armpit at 120–145°:** the bake misses there (up to 23 mm), and there is a sharp edge at 130°.
- **Stretch:** higher at mid-press and at lockout than R31.
- **The owner's eye:** whether the arm root now reads smooth while raising, and whether the elbow is soft enough.
