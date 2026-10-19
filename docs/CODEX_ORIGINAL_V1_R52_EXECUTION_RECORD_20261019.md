# SDD ledger — plan: docs/CODEX_ORIGINAL_V1_R52_IMPLEMENTATION_PLAN_20261019.md

Owner approved R52 at19October2026 07:59 Europe/London. Execute inline without another approval gate for the approved study.
Workspace: isolated new r52-work staging directory, GitHub API tree/commit/CAS workflow. No local checkout is available; no existing source file will be edited. Live HEAD will be checked before publication.
Pre-flight Task1 -> Task2: mapping uses95..166 ghost-zero temporal indices; kernel and fitter share the same72-node representation.
Pre-flight Task2 -> Task3: solution has dense_delta for actual native model and delta for explicitly labeled source-knot legacy diagnostics. Original tests remain unchanged; actual dense-native tests enforce equivalent thresholds independently.
Ruling: Original seven-control test interfaces cannot encode independent dense controls. Retain their unchanged source-knot-projection outputs as legacy diagnostics, add direct native geometry checks for actual acceptance, and do not conflate the two. Cost if wrong: a false test interpretation; study has no save/promotion.
Ruling: No full local Blender or full checkout suite is available. Use focused local numerical tests, original affine preflight and native CI with all old checks; record unavailable/skipped checks honestly.

Task1 complete:13 local tests pass; red/green logs retained. All83 coefficient arrays decode.
Task2 study implemented; local preflight still fails motion/step/outward limits and all failures retained. No passing-model claim.
Review: independent reviewer found Important checkpoint-ranking bug; feasible-first regression failed before fix, passes afterwards; focused suite13/13. Envelope guarantee wording corrected, duplicate download removed.
Ruling: Added early-outward0.05mm native guard and dual halfspace because a motion-only fit could suppress a jolt while retaining the swelling. This strengthens coverage; no original test is changed. Cost: a conservative study can remain infeasible.
Task2 local reviewed100-iteration preflight complete, failed/unsafe with retained0.854765mm motion,3.271742mm step,0.062665mm early outward,0.949999mm outline. Native decoder dependency regression RED->GREEN; full focused suite14/14. Task3 source prepared, actual native CI pending.
