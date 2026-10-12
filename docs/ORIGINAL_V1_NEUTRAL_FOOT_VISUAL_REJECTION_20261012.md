# ORIGINAL_v1 neutral foot visual rejection — 2026-10-12

## Status

**Owner visual acceptance: REJECTED.**

This checkpoint corrects the interpretation of the earlier comparison sheet. The `-30°` toe-control sample exaggerated the upward-pointing appearance, but it is **not** the sole cause. A native identity-pose inspection of the actual current ORIGINAL_v1 body shows that the distal toe surfaces are already suspended above the reference floor in neutral.

This document records evidence only. It does not approve, merge, or install a mesh correction. The approved anatomical skeleton remains the source of truth and was not moved.

## Exact source identity

| Item | Value |
|---|---|
| Review branch | `codex/original-foot-proportions-candidate-20261012` |
| Branch head before this documentation commit | `7c80c48d98a8ed4680bc33ce2ebc538da0613a38` |
| Latest focused PR CI | run `38230062412`, success |
| Native Blender source | `ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend` |
| Native source SHA-256 | `670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56` |
| Body object | `HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE` |
| Runtime skeleton | `HGPT_CANONICAL_V4_ORIGINAL` |
| Body topology | 17,946 vertices |
| Runtime joints | 67 |
| Live toe-authoring file | `scripts/original_v1_o2_body.py` |
| Authoring-file blob SHA | `28a4d954d806f1ca9ef7cef1c625ad9c2c833346` |

## Native identity-pose measurement

The runtime pose was cleared to identity. No toe-control rotation was applied. The overall body/foot minimum was approximately `-0.000000226 m`, confirming that some plantar surfaces touch the reference floor. The distal toe samples, however, remained above it.

Measurements below are bilateral: the left and right values were identical at the recorded precision.

| Digit | Distal minimum above floor | Median above floor | Maximum above floor |
|---|---:|---:|---:|
| Hallux / digit 1 | 9.327 mm | 18.424 mm | 28.359 mm |
| Digit 2 | 9.327 mm | 18.752 mm | 28.205 mm |
| Digit 3 | 8.587 mm | 15.460 mm | 23.035 mm |
| Digit 4 | 8.514 mm | 14.896 mm | 22.091 mm |
| Digit 5 | 8.723 mm | 13.928 mm | 21.255 mm |

Result: **neutral toe-ground acceptance is false**. Every distal digit sample begins at least about 8.5–9.3 mm above the floor, even though other plantar regions contact it.

Both native foot lengths remain `309.156645 mm`. This checkpoint does not resolve or authorize the blocked 280 mm proportion candidate.

## Root cause in current mesh authoring

The current visual defect is consistent with the procedural toe construction in `build_toes()`:

- The toes are built from repeated near-circular cross-section rings.
- Ring centers follow fixed elevated Z values rather than a plantar/contact profile.
- Forward dome caps preserve the rounded, tubular tip appearance.
- The final ground operation only clamps vertices below `2.5 mm` to the floor, so it grounds parts of the sole/forefoot but does not bring the distal toe surfaces down.
- The runtime supplies one shared `toe_l` / `toe_r` control per foot. It does not provide independent MTP/IP articulation for each digit, so the test pose lifts all five toes as one block.

The resulting visible problems are:

1. neutral distal toes suspended above the ground;
2. long, straight, tubular digit silhouettes;
3. abrupt toe-root transitions into a simplified forefoot;
4. inadequate individual toe articulation;
5. foot length still approximately 30.92 cm.

## Relationship to the weights-only candidate

The separate 724-vertex weights candidate remains a narrow, reversible contact/deformation experiment. It reduced one unloaded toe-lift sample's forefoot floor crossing from `1.509 mm` to below `0.001 mm` while preserving native mesh coordinates, skeleton geometry, ankles, height, and neutral footprint.

That technical result does **not** correct the rejected toe shape, the neutral distal suspension, the excessive foot length, or missing individual articulation. It is not planted-gait, anatomical, physiological, production, or owner approval.

## Safe correction gate

Any later geometry proposal must be a separate reversible candidate and must:

- keep the approved skeleton, ankle positions, body height, heel position, ground reference, and bilateral symmetry unchanged;
- resolve source-compatible ankle/heel/MTP/toe-endpoint semantics before shortening the skin;
- reshape the skin to the skeleton rather than moving the skeleton to fit the current mesh;
- establish a credible plantar envelope, arch, heel, ball/forefoot taper, toe-root web transitions, and descending distal toe contact profile;
- avoid the current tubular ring/cap silhouette;
- provide unobstructed neutral left/right side, top, sole, front, rear, and three-quarter views with no overlapping posed foot and no near-clipped ankle;
- test neutral contact, toe flexion/extension, ankle motion, skin weights, and foot-ground contact numerically and visually;
- remain unmerged and unapproved until explicit owner acceptance.

The existing 280 mm target remains a provisional population trial only. A forced 280 mm shrink is blocked because the current low-confidence, surface-derived reference envelope would require `304.161597 mm` before skin and would leave `24.161597 mm` of reference protrusion. No skeleton point is to be moved to make the target fit.

## Acceptance flags

| Gate | State |
|---|---|
| Owner visual acceptance | **REJECTED** |
| Neutral toe-ground contact | **FAIL** |
| Foot shape/proportion accepted | **NO** |
| Individual toe articulation | **NO** |
| Anatomically validated | **NO** |
| Production-ready | **NO** |
| Skeleton modified | **NO** |
| Geometry correction installed | **NO** |
