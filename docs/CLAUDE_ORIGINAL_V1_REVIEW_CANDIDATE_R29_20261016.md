# ORIGINAL_v1 review candidate R29: arms in a wider V, the arm in line with the back (Claude, 16 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

## Why

Owner, on R28, with the reference photo of a dumbbell press from behind (the photo is kept outside the repo): "Do you see that the outside of the arm is inline with the body itself?" They agreed to both proposed changes ("Yes please"). Later, on an R29 build: "Why is there a fold here?"

## What was measured on R28

Measured in the reference camera view, at 600 px (1.58 mm/px):

- **The arms were too upright.** The outer edge of the arm leans 2.5° from vertical; in the reference it leans about 8°.
- **The body stepped in under the arm.** Under the arm, the outline steps in by 42 px (6–7 cm) before running down the side of the back. In the reference, the back muscle under the arm fills that step: the outer edge of the arm and the side of the back form one line.

## What R29 is

R18 plus the S7 lockout corrective (keys 145/156/166 from 130°). The targets come from `build_original_skin_slide_targets_blender.py`. Recipe: `r29_targets_recipe.json`.

**1. Lockout elevation 166° (skeleton, owner-approved).**
- `original_v1_press_extension.install()` now reads an opt-in `scene["hgpt_press_lockout_ht"]`. Blends without it keep 172°.
- Measured outer-edge lean in the reference view:

  | Lockout | Lean |
  |---|---|
  | 172° | 2.5° |
  | **166°** | **8.4°** |
  | 162° | 12.4° |
  | 158° | 16.5° |

- The S7 bake (`S7_LOCKOUT_HT`) and the targets builder (`LOCKOUT_HT`) set the property, and it is saved with the blend.

**2. Back fill under the arm (`LAT_WEB` 0.6 : 55 cm : 6 cm).**
- Seen from behind, a straight line is fitted to the outer edge of the upper arm (7.6° from vertical) and extended down.
- The side of the torso below the armpit is pushed out across to meet that line, at 60 % strength. The push fades over 55 cm and with distance in from the outline, and is smoothed with 60 passes.
- **Per-key strength (`LAT_KEY_GAIN`):** 0.3 at 145°, 0.6 at 156°.
- A shorter fade (30 cm) left a ledge at the bottom.

**3. Wider post-fit skin slide (`POST_RR` 0.30–0.45 m).** The fill reaches beyond the original slide region, and the skin could only stretch there. Before the change the baked lockout stretch was 282.

**4. Automatic clean-up (`AUTO_UNCROSS`, `UNCROSS_FOLDS` 90,45, `FINAL_SLIDE` 40).**
- Each round rebuilds a small thin-plate patch round:
  - every crossing pair;
  - every crushed triangle;
  - every sharp new fold within 22 cm of a shoulder joint (dihedral > 90° and > 45° above rest).
- It then slides the skin and cleans up once more.
- **Why:** the hand-placed hook and front-fold rebuilds were tuned for 172°, and these folds moved with the new lockout (dihedral up to 169°).

**5. The arm column carried into the arm root (`ELBOW_FAIR` window −38 to +22 cm, fill-only below −16 cm).**
- **Owner's question ("Why is there a fold here?"):** the fold was the corner where R27/R28's straight-column fit stopped, about 6–7 cm up the inner edge of the upper arm. Above it the arm was fitted to the column; below it the root kept its old shape. At 166° the root's inner side sits further in, and the skin there folded (dihedral up to 129°).
- **Fix:** carrying the column down through the root (fill-only there) removes the corner. Close-up: `renders/lockout_r28_r29.jpg`.

**Kept from R28:** the hook and front-fold rebuilds, the 1.5 cm deltoid swell, and the arm column with its root 20 % wider.

## Results

**Targets:** at 145/156/166°, collapse 0 and pairs 0, also over the whole body.

**Bake:** p99 error 0.2 mm. Max 8.8 mm, on a few vertices on the spine line; not visible in the renders.

**Press path** (`r29_build.json`):
- above 130°: collapse 0 and pairs 0;
- stretch at lockout: 318 (R18 at 166°) → **83** (R28 96);
- volume at lockout: **+4.41 %**. This is the back filled out under the arm, and is recorded.

**Sharp folds at lockout:** **58** (R28 94).

**Benchmarks vs R28** (`r29_validation.json`): 12 of 13 are identical. shoulder_press:
- collapse 3 → 1;
- pairs 0;
- volume range [−2.61, 1.01] → [0.48, 2.30] %.

**Visual** (`renders/lockout_r28_r29.jpg`, `press/shoulder_press_r29_views.mp4`):
- the arms are in a wider V;
- the outer edge of the arm runs into the side of the back;
- no fold on the inner arm, no spikes at the neck.

**Tests:**
- `test_original_review_candidate_r29.py` passes 3/3. It adds the lockout property, the recipe and whole-body target checks, and a volume ceiling of +5 %.
- R28, R27 and press-extension tests still pass.

## Still to watch

- **Volume +4.4 % at lockout.** The fuller back is intended; the owner should confirm it reads right.
- **Movement change.** The press now tops out at 166° instead of 172°. Benchmark shoulder_press peak angles are recorded in the validation.
