# Contact-corrected character validation

**The previous push-up and pull-up failures are corrected. The character now keeps its real palm, sole and grip surfaces on their contacts through the preserved-skeleton production path. Remaining defects are local shaping issues.**

Input SHA-256: `854cc1193498b49722ea7ccce92d47d8ba6166b3fc0055cb4666675b710e5a49`  
Contact-corrected candidate SHA-256: `e1c60f1367d7d491903a4a9cf7abe862804c8236d63cb612d35f6d4ce51a1208`

The original upload remains unchanged. The repaired copy retains 10,839 vertices. Its rest-pose skinned surface differs from the supplied file by at most 0.0007 mm, which is floating-point export precision.

## Changes

- Passed the final canonical lock targets into preserved imported characters.
- Added bounded source-skeleton IK for different arm and leg proportions.
- Measured floor contact from the imported palm and sole triangles rather than wrist and ankle pivots.
- Added source toe support automatically for the horizontal four-point push-up position.
- Applied character-only root reach compensation where a shorter source limb cannot reach the floor or pull-up bar.
- Oriented the actual imported palm from its knuckle line to the resolved contact frame.
- Smoothed the repaired GLB's forearm-to-hand weight transition for loaded wrist extension.

No exercise definition was changed. The source skeleton, mesh topology and bind-based production path remain in use.

## Verification

- **190 regular automated tests passed; 1 optional asset test skipped in the regular run.**
- The optional production diagnostic was run explicitly with this GLB: **passed**.
- TypeScript and production build passed. The existing bundle-size warning remains.
- Across 61 samples, push-up palms stayed from 0.00005 mm below to 6.01 mm above the floor; push-up foot surfaces stayed from 1.35 mm below to 0.29 mm above it.
- Squat foot-surface penetration stayed below 2.30 mm.
- Pull-up grip-frame error stayed below 1.04 mm.
- Every finger and thumb still passed the independent 30° isolation test, with zero opposite-side or forearm leakage.
- The absolute anatomical transfer still replaces the source A-pose/open-hand rest. Contacted limbs then receive the small source-proportion correction needed to put the actual surface on the intended floor or bar.

## Movement verdicts

| Movement | Verdict | Exact result |
|---|---|---|
| Dumbbell bicep curl | **NEEDS MINOR FIX** | Both hands close around the handles and the dumbbells remain rigidly locked. Small handle/skin intersections and angular knuckle folds remain. Maximum sampled edge strain is 3.82×. |
| Bodyweight squat | **NEEDS MINOR FIX** | Both feet now maintain floor contact within 2.30 mm. The deepest pose still has flattened groin/inner-thigh shaping and angular knee folds. Maximum sampled edge strain is 3.68×. |
| Dumbbell shoulder press | **NEEDS MINOR FIX** | Closed grips remain locked at full overhead. Shoulder/armpit creasing and faceted wrist/knuckle transitions remain. Maximum sampled edge strain is 3.68×. |
| Push-up | **NEEDS MINOR FIX** | Both palms are flat and the hands and feet stay on the floor. Maximum palm clearance is 6.01 mm and maximum foot penetration is 1.35 mm. Low-poly wrist and knuckle folds remain. Maximum sampled edge strain is 3.85×. |
| Pull-up | **NEEDS MINOR FIX** | Both grip frames stay within 1.04 mm of the bar and the fingers remain wrapped at the bottom and top. Minor bar/skin intersection and angular wrist folds remain. Maximum sampled edge strain is 8.23×. |

## Quantitative deformation

| Movement | Maximum sampled edge strain |
|---|---:|
| Curl | 3.82× |
| Squat | 3.68× |
| Shoulder press | 3.68× |
| Push-up | 3.85× |
| Pull-up | 8.23× |

Fifteen representative poses and 61 trajectory samples per contact movement were measured. The screenshots are offline renders of the actual production-posed triangles rather than captures of the Studio user interface.
