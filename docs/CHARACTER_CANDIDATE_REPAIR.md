# Repaired hand candidate validation

**The bilateral hand-weight repair succeeds for independent finger control and substantially improves weighted grips. The character is still a candidate because push-up floor contact, pull-up bar contact and deep-squat shaping need further work.**

Input SHA-256: `854cc1193498b49722ea7ccce92d47d8ba6166b3fc0055cb4666675b710e5a49`  
Repaired candidate SHA-256: `cc758295db337bbf7b040d229ec03c4eecbf566f8bc923011732f333149e5144`

The original file remains unchanged. The repaired copy retains 10,839 vertices and the authored surface. Rest-pose skinned positions differ by at most 0.0006 mm, from floating-point export precision. The repaired runtime skeleton contains 160 deform bones. The source's twelve weight slots were consolidated so the strongest four influences used by Three.js describe each repaired vertex consistently.

## What changed

- Removed finger/thumb influence from unrelated hand and forearm vertices.
- Fitted the wrist and 15 finger joints per hand to the actual mesh branches.
- Rebuilt each finger's weights independently and mirrored the verified repair to the right hand.
- Aligned split upper-arm/forearm deform pivots with the physical shoulder–elbow–wrist path.
- Stored per-hand grip-frame calibration in the GLB metadata.
- Updated the importer to prefer Rigify `DEF` bones when control bones are present, orient palms from the knuckle line, and read grip-frame calibration.

No exercise definition was changed.

## Verification

- **189 regular automated tests passed; 1 optional asset test skipped in the regular run.**
- The optional production diagnostic was then run explicitly with the repaired GLB: **1 passed**.
- TypeScript and production build passed. The existing bundle-size warning remains.
- All 10 proximal finger chains were rotated independently by 30°. Every finger moved its own side; zero opposite-side or central/forearm vertices moved more than 3 mm.
- Mapped anatomical-frame error stayed below 0.031°. Dumbbells remained locked to their hand frames to numerical precision.

## Movement verdicts

| Movement | Verdict | Exact result |
|---|---|---|
| Dumbbell bicep curl | **NEEDS MINOR FIX** | Both hands close coherently around the handle at bottom, halfway and top, and equipment stays locked. Small handle/skin intersections and angular low-poly knuckle folds remain. Peak maximum edge strain is 4.31×, down from about 17.4× in the supplied arm-repaired GLB. |
| Bodyweight squat | **NEEDS MINOR FIX** | Hands remain coherent. Deep position still has flattened inner-thigh/groin shaping and angular knee folds. Left-foot bone drift is 79.4 mm across 61 samples. |
| Dumbbell shoulder press | **NEEDS MINOR FIX** | Both hands keep a closed equipment grip overhead. Shoulder/armpit creasing and faceted wrist/knuckle transitions remain. Peak sampled maximum edge strain is 4.92×. |
| Push-up | **FAIL** | Fingers are now coherent, but the hands are not planted as flat palms; the skinned hand reaches about 45 mm below the intended floor plane at the bottom capture. Left-hand bone drift is 25.9 mm. |
| Pull-up | **FAIL** | Fingers are coherent, but bar enclosure and contact are not held throughout the rep. Left-hand bone drift is 39.0 mm. A source-proportion contact solve is still needed. |

## Quantitative comparison

| Movement | Maximum edge strain after repair |
|---|---:|
| Curl | 4.31× |
| Squat | 3.41× |
| Shoulder press | 4.92× |
| Push-up | 5.39× |
| Pull-up | 6.74× |

These maxima identify local deformation and do not alone determine visual acceptance. Fifteen key poses and 61 trajectory samples per movement were measured through the preserved-skeleton production path.

## Limits and next repair

The screenshots are offline renders of the actual production-posed triangles rather than live Animation Studio WebGL screenshots. The next code task is a character-aware contact layer that uses the imported hand/foot surface offsets when resolving floor and bar locks. After that, the remaining deep-squat hip/knee weights and overhead shoulder folds should be refined on another preserved copy.
