# ORIGINAL_v1 review candidate R14: press path v2, shoulder-top gradient, muscle-line helpers (Claude, 15 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

## What the owner asked

1. "I want you to fix the shoulder press first because it seems to be the sticking point. When it gets to the highest point that is the worst deformation."
2. The owner then sent a 7-view photo series of a standing dumbbell press (start, mid, near top, lockout) and an armpit close-up.
3. Later messages:
   - "I want the shoulder and arms and armpit problem fixed."
   - "Is this an issue with the mesh or weights? The muscles …"
   - "Ok please proceed with it."
   - Should muscle evidence come first?
   - "Continue to fix."

The owner's photos are kept out of the repo. The comparison sheets live in the session scratchpad only.

## What the comparison with the photos showed (R13)

1. **Arm path.** R13's arms rose 40° forward of the frontal plane, with the forearms leaning 25° in and 21° forward, so the hands were in front of the face. The photos show elbows out, at about 15° forward, and the dumbbells beside the ears.
2. **Shoulder-cap balls at the start**, seen from the back.
3. **At the top of the press:**
   - a flat shelf across the top of the shoulder, from the neck to the raised arm;
   - a taut ridge from the armpit to the collarbone;
   - a lump in the armpit.
4. **Build and posture.** The model is much slimmer and less muscular than the man in the photos, with a rounded upper back and a forward belly. This is a body-shape question for the owner, not deformation.

## What R14 changes

R14 starts from R13 and changes the following. The baked shoulder shapes are re-made on top of all of it.

**1. Press path v2** (`scripts/original_v1_press_extension.py`)
- **Opt-in:** a blend uses it only if `scene["hgpt_press_path"] = "v2"`. R10–R13 stay on v1, and their tests are unchanged.
- **Elevation plane:** 15°.
- **Start:** 70° elevation with the elbow at 140°.
- **Forearm aim:** the humerus turns about its own axis so that each bent forearm points at a dumbbell 8 cm lateral of the shoulder joint. This turn fades out over the last 30° of elbow extension.
- **Result:** at the start the hands are at head height about 10 cm outside the shoulders, with the elbows out wide.

**2. Neck-to-shoulder weight gradient** (`scripts/original_v1_shoulder_trap_weights.py`)
- **Cause of the shelf:** across the top of the shoulder, the skin switched within about 3 cm from following the head/neck (which barely moves in a press) to following the clavicle/scapula (+26° clavicle elevation, about 51° scapular rotation, plus the shrug).
- **Fix:** the girdle share now rises smoothly from 3 to 20 cm off the midline. The top of the shoulder now slopes up into the arm, as the trapezius does in the photos.

**3. Muscle-line helper joints** (`scripts/original_v1_muscle_line_helpers.py`)
- **Attachments:** from standard descriptive anatomy, placed on this skeleton's own landmarks (sternum IJ/PX, clavicle SC/AC, scapula AI/AA/TS/GH, humerus EJC).
- **Why no third-party model data:** the MoBL-ARMS OpenSim model is licensed non-commercial only, and SimTK cannot be reached from this environment.
- **Muscle lengths along press path v2**, measured on this rig with `scripts/measure_original_muscle_lines_blender.py` (% of rest length):

  | Muscle | 70° | 130° | 172° |
  |---|---|---|---|
  | Latissimus dorsi | 113 | 138 | 156 |
  | Teres major | 121 | 134 | 139 |
  | Pectoralis major, sternal head | 128 | 137 | 132 |
  | Pectoralis major, clavicular head | 116 | 110 | 96 |
  | Deltoid, middle | 80 | 64 | 54 |
  | Deltoid, anterior | 100 | 93 | 79 |
  | Upper trapezius | 94 | 87 | 80 |

  - Stretched muscles form the front and back axillary folds.
  - Shortened muscles bunch up: the deltoid and the trapezius.
  - These are straight-line lengths with wrapping ignored, so the shortening of the deltoid is overstated. The direction of change agrees with standard functional anatomy.
- **The helpers:**

  | Helper | From → to | Carried by | Behaviour |
  |---|---|---|---|
  | `muscle_pec_<s>` | mid-sternum → lateral lip of the intertubercular groove | thorax | |
  | `muscle_lat_<s>` | scapular inferior angle → floor of the groove | scapula | takes trunk weight only |
  | `muscle_trap_<s>` | nuchal / C7 region → lateral third of the clavicle | neck | may thicken up to 1.25× as it shortens |

- **Mechanism:** each helper is aimed from its origin to its insertion every frame and stretched along its length, thinning to preserve volume. Skin over the muscle belly therefore interpolates between trunk and arm along the muscle line.
- **Constraints:** the helpers live in memory only, so the saved blend stays at 67 bones. The lat helper takes trunk weight only. When it also took the shoulder/arm share, the bent-over row's end pose pulled the back of the armpit into the arm (4 → 36 pairs); trunk-only gives 0.

**4. Re-made shoulder shapes**
- R13's S4/S5 shapes were made along press path v1 and are dropped.
- New S5 shapes are baked with the R12 recipe:
  - S4 at ×5, with the axilla at 0.3 over 12 cm and the trapezius at 0.3;
  - a delta-mush target;
  - the LBS-inverse bake.
- **Guard:** the smooth guard runs along both the v2 press and the shoulder-press benchmark's own coupled path.

## Tried and rejected on the way

| Attempt | Result |
|---|---|
| Laplacian-coordinate curvature restore (whole region) | drifts up to 105 mm; 386 pairs |
| Same, light (15 passes) / ridge-only | lump and back crease improved; ridge stays; 40–270 pairs |
| Chain-weighted armpit helper (thorax → helper → arm by distance to the arm axis) | spiky flaps |
| Chest weight gradient (sternum → arm) | notches and folds on the chest |
| Armpit-wall weight hand-back to the trunk | hard crease in the axilla |
| Muscle helpers with a hard front/back split | vertical crack down the side of the chest |
| Lat helper gated by elevation | row 130 pairs |
| Tangential "skin slide" (projected) | triangles fold (about 4,500 pairs); with a flip guard, collapse goes up to 812 |
| Local weight smoothing of the posterior axilla | notches; the flap in front gets worse |

## Results

**Press path v2, with and without the new S5 shapes** (`r14_build.json`; collapse / stretch > 2 / self-intersecting pairs / volume %):

| Elevation | Without S5 | R14 |
|---|---|---|
| 70° (start) | 0 / 81 / 278 / +0.08 | 0 / 56 / 226 / +0.15 |
| 86° | 4 / 165 / 302 / −0.06 | 0 / 92 / 0 / +0.31 |
| 99° | 22 / 182 / 14 / −0.29 | 0 / 80 / 0 / +0.26 |
| 121° | 0 / 216 / 0 / +0.27 | 0 / 112 / 0 / +0.83 |
| 150° | 0 / 400 / 0 / −0.11 | 0 / 142 / 0 / −0.31 |
| 172° (lockout) | 10 / 610 / 2 / −0.46 | 10 / 250 / 2 / −1.30 |

- Above 120°, stretch is cut by about 60%.
- The S5 shapes add no overlap at any step.
- **The start pose (70°, elbow at 140°) still has 196–226 pairs.** They disappear by 86°. The cause is not yet isolated; the likely candidate is forearm–upper-arm contact at deep elbow flexion. This is kept as a genuine, open failure.

**Benchmarks vs R13** (`r14_validation.json`, worst frame; self-intersecting pairs / collapse):

| Benchmark | R13 | R14 |
|---|---|---|
| bent_over_row | 4 / 2 | **0 / 0** |
| shoulder_press | 0 / 4 | 0 / **18** |
| grip | 20 / 0 | 18 / 0 |
| push_up | 2 / 3 | **0** / 3 |
| deadlift | 293 / 4 | 293 / 4 (unchanged, DL1 owner decision) |
| all others | equal | equal |

- **shoulder_press collapse rises by 14:** the benchmark's own coupled path (40° plane) now carries shapes tuned for the 15° v2 plane. The test allows +16 and records this openly; it is not hidden.
- **First bake left 190 pairs on the benchmark.** The S5 smooth guard had followed v2 only. It now also follows the benchmark path, with the press-extension hook switched off for those poses so that the guard sees the same path the validation runs. Result: 0 pairs.

**Tests (all OK):**
- R14: 4;
- movement benchmarks: 15;
- press extension: 5;
- R12: 6;
- R13: 6.

**Videos:** `ORIGINAL_V1_WORK/anatomy/candidates/claude_review_r14_20261015/press/`, `shoulder_press_r14_views.mp4` and `shoulder_press_r14_closeup.mp4`.

## What is still not right

- At lockout, a crease where the arm meets the back (back view).
- A rounded mass behind the arm root (side view).
- Thin fold lines at the front of the armpit.

None of the blended-skinning fixes above removes these. What is left is mesh structure:
- the shoulder and axilla are a uniform triangle field with no edge loops along the deltoid / axillary folds;
- the arms-down rest pose leaves no spare skin in the armpit;
- there is a density seam where the shoulder re-mesh meets the original mesh.

The body's muscle volume is also much smaller than the reference's.

**Owner decision:** rebuild the shoulder/axilla mesh. That means a topology change, re-transferring weights, and rebuilding every shape-key family. It is a contract item.

## Skeleton diagnosis at lockout: the clavicle swings forward (found after R14)

**Owner (on the R14 back view at lockout):** "The shoulder should move with the arm. If you show me the skeleton in this pose I want to work out what is causing this. I think maybe the shoulder is coming over too far."

**Skeleton renders** are in `diagnosis/` (skin, skeleton and X-ray views, rest → lockout). The landmark numbers are in `diagnosis/girdle_landmarks_v2_vs_v3.json`.

**From rest to lockout on R14 (path v2):**

| Part | Movement |
|---|---|
| Glenohumeral joint | 5 cm forward, 11 cm up |
| Acromion angle | 4 cm forward |
| Root of the scapular spine | 10 cm lateral, 6 cm forward |
| Clavicle | 26° up, but **5° forward**, although the motion profile asks for 10° back |

**Cause.** `coupled.clavicle_basis` (Work's module, unchanged here) builds the clavicle rotation as `Rz(retraction) @ Ry(axial) @ Rx(elevation)`.
- Each channel is correct on its own. A +20° test of each gives +20° of that motion and nothing else.
- The problem is the order. The axial "posterior rotation" is applied after the elevation, and about the rest shaft line instead of the clavicle's current shaft.
- So once the clavicle is raised, the axial turn swings it around a cone.
- At lockout (elevation about 30° including the shrug, axial turn 31.6°), the cone swing is 15.6° forward. That matches the measured gap: 22.6° of retraction expected, 7.0° measured.
- The acromion, scapula and glenoid are carried forward over the arm by this swing.

**Fix: press path v3 (opt-in).** v3 is v2 with the axial turn applied first, about the shaft. The channels, signs and axes are the same (`original_v1_press_extension.clavicle_basis_axial_first`).

| At lockout | v2 | v3 |
|---|---|---|
| Clavicle retraction | 7.0° | 22.1° |
| Clavicle elevation | 30.4° | 34.0° |
| Glenohumeral joint vs rest | 5.1 cm forward | 0.8 cm forward |
| Acromioclavicular joint vs rest | 1.9 cm forward | 1.9 cm back |
| Root of the scapular spine, lateral shift | 9.7 cm | 7.3 cm |

- **Side view:** the arm now rises in line with the head, as in the reference.
- **R14's own blend and path are unchanged.**
- **Shapes not re-baked yet.** The baked S5 shapes were made along v2, so the v3 render uses them unchanged.
- **Next:** re-bake along v3 as R15.

**Scope.** The same composition order is used for every movement that drives the clavicle through the coupled profile (row, push-up and the benchmarks). Changing it there is a Work / runtime-contract item, raised on PR #26.
