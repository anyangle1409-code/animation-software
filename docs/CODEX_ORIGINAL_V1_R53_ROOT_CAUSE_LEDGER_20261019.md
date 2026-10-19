# R53 shoulder root-cause investigation

Status: INVESTIGATION_IN_PROGRESS. No R53 correction, saved model or visual approval.

## Reconciliation and scope

Owner's 19 October brief replaces further blind numerical fitting with component isolation. Isolated branch `codex/r53-shoulder-root-cause-20261019` starts at consolidated HEAD `cb4a7ac361c6a8acbe2ca2b9b976e3241352e2a5`. Branch inventory pages 1–3 (212 entries) and open PR pages 1–2 (110 entries) were checked. No competing R53 was present apart from this new isolated branch. Relevant latest open PRs remain #111 shoulder/thorax guides, #112 coupled correctives and #113 movement benchmarks, updated 13–14 October. None is merged into this investigation or overwritten.

Read original shoulder handoff, R47 candidate note, R52 candidate results and R52 build note. R47's overall marked-pose outline was approved; its folded surface and complete moving clip were not. Preserve that intended arm-to-body relationship and newer upper-arm/elbow detail. A sub-millimetre marked-pose outline result alone cannot approve the moving arch or back bulge.

Canonical anatomy, skeleton, 1.82 m proportions, production assets, Claude work, Basis, topology, weights, HGPT_SHOULDER and non-S7 key coordinates stay protected. Weight examination and temporary key-value ablations are read-only diagnostics. Existing modification scope permits only separately named, reversible S7 skin candidates within original masks, caps, distal and anchor protections. No evidence yet supports publishing such a correction. Do not change bone geometry to fit the skin. No reference photos, traced outlines, third-party models or external assets enter Git.

## Evidence already established

* R52 run 39215634074 completed its search, retained iteration 125, saved no model, and failed actual native safety/motion checks. Its actual marked outline error was 0.949948 mm against unchanged 1 mm. Native dense motion excess was 40.644618 mm equivalent on the original grid against 0.5 mm; 6 marked reversed faces and 7 contact records remained. Thirteen benchmarks ran with six regressions versus R41. All detailed original failures remain in the R52 reports; none is waived.
* Read-only family isolation run 39245688426 found exactly identical bone endpoints and matrices between R41/R52 at all 161 poses. Removing S5 or S7 reintroduced severe crumpled armpit surfaces. This identifies dependencies, not a repair. It does not prove the shared skeleton is anatomically correct or stationary during the clip.
* Native temporal analysis identifies an R52 corrective slope change at vertex 19057 near t=0.5: baseline second difference 0.014902 mm versus R52 2.555191 mm. Coarse fitting missed intermediate motion. This supports a corrective-field cause for the R52-specific bulge, not a complete explanation of inherited arm-root shape.

## Completed containment check reconciled

Run 39258547533 finished successfully. Artifact `original-v1-scapula-containment-20261019` SHA256 `698aa0453039ca4e2c278c143ac9469dc74571432df32aa4ca6972f69e2f3f00` was downloaded and verified. Both skin meshes were topologically closed; all seven protected identity categories passed; scapula matrices matched exactly between versions.

At t=0.8 the existing provisional scapula guide had confirmed outside samples in both versions: up to 34.595 mm nearest-skin distance in R41 and 41.416 mm in R52. Anatomical landmark AI was classified outside at up to 56.898 / 62.327 mm respectively. GH remained inside; AA was outside by smaller distances. Ambiguous/on-skin samples are retained, not counted as inside. At lockout both versions coincide again, with guide samples outside by about 32.8 mm.

These are **project guide/landmark containment findings**, not exposed physical bone measurements. The authored guide is provisional, its shape and source landmark registration differ, and ray parity is not full anatomical validation. Their mismatch predates R52 and requires separation of guide registration, runtime bone transforms and skin ownership. It does not authorize altering canonical anatomy or simply expanding the back to enclose a provisional guide.

## R53 component-isolation capture

New native capture evaluates R41 and R52 in fresh processes with pinned Blender 5.2.1 and exact source/model hashes. Across 161 full-press poses it records actual skin, full vertex weights, group names, topology, rest/key geometry, modifier configuration, active key values, bone matrices/endpoints, and within-clip relative rotations. Clavicle/scapula are measured relative to thorax and humerus relative to scapula. Rotation magnitudes are explicitly not clinical ISB angles.

Independently mute S1–S7, then all seven together, restoring values after each evaluation while preserving HGPT_SHOULDER and K1 elbow keys. Record evaluated per-family displacements and descriptive edge/area ratios. Raw measurements do not certify fold/intersection safety or candidate acceptance. Compare exact bone matrices after ablation. Produce front/rear/side/three-quarter native frames and full-press comparison video. No fitter and no model-save operation exist in this capture.

## Task ledger

| Work | State | Evidence/next decision |
|---|---|---|
| Reconcile source, branches, PRs and R52/R47/handoff | Done | Pinned source and prior failures above |
| Inspect completed scapula containment | Done | Verified artifact, actual four-panel renders reviewed |
| Authoritative anatomy/biomechanics and real exercise photo references | Research gathered | Source URLs and limits in anatomy evidence note; do not import photos |
| Full weight/mesh/key/bone interaction capture | Prepared; native execution pending | New isolated diagnostic workflow; original tests untouched |
| Identify inherited arm-root cause from actual component results | Pending | Distinguish unsupported weight region, mesh arrangement and cancelling corrections |
| Reversible R53 correction candidate | Not started | Only after evidence supports one scoped change |
| Complete native acceptance tests, comparisons, owner review | Pending candidate | All original thresholds remain unchanged; no approval claim |

Runtime blockers: local environment has no Blender/bpy. Native tests/rendering run in the pinned GitHub workflow. Local diagnostic arithmetic tests and compilation run here. Search completion or workflow success is evidence completion only.

Five new diagnostic tests pass locally. Independent review found a packaging integrity gap: truncated bone arrays could broadcast as identical. A failing regression was added, then strict 161-pose array shape, ordered inventory, finite-data and protected-field checks fixed it. This adds evidence validation; no existing acceptance test or threshold changed.

## Execution checkpoint

Source commit `f9f9bcb241ea16a3b460f30babdf4245616c0163` launched native run https://github.com/anyangle1409-code/animation-software/actions/runs/39264438580 . It passed input-hash verification and five helper tests and entered native capture. Results remain pending at this checkpoint; no new native pass is claimed.

Additional analysis of the already verified earlier native artifact establishes within-clip motion: clavicle relative to thorax changes by up to 34.52 degrees, scapula by 42.41 degrees, and humerus relative to scapula by 55.21 degrees from the starting pose. These are general rotation magnitudes, not ISB components, prescribed anatomical angles or a complete validation. Thus the inherited rig does participate during elevation; the R52-specific defect cannot be attributed simply to stationary shoulder-girdle bones.

Existing S5/S7 native ablations also show broad opposing displacements: at t=0.5, 5,271 shoulder-region vertices have both contributions greater than 1 mm, with opposing dot products at 2,750. Their separate maximum contributions are 21.656 / 32.557 mm. Removing both and adding the individually measured contributions reconstructs the baseline within 0.000430 mm. This confirms a substantially cancelling corrective stack; cancellation itself is not proof of bad anatomy. Full S1–S7 and weight capture must establish which inherited component creates the arm-root contour before a correction is justified. Raw summary JSON records the region and limits.

Stored source affine-response audit covers 82 responses in the declared shoulder region. Minimum response singular value is 0.433915 and minimum singular-value ratio 0.409590. This does not reproduce the historical 0.004 near-singular case, but cannot rule out spatial weight-gradient collapse or validate triangles. Source rest extent in Z is 1.82000017 m. The full native R53 capture is still pending; no candidate acceptance follows from these measurements.

## Native capture completed; controlled hypothesis next

Run 39264438580 completed successfully at 14:09 UTC on 19 October. Artifact `original-v1-r53-root-cause-20261019` (12192947162, 230864003 bytes) was downloaded and SHA256-verified: `562f90894196d357079d1ca14c5f253c386684553b44a7a122b6929a29ef6f4d`. Both native processes completed 161 poses, preserved all seven protected categories, and had exactly matching bone matrices. Five helper tests passed in CI. Actual four-view stills and a native press video exist. This is diagnostic completion, not repair completion.

S1, S3, S5 and S7 are present; S2/S4/S6 are absent rather than falsely credited with a successful ablation. At all 161 poses, R41/R52 shoulder positions become identical to float precision when S7 is muted (maximum difference 0.00000373 mm). The same holds with all shoulder families off. Thus the R52-specific geometry difference is wholly attributable to S7, not different weights or bone motion. Muting S7 or all shoulder families exposes inherited bulging/curling and does not produce a usable surface. The actual t=0.8 four-view and ablation renders were inspected.

At posterior-back vertex 19057 (rest -0.193407, 0.086154, 1.376572 m), weights are 47.812% shoulder_cap_l, 37.553% upperarm_l and 14.635% muscle_lat_l, with no spine share. In the original back-motion region, 1064/1796 vertices have over 50% combined arm/shoulder/axilla/muscle-helper share; 698 exceed 90%. These are measured allocations, not automatic anatomical diagnoses.

Source inspection identifies a concrete hypothesis: `original_v1_muscle_line_helpers.ANAT['lat']` carries its origin with the scapula, and `_anat_points` places that origin at scapular AI. That is a scapula-to-humerus posterior-fold proxy, not the broad thoracic/pelvic latissimus anatomy described by UAMS. It resembles a teres-major connection in its origin relationship. The proxy is intentional historical code, so do not treat its name alone as proof of a defect. Its moving-origin influence on back skin now needs a controlled native experiment.

The follow-up probe keeps the existing AI rest point and humeral insertion but temporarily carries the origin with spine_03 instead of scapula, after installing all existing helpers. It changes only muscle_lat_l/r pose transforms. All canonical/rest bones, stored weights, all key coordinates and activations must match; all other pose matrices must be identical. It replays each baseline against the first capture to within 0.001 mm, measures actual R47 marked-outline error with the unchanged original outline function and 1 mm limit, and records 161-pose back motion. This is **not** an authored broad lat muscle, approved runtime change or correction candidate. Existing complete acceptance tests/benchmarks are not run on this isolated diagnostic; their original failures remain unresolved. Four-view before/after images and forward/reverse replay video must be labeled accordingly.

An independent review found no blocking source issue in this probe; actual native verification remains pending. No fitter is involved. A production/candidate helper-origin or weight change would expand the current S7-only scope and cannot be adopted silently.
