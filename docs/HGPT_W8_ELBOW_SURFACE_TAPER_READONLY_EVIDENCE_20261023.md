# Home Gym PT — W8 distal upper-arm silhouette taper: observed, not yet judged anatomically

**23 October 2026 — independent read-only saved-geometry inspection; NO MODEL ALTERED.**
Owner reports upper arm looks unnaturally thin where it meets the elbow, despite brachialis, biceps, brachioradialis and triceps layers supporting natural continuity.

## Input sources and exact identity

- [Original native Blender visual diagnosis run 39937882229](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229), [W8 artifact 12495910312](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229/artifacts/12495910312). Downloaded ZIP **75.3 MB**; SHA256 independently recomputed and matched GitHub: `3be4322ba67da8b3827c96c0afdb58ffa8adb998cf8d1814aab0978a9e68d63e`.
- `W8__shoulder_press__sample00/06/08__geometry.npz`: rest/posed points, fixed triangle topology, vertex dominant-weight labels. Each rest coordinate array is identical across these samples (219,974 vertices); records are from the same unapproved recovered W8 reconstruction.
- [Source W8 rest-rig inventory](https://github.com/anyangle1409-code/animation-software/actions/runs/40034242376/artifacts/12535503988), independently downloaded ZIP SHA256 = `41a5f00bed46842a7b4857d35893a653695ca23d24d237234dedaadaae63a822`. Rest controls `upperarm_l/r` span ~299.47 mm from head near shoulder to tail near elbow in body coordinates. **Bone control tail is NOT a certified anatomical elbow centre.**
- Source skin, rig, production app and .blend file all unchanged.

## Method: precisely defined *proxy*, not measured anatomical circumference

1. On each side, use W8 **rest** upper-arm control head/tail to define a line, then select the same original skin vertex IDs in a narrow band at 55% (**mid upper arm**) and 95% (**distal upper arm near elbow**) of the rest control span. Each band is ±2.5% of that span, with a ≤9 cm radial locality guard.
2. Admit only preserved dominant labels `upperarm_l/r`, `forearm_tw0_l/r` to exclude torso and unrelated surfaces. Distal band retained 225 vertex IDs each side; middle 398 (suffix l) or 397 (suffix r).
3. For the exact same vertices, compute the two **largest** square roots of 3D covariance eigenvalues in resting points and in actual evaluated press frames. The narrow band has a much smaller longitudinal spread, so these serve as **rotation-invariant transverse surface spread proxies**. Multiply the two to make a *spread-product*; distal/mid **ratios are dimensionless**.
4. This covariance spread-product is **NOT** true circumference, area, tissue volume, skin thickness, muscle cross-section or an anatomical acceptance threshold; no external reference shape has yet been fitted. Model's world/object coordinate equivalence and true joint location require native calibration. No per-muscle volume can be inferred from labelled skin weights.

## W8 numerical observations

| Condition | L mid spread-product (arbitrary mm² covariance proxy) | L distal spread-product | L distal/mid | R distal/mid |
|---|---:|---:|---:|---:|
| Rest skin | 2581.36 | 1051.67 | **0.407** | 0.408 |
| Press frame 0, elbow bent | 2592.47 | 1050.37 | **0.405** | 0.406 |
| Press frame 6, 75% | 2563.79 | 1097.39 | **0.428** | 0.428 |
| Press frame 8, overhead end | 2656.31 | 1108.71 | **0.417** | 0.417 |

For L suffix, mid rest transverse standard deviations ≈**47.10 and 54.81 mm**, distal rest ≈**31.94 and 32.93 mm**. At frame 8, mid ≈44.89/59.18 mm and distal ≈33.06/33.54 mm. R follows nearly the same pattern.

**Narrow, defensible inference:** this **particular distal-band narrowing exists in the rest surface** and its relative covariance proxy remains broadly similar across three press poses. The saved press animation does not newly produce a large reduction in this specific proxy. This does **not** rule out local elbow skin pinch during other motion (e.g., forearm pronation, deeper curl), and it does **not** establish whether the *rest* taper is anatomically too narrow. The previous owner's assessment that it looks visually wrong remains a high-priority human-art review item.

## Correct anatomical response, not fake inflation

- Confirm upper-arm/lower-forearm surface *silhouette* from identical front/back/side/three-quarter lenses in neutral, elbows 45/90/120° and different pronation/supination poses.
- Review actual bone-local origins and insertions of biceps long/short heads, underlying **brachialis** on distal anterior humerus, brachioradialis on forearm, triceps distal tendon/posterior elbow, and fascia/skin; existing PR124 semantic IDs do not constitute verified fitted tissue.
- Fit **separate superficial/deep volume** only after signed outer skin contour and real bone/landmark/side are validated. A smooth overlapping outer surface is the desired output, not exposed cylinders or an artificial deltoid/biceps swelling.
- Measure and compare true posed cross-sectional planes from reviewed elbow centre, humeral shaft axis and moving attachment frames; register actual segment transforms for each pose before accepting area, circumference or slope of taper.
- Avoid forcing symmetry or muscle size from these numeric proxies. A normal biceps naturally tapers into its tendon; the question is whether total arm/forearm structures maintain plausible volume and skin continuity.

## Quality status

- Immutable source archive SHA, stable IDs, bilateral PCA proxy existence: **PASS for evidence integrity**.
- Owner-reported unnatural visible elbow transition: **OPEN for anatomy/art review**.
- Joint-axis coordinates, true elbow centre, cross-section anatomical comparison, muscle overlap and new isolated curl pose: **NOT_APPROVED / NOT_RUN**.
- Existing press and squat deformation / grip gates **FAIL**; no condition is promoted by this analysis.

**Next execution focus:** automated source-pin regression of the same band spread across saved frames, coupled to an isolated elbow bend / radioulnar forearm rotation test with actual bone centres and contact/skin metrics. This should enable a genuine before/after measure when a **separately authorized** experimental candidate is created; do not alter preserved W8/V14/R120 sources.
