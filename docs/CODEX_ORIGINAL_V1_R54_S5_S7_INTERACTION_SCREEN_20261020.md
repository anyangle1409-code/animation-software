# R54: read-only shoulder S5/S7 interaction screen (20 October 2026)

**Status: diagnostic prepared, actual cloud results pending. No Blender model saved, no correction accepted.**

## Why

R52's approved R47 marked outline (0.949948 mm mismatch) still has bad full-motion behavior: 40.644618 mm dense-motion excess on the original-grid equivalent, contacts, reversed normals and benchmark regressions. R53 attributed the R52-specific deformation to S7 and identified opposing S5/S7 corrections. Its 26-vertex smoothing trial was **rejected** after increased seed-edge stretching; replay workflow run 39389114707 successfully executed the 83-response safety, 13-benchmark and historical tests, but this was evidence completion, not geometric acceptance. The local weight-only test remains rejected.

Before altering weights again, inspect a very small family of **read-only** scaling hypotheses using the actual captured 161-pose S5/S7 ablations and unchanged skeleton, weights and poses.

## Method

- Source baseline: immutable R41 and rejected R52 from the R53 root-cause capture (run 39264438580); R52 hash-pinned response (run 39215634074).
- Assert exact matching bone matrices, exact matched back/shoulder vertices, 161 full-press frames and baseline numerical replay.
- Since no-S5/no-S7 capture differs from the baseline only by the associated shape-key family at the same bones/weights, under existing linear-blend skinning a uniform amplitude change is represented by baseline + (1-s5)*ablation-S5 + (1-s7)*ablation-S7. This is a **counterfactual screen**, not a native installed key change.
- Evaluate 25 ordered coefficient pairs (0.90, 0.95, 1.00, 1.05, 1.10 for each family).
- For each pair compute the **unchanged historical** R47 marked outline measurement at t=100/160 with the exact source-matched algorithm and the **existing** R52 dense second-difference calculation over 161 poses, normalized by (160/40)^2.
- Report both pass/fail guard booleans without relaxing 1 mm outline or 0.5 mm dense-motion limits. Report even if zero pairs pass.
- The actual screen does **not** evaluate contacts, triangle normals, crease, mid-pose outline, 13 benchmarks or the early-outward displacement threshold for altered scales. Those require a separate native candidate and all existing checks. Never label a screened pair approved.
- The previous 26-vertex weight experiment is neither reused nor reauthorized by this read-only study; no new skin-weight patch is created.

## Scope and ownership

Isolated branch only. No edits to original blend, R41/R47/R52/R53 studies, bone geometry, Basis, weights, topology, elbow, any animation, production assets, original tests or acceptance thresholds. No private photographs, vendor meshes or outside asset packages.

## Acceptance of this diagnostic

- Seven synthetic arithmetic/scope tests pass.
- Authentic 161-frame R52 baseline values reproduce within 0.02 mm outline and 0.05 mm motion; mismatches abort without inventing data.
- Save a diagnostic JSON artifact including all 25 rows even when every row fails.
- Evidence success means **screen executed**, not that the shoulder is corrected.
- If no pair passes both preliminary guards, do not repeat global S5/S7 scaling as a prospective correction. Investigate spatially local, anatomy-informed S5/S7/weight transitions in a new separately authorised candidate with actual Blender surfaces. Preserve every existing failed test.

## Next steps

1. Inspect the exact-head CI screen and JSON, including any failed verification.
2. If a pair meets both screen guards, propose it for **actual, separate** Blender area/contact/normal/crease/13-benchmark and visual evaluation, still respecting frozen anatomy and model rights.
3. Otherwise retain the negative result, narrow down local posterior axilla influence ownership (deltoid cap / upper-arm / muscle_lat proxy / thorax) and design a local joint-weight/corrective strategy with protective masks; do not assume numerical redistribution will improve surface continuity.
