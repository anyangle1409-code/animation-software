# Home Gym PT — phone-only cloud Blender execution ledger
Date: 2026-10-23

## Source of truth
- Repository: `anyangle1409-code/animation-software`
- Isolated execution branch: `work/phone-blender-workbench-20261023`
- Prior handover: `ad5b6f012427c2bc378534bb566c72ad37d41776`
- Previously VERIFIED initial cloud run: https://github.com/anyangle1409-code/animation-software/actions/runs/40001879043 (W8, V14, R120 completed successfully).
- Current code updates: `c064ecbd45f5b2ff6bdd2450fca2d65e12157232` (read-only bone/weight/rest coordinates) and `d0446b66bd299b3ceb2b6d0a28b67730402e41f3` (report integrity gates).
- Workflow: `.github/workflows/phone-blender-workbench.yml` (script/workflow changes trigger three cloud Blender inspection jobs **and** one report-comparison job).
- Worker script: `scripts/phone_blender/task.py`.
- Workflow runs page: https://github.com/anyangle1409-code/animation-software/actions/workflows/phone-blender-workbench.yml

## Important status distinction
- VERIFIED: The original cloud smoke test retrieved and opened each reconstruction in Blender 5.2.0 and preserved expected source SHA256.
- VERIFIED: Commit `c064ecb` passed cloud run `40003658521` (3/3); `d0446b6` passed run `40010003731` (3/3). All six model job outputs exist; W8/V14/R120 report ZIP digests were independently matched to GitHub.
- VERIFIED: New four-job workflow at `3f25e57` passed run [40015895314](https://github.com/anyangle1409-code/animation-software/actions/runs/40015895314) (three native models plus cross-model comparison). The combined artifact `12529220072` was downloaded, inspected and matched published ZIP SHA256 `3a8b94c53880b2ee94ec6fffaa0f96150c2c077b5501e5b75787b47feb4e6416`.
- NOT APPROVED: anatomy, archive equivalence, movement/grip deformation, and experimental muscle attachments.

## Immutable reconstruction IDs and hashes
- W8: run 39922636070, artifact 12487119841, SHA256 `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`
- V14: run 39922636070, artifact 12487932177, SHA256 `5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91`
- R120: run 39922636070, artifact 12488550235, SHA256 `fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb`
These are *reconstructions*, not verified originals. Artifacts expire under GitHub retention; earlier independent second-drive copies were recorded as verified. Check artifact availability afresh.

## Outstanding existing defects
- V14: 238065 vertices vs archived 238067 (two-vertex discrepancy).
- W8 archive content mismatch (offset difference up to 3.59286 mm against 0.01 mm tolerance); unresolved archived JSON discrepancies.
- Previously reproduced shoulder press/squat collapse/stretch/intersection quality-gate failures and grip solver failures in all three reconstructions.
- Recovered authoring rig 77 bones vs old production bridge 67; movement bridge applicability cannot be presumed.
- Anatomical left/right landmark mapping not independently certified. Weight-group centroids or bone names are only evidence for triage.
- Muscle attachment authorization, validated anchors and source acceptance are not satisfied.

## Latest read-only findings (verified)
- All three reconstructions have 77 bones, 77 named groups, 79 shape keys, zero unweighted vertices, and matching recorded rest-bone positions at six-decimal-metre precision.
- Group weight centroids >10 mm apart: W8→V14 4/77; V14→R120 24/77; W8→R120 30/77. See [digest-verified evidence](PHONE_CLOUD_CROSS_MODEL_EVIDENCE_20261023.md).
- Archive V14 right-leg cut loop 699 vs reconstructed 700; left cut loop 696 in both; feet 26877 vertices each and ring counts unchanged. New reconstructed report stages `back_depth_smooth` and `pec_junction` were absent from archive. **Source of final −2 vertices not proven**.

## Next safe steps (ordered)
1. Use documented V14 cut-loop and extra-stage discrepancies to design isolated read-only native intermediate-topology checks. Do not add/delete two vertices without evidence.
2. Prioritize shoulder press and squat failure localization by reviewing existing exact-frame render/geometry snapshots, especially scapula/clavicle/shoulder and hip/shin; grip failed before the right-hand test.
3. Independently verify anatomical coordinate handedness with landmarks before muscle bindings. Preserve muscle IDs and exercise contracts, but do not attach without approved source and anchors.
4. Maintain cloud test and report artifacts with hashes; no production merge/deploy, no source replacement.

## Guardrails
Laptop OFF is supported for GitHub-hosted scripts; the original-session search and interactive desktop-only Blender tasks remain unavailable until laptop return. No production asset, validated skeleton, `ORIGINAL_v1`, `PT_MODEL_VERSION 1.0`, original reconstructive artifact, Claude branch, merge or deployment should be changed. Do not commit binary .blend files.

The assistant/Work does not run indefinitely after chat termination. GitHub Actions does execute independently once triggered; further code commits require an active authorized cloud session.


## 2026-10-23 native failure-localization extension

Read [PHONE_NATIVE_SHOULDER_SQUAT_GRIP_LOCALIZATION_20261023.md](PHONE_NATIVE_SHOULDER_SQUAT_GRIP_LOCALIZATION_20261023.md) for exact read-only reproducible evidence.

- W8/V14/R120 diagnostic ZIPs from run39937882229 (W8=12495910312, V14=12494932817, R120=12495970648) were independently downloaded and SHA256 matched their recorded digests.
- New script scripts/cloud_body_analysis/localize_failures.py reads immutable triangle flags, geometry snapshots, dominant weight labels and finite-grid grip records. Does not import Blender or write a model.
- Seven new synthetic regression tests + five existing cross-model tests = 12/12 PASS in the native-localization cloud job at run40019611125.
- Native localization job PASSED in run40019611125 and again in corrected run40019877883.
- W8 75% shoulder press: 3,509 stretched, 3,072 newly flagged vs baseline; dominant proxy regions spine_03, shoulder_cap_r/l, scapula. Press flags recorded in all models; no anatomical approval.
- W8 squat sample7: 885 stretched, concentrated hip_crease_r/l, spine_01, pelvis. Pair collisions remain present and are not equivalent to distinct triangles.
- Grip: 263 attempts on runtime suffix l per model; combined acceptance unresolved, suffix r untested.
- Uploaded native ZIP: run40019877883 artifact12530565814, downloaded and SHA256 verified = 595a971897bedce022ca88f57f0cae1d59f2e526d7617484f382f58c5bf660ef. Contains movement_failure_localization.json and .md.
- Initial expanded five-job run40019611125 overall FAILED because older rest-compare job discovered numpy tests without numpy installed. Fixed in commit 78173b749d0e7ff669043847b2fd3d5567fb1517 by restricting rest job to its standard-library tests. **FINAL:** Corrected [run40019877883](https://github.com/anyangle1409-code/animation-software/actions/runs/40019877883) is **SUCCESS / all five jobs passed** (W8, V14, R120, cross-model compare, native localization). The native report artifact 12530565814 SHA256 is `595a971897bedce022ca88f57f0cae1d59f2e526d7617484f382f58c5bf660ef`; cross-model artifact 12530466695 was independently downloaded and its SHA256 verified as `dc69ccf09cc8806bdfea955cc0d418a8a030fa3dc84c7e6235769c2681d489bd`. Run is an infrastructure and read-only diagnostics pass only. Anatomy, archive equivalence, grip, movement safety and muscle attachment remain NOT_GRANTED / FAILED / BLOCKED.
- User may use a separate Claude cloud branch for *read-only V14 topology provenance investigation*. Keep Claude's lane separate. Do not overwrite original reconstruction artifacts or alter source acceptance gates.

Next: verify final five-job workflow; review 5 cm evaluated-coordinate shoulder hotspots at press sample6/8, build a reversible hypothesis checklist for clavicle/scapula/axilla skin deformation; do not edit preserved models, unfreeze anatomy, attach muscles, merge or deploy without explicit authorization. PT_MODEL_VERSION1.0 untouched.
