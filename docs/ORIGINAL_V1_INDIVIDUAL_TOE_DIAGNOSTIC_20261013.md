# ORIGINAL_v1 individual toe diagnostic checkpoint — 13 October 2026

**Individual-control implementation demonstrated. Mesh deformation gate FAIL. No owner, anatomical, physiological or production approval.**

## Actual phone review

- [Labelled neutral/posed phone sheet](https://chatgpt.com/api/library/files/libfile_bddac859014081918e2071b9507e5be6/download)
- [Neutral side](https://chatgpt.com/api/library/files/libfile_8264046c532c8191833d4b4235f5ee4d/download)
- [Neutral three-quarter](https://chatgpt.com/api/library/files/libfile_b62a8e1be2988191b7d183b635627dc2/download)
- [Hallux MTP-only 15-degree side test](https://chatgpt.com/api/library/files/libfile_ef3d8e57612c8191b3cd039b37576911/download)
- [Hallux MTP-only 15-degree three-quarter test](https://chatgpt.com/api/library/files/libfile_26bdb24aa1808191b7c4824daacd7ab2/download)
- [Second-toe PIP-only 15-degree side test](https://chatgpt.com/api/library/files/libfile_58f8fecb20c4819185b1a3fc35f556fe/download)
- [Second-toe PIP-only 15-degree three-quarter test](https://chatgpt.com/api/library/files/libfile_a29de8a37b388191b66db63e55b707b6/download)
- [Separate full-body native diagnostic scene](https://chatgpt.com/api/library/files/libfile_a8d6241a34f081918e4d8088e1ccc58e/download)
- [Rig/source/render manifest and PNG hashes](https://chatgpt.com/api/library/files/libfile_05cea984b4e8819185ea7ac360d73283/download)
- [196-frame trajectory measurements](https://chatgpt.com/api/library/files/libfile_f90bda21ba88819192af31d5927f4f62/download)
- [All ten final export hashes](https://chatgpt.com/api/library/files/libfile_546f0b6b4d048191979ef22e8570352f/download)

All images are actual Blender 5.2.1 renders. They display a disclosed left-foot surface extract below160mm to avoid overlap/occlusion; the complete original and trial bodies remain in the separate native file. The open ankle collar is a display crop. The two15-degree images are deliberately posed implementation tests, not neutral stance. No model substitute or generated illustration is used.

## What changed

A copied rig adds28 controls at the existing anatomical phalanx reference stations: twohallux segments and threeperlesser toe on each side. The copied runtime contains95 controls (67inherited +28new), **not** the current67-joint app/review schema. Original reference stations and original67-control rig are retained unchanged. This is a provisional control/skin experiment; reference endpoints remain low-confidence, surface-derived stations.

The PR104 body is copied without changing mesh coordinates, topology or corrective coordinates. Existing shared-toe influence on2192vertices is reassigned to independent chains and a foot-root blend. Five actual distal connected skin components per side identify the digits, with geodesic propagation into their roots and a nearest-ray fallback for unlabelled proximal vertices. Component vertex counts per side:137/137/137/87/63. An8mm IP influence transition and40mm MTP-root blend are artist assumptions. No bones are moved to fit the skin.

Neutral evaluated maximum skin difference from input is0.0000603mm. Body height, foot length and width are unchanged; feet remain309.156645mm long. Source scientific freeze and owner-rejected foot-shape statuses remain unchanged.

## Actual tests and unresolved failure

Four native tests were first observed failing on the prior67-control scene because individual controls/skin did not exist, then passing on the saved95-control scene:

1.95controls/28newcontrols exist; all67copied original bones retain source heads/tails, parents and rest matrices.
2.New controls match unchanged206-reference toe stations within0.002mm.
3.Shared-toe influences are removed from the trial body and all weight sums remain within0.000002of1.
4.All ten individually posed MTP controls move their own dominant skin, leave other dominant-digit samples within0.002mm, remain finite and return to identity. This is implementation isolation, not a human coupling claim.

The added full-mesh regression `test_hallux_root_does_not_reverse_triangles_at_15_degrees` **still fails**: the source-anatomical-right/suffix_l hallux has one orientation-reversed triangle versus neutral at+15degrees. Latest native suite result is **4PASS/1FAIL**, not green. The test is retained unchanged; no tolerance weakening or xfail was used.

Fresh motion diagnostics cover28controls ×7frames:0/5/10/15/10/5/0degrees,196samples. All coordinates are finite and each trajectory returns to neutral. **Sampled** maximum orientation reversals:3; minimum sampled height:−0.012974mm; maximum adjacent angular-step displacement:6.4177mm. These extrema cover vertices with an individual digit-group weight>0.1 and adjacent triangles, not every foot surface. They do not establish loaded stance, full-foot collision freedom, gait, tendon coupling, physiological limits or motion velocities.

The initial nearest-reference-ray partition wrongly assigned part of the hallux skin to digit2. Actual reversed-triangle influence records exposed this. Connected-component/geodesic assignment reduced the hallux regression from16orientation reversals to1. Tapering root weights did not clear the last failure. The remaining topology-labelled example is triangle15123 at forward207.221–214.090mm, a web/root region with competing digit influences. That identity came from the25mm-root intermediate; the final40mm-root trial still reproduces the one-triangle gate failure. No further blind parameter sweep is justified.

The skin still has exaggerated tubular toes, crude web/root geometry and excessive length. Control independence does not solve those defects. A deliberate web/root skin and influence redesign is required before stronger movement claims.

## Source and output identity

| Item | Exact identity |
|---|---|
| Input code | PR104, `16d8d50713326e08068d666d82be9eb7c451aa80` |
| Input native candidate | `HomeGymPT_ORIGINAL_v1_NEUTRAL_TOE_PAD_TRIAL.blend` |
| Input candidate SHA-256 | `6ee29cec4dfd4b2de867f8dbcce4364203bc5f40182deeea72e60e01683438e2` |
| Historical original source | `HGPT_ANATOMICAL_AUDIT_r95_a003.blend` |
| Historical source SHA-256 | `670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56` |
| Diagnostic native output | `HomeGymPT_ORIGINAL_v1_INDIVIDUAL_TOE_TRIAL.blend` |
| Output SHA-256 | `5eab3dad1338b90e98f27076f4ed181785029d35e0066312f2d0511031e46316` |
| Work branch | `codex/original-toe-articulation-trial-20261013` |

The builder fingerprints retained input mesh, faces, original group identities/weights, all corrective coordinates and both original rig rest/world matrices/endpoints/lengths/parents before and after execution. Input native bytes are checked against their exact hash. The copied67bones and new source-station controls are checked after native reopening. Original input body/rig objects remain in the scene as hidden references. The trial uses PR104 geometry, including its902vertex plantar-pad experiment; it is not byte-identical r95skin.

No GLB was exported and no existing model/GLB, production rig, source skeleton or LaneG software was replaced. The95-control trial must not be sent to the current67-joint integration as if compatible. All acceptance flags remain false.

## Primary research boundary

[Oosterwaal et al.2016](https://link.springer.com/article/10.1186/s13047-016-0152-7), DOI10.1186/s13047-016-0152-7, distinguishes foot joints in a26-segment kinematic model and constrains interphalangeal motion through coupling. Its results use subject-specific scaling and skin markers, with acknowledged uncertainty. It supports separating joint representations; it does not validate our source stations, trial axes or15-degree probes. No study software, scan geometry or universal coupling ratio was imported.

[Three-dimensional MTP kinematics during walking](https://pubmed.ncbi.nlm.nih.gov/25566536/) is retained as a functional-axis reference, not a numerical target adoption. Generic world-Z roll alignment in this trial is an artist convention, not a verified functional joint axis.

## Restart and gate

Resume from this exact diagnostic branch/head and candidate hash, preserving the failing hallux regression and the196sample report. Next: inspect the actual web/root triangle neighbourhood and source-compatible joint-frame/skin relationships, then make a separate deliberate refit. The280mm shortening proposal remains blocked by endpoint semantics/reference containment. Independent shoulder SC/AC/GH authority and provisional runtime/skin refit remain available Work tasks. Do not rerun unchanged CT intake or historical sweeps.

Independent fresh review found no critical implementation defect; it identified sampled-extrema scope, stale ray-assignment wording and missing copied-bone comparison. Scope/wording were corrected and the copied67bone checks executed. The model deformation failure remains explicitly open.

Ruling: retain the diagnostic prototype and known failing regression as evidence, without accepting or merging it. Cost if the provisional controls/artist weights are unsuitable: discard the separate trial; original input/production assets remain intact. This checkpoint completes a diagnostic milestone, not the model or foot correction.
