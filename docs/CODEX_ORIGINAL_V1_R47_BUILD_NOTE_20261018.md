# R47 approved inward shape study — build note

Owner approval:18October2026,19:05 Europe/London, following the concrete cyan full-outline overlay. Scope: reshape local arm-root and upper-side skin; retain newer distal-arm/elbow detail and frozen skeleton.

R46 was rejected. Its locked upper-arm source mask made the marked outline uneditable, and its outward R42 body-fill target contradicted the owner's full-outline reference. See CODEX_ORIGINAL_V1_R47_SHAPE_SCOPE_AUDIT_20261018.md.

R47 is a short direct authoring study, not another long optimizer run. A smooth project-authored inward side-cap envelope acts around the shoulder/upper flank, fading before the distal arm and waist. The gains at110/120/130/136/145/156/166 are0/.55/.95/1/.70/.20/0. Source coordinates are recovered using the retained exact native response matrices; dense S7 sampling is unchanged. One global scale enforces BOTH existing45mm caps without clipping individual vertices.

## Protection and tests

- Any vertex at least0.16m along either humerus at ANY of the seven original controls is fixed at EVERY control. Distal fade begins at0.12m.
-166, anchors18633/18639 and centre seam remain fixed.
- Frozen bones, topology, Basis, weights, HGPT_SHOULDER and all other non-S7 keys are not editable. The native renderer checks their in-memory identities before/after installing S7.
- Own test: scripts/tests/test_original_review_r47_authorized_scope.py. The previously locked-root regression was observed failing before implementation. A stronger any-angle distal test caught0.109mm leakage, then passed after applying global distal protection. Four tests pass against the actual prepared source/solution.
- Native BVH/area/orientation checks at83 responses and13 unchanged movement benchmarks run without relaxed thresholds. Motion excess0.5mm and posterior crease excess2degrees remain unchanged. The posterior check covers the expanded region.
- All five legacy contour/front tests execute unchanged; all outcomes are retained. R42 outward-fill and R41 proximal-line requirements reflect the superseded shape interpretation. Their failures will not be hidden or converted to passes. No old test is edited.
- No model-saving step exists. This study cannot claim model acceptance even if a subset of tests passes.

Outputs: separately named codex_review_r47_study_20261018, full rear/three-quarter R46/R47 comparison, matching close-ups and actual press videos. Everything is rendered in pinned Blender5.2.1 from the authored geometry. Owner reference photos and traces remain out of the repo. The authoring module accepts only the native dataset and project-authored parameters, not private image files.

Workflow: .github/workflows/original-review-r47.yml. Normal commits on the authorized branch only; no main merge or force push. Final results are written to CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R47_20261018.md. Report every regression honestly; owner shape review comes before any further long fit.
