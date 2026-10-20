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


## Actual cloud outcome (20 October 2026)

**Diagnostic execution completed; global family-amplitude tweaking is rejected as a correction path in the tested range.**

- Final pinned source commit: `167551396b90297163992a1ecaa33ebde574f005`.
- Exact native-data workflow: https://github.com/anyangle1409-code/animation-software/actions/runs/39407075261 — SUCCESS.
- Eight synthetic/guard regressions PASS. All three checked original SHA256 values PASS. Actual 161-pose R53 captures and authentic R52 response are used; no synthetic substitute for the real-data screen.
- Original R52 scale 1.0/1.0 reproduces the marked R47 historical outline error **0.949949 mm** (1 mm guard) and the original dense 161-pose motion excess **40.644618 mm** (0.5 mm guard).
- Full screen evaluates **25** S5/S7 global amplitude pairs (0.90,0.95,1,1.05,1.10 on each). **Zero** satisfy both original outline and motion guards. The ranked best pair retaining the outline is the unchanged 1.0/1.0 baseline; it still fails motion.
- Artifact `original-v1-r54-s5-s7-screen-20261020` retains JSON for all tested pairs. A successful data pipeline never indicates a passing model.
- An earlier exact-head workflow 39406766371 correctly FAILED at the authentic motion replay when draft code took the norm of a difference instead of the project's existing difference of second-difference magnitudes. The formula was corrected without touching the numerical limit, and an eighth synthetic regression verifies this exact distinction. Its failed evidence remains available.
- No native candidate was built or saved. Original skeleton, Basis, shape-key geometry, skin weights, bounds, photos, production assets, PRs and corrective control definitions remain unchanged.

### Decision

**Do not rerun simple uniform S5/S7 amplitude scaling or 26-vertex averaging.** The next implementable experiment needs spatially selective shoulder/axilla deformation work. It must explicitly co-model the inherited sharp weight-gradient edge (18081–21057), the t=0.5 S7 curvature jump near posterior vertex 19057, and the R47 approved silhouette, with native Blender evaluation and all unchanged guards.

The sole previous weight exception covers exactly 26 vertices; do not silently enlarge it. Keep weights and shape modifications confined to separately named, reversible study files and approved source masks. An expanded weight region, new helper deformer, topological surgery or canonical bone move requires a separate owner scope decision. **R54 is an evidence milestone, not shoulder repair.**
