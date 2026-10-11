# Master programme: independent execution checkpoint, 10 October 2026

This continues the owner's supplied programme, retaining the canonical phase
numbers and source-first acceptance gates. It is not a production release.
Working branch: `codex/source-skeleton-blender-measurements-20261010`, draft PR26.
Starting verified checkpoint: `00f06ea2346f5ccad741dcab26b087e3c909550e`.
Canonical anatomy remains `7761a12d684f576bf49a0bac7563d5b5ae9b8998`.
Readiness remains **0 READY / 9 PARTIAL / 3 BLOCKED**. No c005, canonical
promotion, V-series intake, production adapter, mesh refit or asset overwrite.
Machine-readable queue: `MASTER_AUTONOMOUS_EXECUTION_20261010.json`.

## Reconciliation and preserved work

Remote heads were fetched before these edits. PR27 runtime-side diagnostic
`9ee0cd30c542013a539e71a08577b7b396f5be4d` and PR29 radius/ulna multi-control
diagnostic `6266ab5edefe0108041c9150dedd12ff3a8ce7bd` are independent newer
work; neither was merged, rewritten or duplicated here. They identify crossed
anatomical/runtime aliases, not justification for reflecting source geometry.
Their 130 links are not 130 separately validated bone surfaces.

Pre-push fetch also discovered independent rib-orientation preflight
`d437afacafdb37ed18dc16bd820ee091ce71b31f` and primary thoracic wedge evidence
`0dc7174b9fede23a63f0f484ebc7cc24998ac3ac`. Preserve those branches and read
their latest reports before further rib/spine source work; neither was merged.

PT-App live branches and open PRs were inspected read-only. Intake-hardening
branch is `3da21c03cf0aa45b8fb716f6605a24a00c3597dd`; Claude's active PR1
is `243dbe23dbca74c4984da08ebd6b6bef20d859f7`. No application changes were
made: anatomy and accepted runtime binding remain upstream dependencies.
Existing Claude laptop checkout was clean and was not modified.

## Corrected real Blender render-path defect

Problem: a relative path given to Blender could resolve outside Python's output
directory. Images then existed elsewhere, while the review manifest's image
hash map was empty. This was an artifact-location defect, not anatomy.

Evidence: a real empty-scene, 32px native Blender regression failed before the
fix and passed afterward. The render boundary now passes `Path(path).resolve()`.
No render settings or anatomical coordinates changed. A headless Blender CI
job was added alongside the existing Windows/Linux source-evidence jobs.
Its first remote execution is still pending at this checkpoint.

Subsequent verified result: implementation commit
`87eec970d974e772eea61c96c84e116e042e7cde` passed all three jobs in
[CI run 38064243229](https://github.com/anyangle1409-code/animation-software/actions/runs/38064243229):
actual Ubuntu Blender native render, Windows source provenance, Linux source
motion gate. This closes only the artifact-location fix, not anatomical Phase9.

Actual c004 re-export produced all 20 expected views in the requested relative
directory. All 20 manifest PNG SHA256 values were independently recalculated
and matched. Input Blend hash remained
`2a9401e77c173280b0b6aa124330e3e48162d4cd1d1d1a1c77057feae7c874b7`.
Manifest SHA256: `1caa99dba2bc930702c5d3011796d7d397c574142d6b795020c1c60163b03578`.
These are display sticks and joint markers, not accepted anatomical surfaces.
Old empty manifests are retained honestly, not retrospectively repaired.

## Actual ORIGINAL-v1 forearm, helper and grip measurements

Blender **5.2.1 LTS** ran the existing read-only audits on laptop r95. Input
SHA256 before/after: `8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd`.
The scripts can install diagnostic helper/corrective state in memory; they do
not save the Blend. This is not a production-path acceptance claim.

Actual rest coordinates place runtime `forearm_l` at X=-0.215m and `_r` at
X=+0.215m. Both extend Z=1.190 to 0.920m. Source anatomical left is +X, so
report side labels below are **runtime suffix sides**, not canonical anatomy.

Grip/wrist audit: `grip`, `curl_handle`, `pullup_bar`, `pushup_bottom`, both
runtime sides. Curl and pull-up each measured 99 digit-owned inside-handle
vertices per side. These counts can repeat shared ownership and are not a
unique-mesh collision count. Minimum signed thumb distances were about
-1.627mm. The existing closer allows roughly 1.5mm soft contact for free
vertices; therefore these measurements are not automatically an anatomical
defect or grounds to change accepted tolerances. Contact closure remains open.
Push-up measured wrist bend 79.86942 degrees on both sides; no physiological
acceptance is inferred from that authored diagnostic angle.

Joint-path audit: three poses above (excluding `grip`), nine fractions from
0 to 1 in 0.125 steps, 66 non-root runtime controls, zero reported path flags.
This thresholded diagnostic does not prove continuous real human motion,
contact at every sample, source joint locations or bone shape correctness.
Curl endpoint local forearm twist was +76.7586 degrees for `_l`, -76.7586
for `_r`; helpers counter-rotated by full/half parent twist (-76.7586/-38.3793
on `_l`, opposite on `_r`). These are relative child rotations; accumulated
world rotation is not the same quantity. Authored curl elbow abduction
component was -9.8163 degrees on both sides, requiring source/pose-method
review rather than automatic classification as a joint defect.

Forearm axial skin stress: existing implementation actually measures only
`forearm_l` despite its header claiming both sides. Six samples: +/-45,90,150
degrees. 588 selected vertices; minimum mean-slice radius ratios 0.9808,
0.9239,0.7935 respectively. No bilateral twist-skin claim, no physiological
range validation, and +/-150 is stress testing, not exercise prescription.

Actual deformation renderer subsequently produced 12 new images for curl and
pull-up, including hand/elbow close-ups; all 12 manifest hashes verified and
r95 input unchanged. Curl: volume ratio 0.9946, 318 compressed edges (<0.6),
24 stretched edges (>1.6), 138 self-intersecting face pairs. Pull-up: volume
ratio 1.0139, 346 compressed edges, 699 stretched edges, zero reported
self-intersecting pairs. These thresholded outputs are not acceptance tests.
Visual review of curl hand and pull-up front confirms reviewable output;
overhead axillary shape remains visibly irregular and neither exercise is
approved. Contact diagnostic penetration includes designed soft-contact
allowance and must not be silently reclassified as an anatomical defect.
Images: private `r95-grip-contact-review-current/`.
Report SHA256 `f09fca6be2937f018b2a1ed73eb710c202a54a6dedd8f1ef3ffc9e57813e1aa1`;
render manifest SHA256 `36be30dec098d24a9deb5e1f3009847b6153296f5e7e50961474dae96d3e0e26`.

Raw diagnostic report hashes (files private on this laptop):

| Report | SHA256 |
|---|---|
| r95-bilateral-grip-wrist-current.json | af38bc5bf56f287c07df1ff8d87c15d81d0850eab775c73abcf77f6df8a95650 |
| r95-forearm-twist-current.json | 1c5fb36ec7903e948fcb494ff8f6ecbefa629ee203173b866ee9ece1383f583f |
| r95-forearm-grip-path-current.json | df36b4b18f8373a358cfcdc85c898f31cacafbbaf0756ee021951645327a5835 |

## Regression status and exact continuation

The first partial-checkout full suite ran 1097 tests: 20 failures, 71 errors,
one skip. Checked-in source, coordination and candidate JSON metadata were
then restored only in this isolated worktree. Expanded-checkout full-suite
results are still pending; do not claim full regression green.
Focused source-motion gate: 10/10 tests passed. The real native render-path
test passed again after clearing factory Cube/Camera/Light to make its scene
genuinely empty. Independent code review found no critical/important issue;
its scene-description mismatch was corrected and the Blender test rerun.
A direct production-control check establishes one remaining omission:
`ORIGINAL_V1_WORK/candidates/review/milestone_r95/milestone_anatomy_shoulder_1.png`.
Restore checked-in visual evidence after the active suite ends; do not loosen
production-control expectations or rewrite immutable historical evidence.
Investigate Git CRLF checkout conversion separately from semantic regressions.

Private outputs are under
`C:/Users/Mark/Documents/Codex/2026-10-09/referenced-chatgpt-conversation-this-is-an/work/private-source-skeleton-20261010/`.
Corrected views: `c004-render-path-verified/`. Earlier actual Blender source
and motion work remains described in `LAPTOP_ACTUAL_BLENDER_AUDIT_20261010.md`.
All medical source bytes remain outside Git.

Next Work/Claude session:

1. Fetch live heads and inspect local dirt before any edits. Preserve PR27/29
   and check whether they advanced; never force-push.
2. Finish classifying the expanded-checkout full suite, restore exact missing
   checked-in visual bytes, and distinguish byte-identity from semantic failures.
3. Verify the native Blender CI job on the published commit. Reproduce locally
   using `--background --factory-startup --python-exit-code 1 --python
   scripts/blender_tests/test_skeleton_review_render_path.py`.
4. Use the existing actual measurements when reviewing forearm multi-control
   binding. Do not rerun the expensive 135 c004 sweeps or install a production
   side adapter without its acceptance evidence. A bilateral twist-skin audit
   is still missing, as is primary physiological motion verification.
5. Continue independent pelvic landmarks, endplate surfaces and carpal/tarsal
   contact evidence. The private CT groups are individually contiguous but
   separated by a nonuniform boundary; do not pretend they are a single
   uniformly spaced image volume. Seven independently accepted pelvic
   landmarks and accepted registration are still missing.
6. Gates 6/9 remain open. Do not treat numerical sweeps or rendered sticks as
   an accepted full skeleton, natural functional motion or production assets.

No laptop installation is needed: Blender is available here. Laptop work is
needed for reviewing these private artifacts and new source-bound surfaces,
not for repeating already executed setup.

## Subsequent full-suite/environment checkpoint

Expanded full suite completed: **1097 tests, 20 failures, 41 errors, one skip**,
1074.889 seconds. Private trace SHA256
`e8f5a4ab17ab5cf5f1586540d11fdba2afa7a75c49fb60b411f3f7c269cbcd9e`.
This is not a full-suite pass. Errors include absent SciPy, missing sparse
visual bytes, Windows long paths/copy failures, existing r96 orchestration
mismatch, and Windows symlink privilege 1314. Failure classes additionally
include exact-byte report/input identity, missing candidate GLBs and historical
production-control assertions. Do not conflate those with anatomical accuracy.

Proven path cause: the tracked c003 Blend exists at a 275-character normal
path but Python reports missing; an extended Windows path can see it.
An attempted move of this isolated worktree was refused by Windows; nothing
was moved or deleted. A separate **detached verification worktree** at
`C:/Users/Mark/Documents/Codex/hgpt-source-blender-audit` checks out exactly
87eec970; c003 path is 204 characters and its bytes match historical SHA256
`3962215043cebbcf71f4d0127e1e457b8974a01bca3d304035f8dcdca51e6ab4`.
The branch's original worktree remains the sole editing checkout.

The verification checkout restores milestone_r95 image evidence and the two
candidate GLBs, uses command-local `core.autocrlf=false`/`core.longpaths=true`
without changing shared Git configuration, and has SciPy1.18.1 available.
Direct production-control build now reads r95 and keeps production_approved
false. Targeted retest of all 61 previous failed/error cases is running;
previous missing imports load their complete modules, so its test count can
exceed 61. The first retest command duplicated method names and loaded 59
invalid selectors; that invocation is not test evidence. The corrected retest
uses the complete qualified case names. Log: private
`targeted-short-path-lf-scipy-corrected.log`. Do not repeat the
whole 1097-test suite merely to poll this checkpoint.

## c004 reconstruction serialization correction

The clean short-path/LF environment isolated a genuine remaining Windows
serialization bug: full c004 record reproduction differed in **exactly two
provenance strings**, `candidate.derived_from.record` and
`candidate.arm_input_correction.blend.reused`. Native `str(relative_path)`
wrote backslashes where the immutable record uses forward slashes. Both
serialization expressions now use `as_posix()`. No geometry, measurement,
stored record, source hash or acceptance expectation changed.

All **14 unchanged c004 tests passed** in 15.963 seconds using the edited
implementation and the exact Git-LF short-path input files. The test invocation
temporarily rebound only the builder's ROOT/A003/C003/C003_BLEND paths to the
verification checkout; anatomical values/hashes were not mocked. The unchanged
immutable-input pins, complete record reproduction, input guard, movement
reuse and hash-seed mirror checks passed. The production Windows CI job now
installs NumPy and runs the entire same test module without those rebindings.
That CI step subsequently passed, without input rebindings, on published
`27b3a9a1c740ff0f4f9cce5534465d22691f00fb` in
[run 38065155129](https://github.com/anyangle1409-code/animation-software/actions/runs/38065155129).
All three jobs passed, including actual Ubuntu Blender and all 14 c004 Windows
tests. This closes only the serialization defect, not anatomical readiness.

## Completed targeted regression classification checkpoint

The corrected short-path/LF/SciPy/exact-visual-byte retest completed:
**72 tests, 21 failures, 5 errors, 46 passes**, 884.779 seconds, on87eec970.
Private corrected log SHA256:
`ffadd87dee874c3d3329df0c434cdc10e8d687c4338bb97b9445c2043ab825ff`.
One of those failures was c004 reconstruction, independently fixed above.
Another was ANSUR correspondence: exactly three platform-dependent source
path keys, with no other report differences. Its one serialization expression
now uses `as_posix()`; all five unchanged ANSUR tests passed using actual
short-path source files and the edited builder (path bindings only).
The Windows CI workflow now runs those same five tests without rebindings;
verification of the next published run remains outstanding.

Remaining failing case names (do not claim full-suite green):

- `production_control`: `test_next_action_requires_both_source_bound_diagnostics`,
  `test_wrist_repair_precedes_grip_and_lunge_after_hand_recovery`,
  `test_zero_blockers_cannot_hide_inherited_regressions`.
- `shoulder_ansur_acromion_audit.Audit.test_reproduces`,
  `shoulder_thorax_c003.Identity.test_reproduces`,
  `arm_chain_ansur_audit.ArmChain.test_reproduces`.
- `canonical_lumbar_orientation_sensitivity.LumbarSensitivityTests.test_report_exact_reproduction`,
  `canonical_lumbar_wedge_decomposition.LumbarWedgeTests.test_report_reproduction_and_se_not_sd`.
- `evidence_integrity_audit.Committed.test_live_reverification_matches_committed`,
  `evidence_integrity_audit.Mutations.test_every_status_detected`,
  `execution_orchestration.test_unknown_support_stage_refused`.
- `review_pack_index.ReviewPack.test_reproduces_and_hashes`,
  `rib_spiral_reconstruction.DistalRibTests.test_export_is_reproducible_and_keeps_floating_rib_exceptions`.
- `shoulder_proposal_c001.Identity.test_record_reproduces`,
  `shoulder_proposal_c001.VerticalRelationAudit.test_reproduces`,
  `shoulder_proposal_c002.Identity.test_record_reproduces`.
- `skeleton_audit_and_p001.P001.test_builder_reproduces`,
  `spine_trunk_audits.P003Rejected.test_rebuild_is_deterministic`,
  `verify_original_v1_candidate_status.CandidateStatusTests.test_current_candidate_status_matches_repository_evidence`.

Five error cases remain: execution orchestration's
`test_live_plan_covers_support_and_selects_active_r96_recovery` and
`test_operational_tool_artifacts_are_validated`; production control's
`test_future_candidate_with_verified_sources_is_selected` and
`test_owner_accepted_regression_is_bound_to_exact_candidate_and_values`;
and the whole-body Blender gate private-QA symlink test (Windows privilege1314).
These are diagnostic classifications, not permission to update frozen records,
loosen production approval, enable OS privileges or hide tests.

## Independently retrieved measurement handbook

See `ANSUR_PRIMARY_HANDBOOK_RECHECK_20261010.md` and its JSON companion.
The complete archived primary report was retrieved privately and its identity
and seven relevant pages independently checked against the actual PDF. The
historical October8 owner-supplied record remains untouched. Definition/page
verification is newly available; endpoint offsets and geometry acceptance are
still missing. Wrist height is section6.4.94, not wrist circumference6.4.93.
Use the verified definitions and their distinct palm postures when seeking
new endpoint-to-centre evidence; do not turn definition closure into a length
target, a sourced 15mm offset or canonical promotion.

Latest pre-edit remote-head check also discovered independent BoneHub intake
branch `c0d2faeac78ce34af726e20166b972d9b5574602`. Rib preflight is now
`909c44ffcce743930a5b98880e1d3dbdd2b0d989`. Both were preserved; inspect
their latest reports before duplicating source acquisition.

Current continuation supersedes earlier pending items: targeted retest and
c004 CI are complete, ANSUR Windows CI awaits the next push, remaining failure
classification and independent endpoint/pelvic evidence are still actionable.
The existing hourly continuation automation was updated to follow this master
checkpoint, preserve newer Work branches and avoid repeating completed sweeps.
It stays quiet during active work or non-actionable usage limits. Local
continuation still requires this computer and Codex app to be running; a reset
does not guarantee uninterrupted execution.

## Follow-on primary forearm CT source triage

`FOREARM_CT_ENDPOINT_SOURCE_TRIAGE_20261010.json` records an independently
retrieved five-page primary study, DOI10.17159/2309-8309/2021/v20n3a5.
Its source figures/methods/table were visually reviewed. The reported bone
measurements are not the missing model-specific offsets; the source's
radius-length confidence interval also differs between Results and Table I.
No interval, offset or geometry target was selected. The private PDF remains
outside Git; its exact identity and unresolved discrepancy are in the ledger.

Next execution should first inspect CI for05a3ac371b6e7d54e8e48f15a315f757086916e4
([run38066488527](https://github.com/anyangle1409-code/animation-software/actions/runs/38066488527)),
then classify outstanding reproducibility defects or seek independently
calibrated endpoint correspondences. Avoid incomplete Visible Human elbow
surfaces as target evidence. BoneHub intake advanced to555e2a6c during the
pre-push fetch and is active independent work; preserve it.

Subsequent result: **all three jobs in run38066488527 passed** on05a3ac37,
including actual Ubuntu Blender and all14c004 plus five unchanged historical
ANSUR tests on Windows. The same19tests also passed locally in the clean,
short-path checkout without input rebindings (13.385seconds).
This closes the ANSUR serialization correction only. New source-ledger PDF
identity, page counts and confidence-interval references were checked against
the actual privately retained PDFs. The full regression suite remains red and
canonical readiness remains0READY/9PARTIAL/3BLOCKED.

## Further reproducibility isolation

Arm-chain audit reproduction failed only on five Windows input-path keys.
Its one serialization expression now uses `as_posix()`; all four unchanged
tests pass with exact short-path inputs (path bindings only). Windows CI now
runs these alongside the five endpoint-correspondence tests; the newly
published implementation still requires remote execution verification.
No stored report, proxy definition, numerical result or geometry changed.

The shoulder acromion audit is **not** the same narrow failure: besides path
keys, five output entries differ by0.0001degrees (5.7023/5.7024 repeated,
1.8394/1.8393,30.4773/30.4774,7.4862/7.4861). Optimizer/runtime portability
remains a hypothesis, not a proven root cause. Do not rewrite historical
angles, round less precisely or relax the reproduction test to hide them.
Investigate pinned numerical environments and optimizer convergence first.

All23unchanged endpoint/arm-chain/c004 tests subsequently passed without
path rebindings in the short clean checkout (13.984seconds), and all three
jobs in [CIrun38066778689](https://github.com/anyangle1409-code/animation-software/actions/runs/38066778689)
passed on2d49f7e1f66d6183058372b06286f82fc941fc7d. The arm-chain path fix
is now remotely verified. Source review then expanded to ten handbook pages:
clavicle-point, lateral-neck and trapezius-point definitions are verified
separately, but their placement on the model remains unresolved. The tape-line
construction needs a muscle/neck surface landmark, not a substituted bone axis.

Read-only solver isolation: with NumPy2.3.5/SciPy1.18.1, two complete acromion
builds are exactly identical, including all33optimizer diagnostic entries.
All33optimizations report success; termination status counts are1:3,2:17,
3:7,4:6, and maximum reported first-order optimality is0.027177687332406972.
Sorted-JSON report SHA256 is
`27c771fd13718503c7fb1be5befb99ea73fbebe4ea08e5bba3e762ddef5846c3`.
This rules out observed run-to-run randomness in this environment, not
cross-platform/version drift or numerical accuracy. It does not close the
five historical angle mismatches. Original `least_squares` was wrapped only
to observe return diagnostics; inputs, tolerances and production files were
not changed. Next: reproduce in the original recorded numerical environment
if obtainable, then investigate Jacobian/convergence sensitivity without
rewriting immutable targets or weakening tests.

## BoneHub component follow-on, source-axis Blender and header declaration

Reconciled and preserved Work's PR32/33/34 heads555e2a6c/484aa52b/c765ff24.
PR34 already acquired and audited54surfaces; its52-test CIrun38074463706 passed.
Before publication rechecked PR34: newer247020ac preserved; successful final
CI38075047099 independently observed. All54headers declareLPS and65tests pass.
The eight laptop header checks corroborate this, not a claim of new full audit.
Do not repeat that work. New laptop follow-on measures flagged component bounds,
mathematical area/guarded algebraic-volume centres and overused-edge positions.
Eight private sources match existing pins; actual Blender retains all raw
coordinates/faces and produced24source-axis views, all PNG hashes checked.
Eighteen synthetic tests and two native Blender tests PASS locally. New CI must
still be verified remotely. Reviewer tiny-camera false-success reproduced and
fixed by refusal before output, with no source scaling.

All eight actual STL headers declareSPACE=LPS, supported by official Slicer tag
documentation. This is declared frame evidence, not accepted image registration
or verified units; do not map it to raw NLM CT without the image transform.
See `docs/BONEHUB_PRIVATE_COMPONENT_GEOMETRY_20261010.md` for exact measurements,
limits and next commands. Keep medical bytes and private review outputs outside
Git. No fragments deleted, anatomical acceptance or canonical promotion performed.

New implementationfc6c639d665aff904559fadd24bc755b639c436f subsequently passed
all3jobs in actual CI38075799684, including native source-axis Blender review,
18new tests on Windows/Linux and unchanged23Windows reconstruction tests.
Clean short-path detached checkout:51targeted tests PASS in16.419seconds.
Reviewer rechecked refusal guard and independently ran18synthetic tests, PASS.
Full inherited suite and all anatomical gates remain as recorded, not green.

Next bounded investigation retrieved three complete small segmentation files
(exact upstream LFS pins verified) and only64KBof the418,636,727-byte male CT
image. Image header declares millimetres and a RAS sform compatible after X/Y
sign conversion with label-grid LPS directions/origin. Full image bytes NOT
hash-verified; no pixel registration or STL scale accepted. Label files decode
to537MBor1.075GBdespite compressed sizes near1MB; foot/hand have two layers.
Read `docs/BONEHUB_IMAGE_SEGMENTATION_HEADER_TRIAGE_20261010.md` before implementing
bounded streaming label sampling. Do not eagerly inflate whole medical volumes.

Subsequent bounded sampler reads all three private gzip payloads through CRC and
exact decoded-length verification, retaining only512KBchunks and requested labels.
Eleven synthetic tests PASS; new CI pending. Under an explicitly unaccepted matching
mesh/grid scale assumption, all11small-component nearest-centre samples equal
their named upstream labels. Do not assume these are purely STL export debris.
Main rib mathematical averages can lie in the empty centre of the rib curve,
and must never become bone/joint landmarks. Exact source-grid samples and method
are recorded in the header-triage document; source report/pixels remain private.

Label-stream implementation560a8083 passed all3jobs in actual CI38076420293;
clean short detached checkout62targeted testsPASS (14.586seconds). Full male CT
now privately acquired418,636,727bytes and its complete immutable LFS hash verified.
New bounded pixel sampler checks UINT16header and full gzip CRC/decoded-length,
hash before/after, no pixel writes or HU acceptance. Seven synthetic testsPASS,
new pixel CIpending. Actual21pixel samples verified: tiny named rib fragments
span raw values6..47290 while foot fragments1356..1498. No guessed intensity
offset/threshold or anatomical conclusion. Inspect actual spatial patches and
calibration provenance next; raw source frames still do not establish HGPT binding.

Verified continuation: pixel implementationfed5f46d passed actual CI38076878218
all3jobs, including native Blender; clean detached69targeted testsPASS in14.887s.
Three private source CT/label patches (56,544sampled pixels) visually inspected;
exact source-grid bounds/display method/PNG hashes are in the header-triage ledger.
Foot fragment is near visible bone-like structure; tiny rib labels appear in
background/near a structured horizontal bright artefact, not independently
identified scanner text. No source fragment removed, no label/anatomy accepted.
UINT16 intensity calibration remains unknown. Denver primary page confirms
aligned/rescaled CT but supplies no BoneHub HU conversion; its download endpoint
returned403 to web reader. Next executable action: bounded primary calibration
metadata or transformation-code inspection, followed by source-bound surface
point/grid correspondence. Preserve all immutable sources and frozen candidates.

Executed follow-on raw-vertex/grid diagnostic:256deterministically selected
original float32 vertices for each of8pinned STLs; all2,048have named segment
within27nearest-grid neighbours, nearest matches126..150/256. This is not
spatially uniform/exhaustive, and does not accept registration or anatomy.
Complete source-stream CRC/length checks passed; exact private report hash and
per-source results in header-triage ledger. Frozen upstream demographic metadata
and smoothing0.5mesh conversion README inspected; neither supplies HU conversion.
Next bounded action: independently establish aligned image intensity provenance
or inspect fragment-focused orthogonal source patches, retaining all fragments.

## Calibration provenance recheck, 2026-10-10

The BoneHub dataset card confirms NLM Visible Human CT provenance through the
University of Denver aligned CT DICOM series and states that 3D Slicer converted
those DICOM files to NIfTI. Neither the card nor the accessible Denver landing
page publishes the pixel-rescale formula or output intensity units. Denver's
record labels its CT as aligned/rescaled to cryosections. Web-reader and direct
read-only requests for both the metadata and aligned-CT download returned
HTTP403, so no source bytes were obtained. The full private BoneHub NIfTI remains
hash-verified, but `scl_slope=1`/`scl_inter=0` does not establish HU. Keep stored
UINT16 values explicitly uncalibrated and do not threshold.

The pixel CI is confirmed complete: run38076878218 passed all3jobs, including
the Windows unsigned16 sampler, Linux provenance gate and native Blender render
path. No anatomy or readiness gate changed. Next executable action: obtain an
accessible, hash-pinned aligned DICOM instance/series or its producer conversion
code and reproduce rescaling on exact corresponding voxels; if unavailable,
retain the HU blocker and continue only source-bound orthogonal candidate review.
Keep medical source bytes and review outputs private.

## Laptop Blender boundary-extension output integrity recheck, 2026-10-10

Read-only audit of the existing private output
`work/private-nlm-ct-20261009/blender-boundary-extension-review-retry1-20261010/`.
No source files, scene, or review images were changed. Actual Blender 5.2.1 LTS
reopened `boundary_extension_contact_sheet_labeled.blend` successfully: one
scene, ten display-only CT image planes, ten labels, one limitation caption, no
armature/skeleton, and ten external 512x512 display images. All ten relative
image paths resolve beside the Blend. The scene has no segmentation or
registered source skeleton; this agrees with its private report.

Independent local SHA-256 recheck matched all ten original PNG and GE header
pins in `boundary_extension_contact_sheet_final_handoff_report.json`, all ten
8-bit display PNG hashes, the saved Blend hash, and the final rendered contact
sheet hash. The report correctly records 10 frames, zero anatomical landmarks,
`UNVERIFIED` region/laterality, `segmentation_performed=false`,
`source_skeleton_loaded=false`, and `canonical_promotion_allowed=false`. The
image sheet is expressly arbitrary-layout display only, not scanner/rig
registration or bone identification. No downloaded source or private Blender
output was added to Git.

Next executable evidence action is an offline independent review of the
contiguous source sequences in anatomically oriented planes, followed only by
tentative, source-pinned region/contour notes where visual evidence is clear.
The current ten-frame sheet is not that review: its two separated ranges cannot
establish continuity, 3D boundaries, named bones, or any of the seven pelvic
landmarks. Keep the applicable true-bone identity and 3D segmentation gates
open; do not infer or promote anatomy from this QA pass.

## Independent PR review and wrist/foot region follow-on, 2026-10-10

Fetched the working branch and related live refs. At review start, it was clean
at `c33c5ae453ef71522f2fa10b74cbc1cbfcfdb490`; no Claude/Work or canonical
changes were applied. Reviewed the actual changed scripts, manifests,
tests and workflows for PRs #35–37. All remain isolated drafts, mergeable and
without submitted reviews or inline threads. Current head CI is green:

- PR #35 `597562dc55b573721b6eccc78446cc6907634e31`: all three check runs
  succeeded. Its rights/cohort index is explicitly metadata-only and fail-closed;
  TotalSegmentator/MedOtter share a donor cohort, restricted licenses remain
  excluded, and no images, models or anatomical targets are promoted.
- PR #36 `8288128f00c648a6c8e7f30646be98091f117401`: both check runs succeeded.
  It records the Selthofer source table and corrects the interpretation of the
  Turkish `CL=M+B` value without mutating the historic file or selecting a new
  sternum length target. The Thai study records local facet-centre intervals,
  but the cohort's training stature does not cover HGPT's 182cm target.
- PR #37 `4879b10ebf0256e7bd8e8de27c795e7335d16b87`: both check runs succeeded.
  Its endpoint compatibility gate rejects incompatible cross-study/model
  comparisons and demonstrates that three local distances do not uniquely
  determine the 3D sternocostal chain. No critical implementation blocker was
  found in these focused metadata/contract changes. This is a code/evidence
  review, not a medical-anatomy or licensing approval; no GitHub review vote or
  merge was submitted.

New independent Work branches were preserved. PR #38's wrist/foot source
proximity work advanced from a failed first real-source CI attempt at
`7b46fb89576cf53bf66aa7b7186393d76cdb301d` to verified head
`d0f275a847208648480bbc924298a11882a9d3c5`; both jobs passed in run
[38086284050](https://github.com/anyangle1409-code/animation-software/actions/runs/38086284050).
It parses 12 pinned meshes for eight bilateral scaphoid/lunate and tarsal pair
proxies. The recorded closest valid-face-vertex bounds are raw source-coordinate
values, with source units, CT registration, triangle-surface gaps, joint centres
and contact all still unverified. They are not model measurements or accepted
joint contacts. Its stacked PR #39 expanded this to 30 source bones and 44
bilateral pair candidates. Latest head
`22074e3c66be50f5e5e639ea02ff06740164f38a` passed both jobs in runs
[38086883381](https://github.com/anyangle1409-code/animation-software/actions/runs/38086883381)
and [38086879494](https://github.com/anyangle1409-code/animation-software/actions/runs/38086879494):
36/36 combined geometry tests, 30/30 pinned LPS STL hashes, 44/44 candidate
pair checks, and 8/8 previously measured PR #38 bounds reproduced to their
recorded three-decimal precision. For example, conditional lunate–hamate
valid-face-vertex upper bounds are 3.443/4.168 and AABB lower bounds
1.237/0.174 for left/right in unknown native source numbers; these are not
millimetres, not CT-to-STL registration, not triangle distances and not accepted
contacts. PR #39 remains a draft; the source STL set is one donor, and readiness
does not change.

Next executable action is a bounded source-pinned pelvic review in anatomical
planes, retaining the two scanner-defined groups and their boundary. Record
candidate image observations only where support is clear; obtain independent
second review before landmarks, segmentation, registration or skeleton targets
can advance. The short separate verification checkout remains detached at
`fed5f46d965d55e1726c14e4a3e98a0a9f8e233a`; a local PR review checkout attempt
was interrupted by Windows file access and was not used as test evidence. No
patient/source bytes or candidate outputs were added to Git.
Regional readiness remains `0 READY / 9 PARTIAL / 3 BLOCKED`; no canonical
geometry, landmarks or anatomical contacts were promoted.

## Read-only full-pelvis Blender scene integrity check, 2026-10-10

Reopened the existing private
`work/private-nlm-ct-20261009/full-pelvis-1734-1947/pelvic-ct-full-series-component-audit-v2.blend`
with laptop Blender 5.2.1 LTS. It loads one scene, 13 objects (12 meshes and a
camera), zero armatures, two external image datablocks, no packed image bytes,
and all external image paths resolve. Mesh objects comprise two thresholded
stored-scalar occupancy groups and ten separately named CT observation
candidates (iliac blades, sacrum, femoral heads, acetabula and pubic region).
This is not accepted bone segmentation, has no source skeleton overlay, and
keeps group separation. The saved report describes two groups covering 37 and
35 slices, ten candidate observations and zero verified segmentation or
canonical promotion. The old report's threshold/calibration fields were not
rewritten; its source-scalar threshold is not a validated bone classifier.

Independent SHA-256 checks matched the saved Blend (`abbbc0a96633538dd5f082105003e731a846c2400cb0fd48fec509b731aaf486`) and render (`6e69c9039eee0d8c60aff16f6644413bf1babc88cf36ad3731ec168583aeb374`) to that report. Private report SHA-256 is `edd111277d4c81eaa8fa796d947523e3d423e1a0493f88f97c78e25ddf09777e`. No Blend, source pixels, headers, mesh, or report were modified or added to Git. This revalidates saved artifact integrity only; it is not a fresh anatomical reading.

Current safe anatomy action remains source-pinned sequential CT review across
the two acquisition groups, with candidate observations only and second review
before any landmark or segmentation advances. Keep the source skeleton
unchanged and all private artifacts outside Git.

## Verified source-ordered pelvic CT viewer, 2026-10-10 evening

Draft [PR #44](https://github.com/anyangle1409-code/animation-software/pull/44)
is pushed at `abaacc61d4ee0a4612598fda1f5b9f0bdbdefad2` on
`codex/pelvic-ct-blender-sequence-review-20261010`, stacked on the independent
CT identification branch. Its private Blender 5.2.1 timeline holds all 82
source-pinned PNG/header pairs, preserving the scanner-defined 43/39 groups
and their boundary. The saved scene reopens with 82 external/unpacked display
images and exactly the expected visible slice at frames 1, 43, 44 and 82.
Fixed-window display copies, the scene, previews and report remain in
`work/private-nlm-ct-20261009/sequential-viewer-20261010/`, outside Git.

Nine native viewer tests pass on both laptop Blender 5.2.1 and hosted Blender
4.0.2. They verify source order, group markers, scale, handedness, corner/UV
orientation, camera geometry, frame visibility, identity checks and external
image handling using synthetic pixels. Native CI first exposed the older
Blender material's empty node tree; the regression now passes after enabling
shader nodes only when required. All five jobs passed in
[CI run 38091450091](https://github.com/anyangle1409-code/animation-software/actions/runs/38091450091).
This completes viewer verification only. Regional readiness stays
`0 READY / 9 PARTIAL / 3 BLOCKED`.

Next executable anatomy action: reuse the saved viewer for source-pinned
candidate notes, consulting the original full-resolution PNG and scanner
header for every observation. Preserve acquisition-group membership and
uncertainty. Independent second review remains required before bone identity,
seven pelvic landmarks, segmentation, scanner-to-HGPT registration or
canonical geometry can advance. The source skeleton remains the geometry
authority. Do not rebuild the viewer, reacquire/calibrate these source bytes,
or repeat completed sweeps. The existing BoneHub intensity-calibration and
regional evidence blockers remain recorded separately.

## Frozen c001/c002 Windows reproduction checkpoint, 2026-10-10 late evening

Draft [PR #45](https://github.com/anyangle1409-code/animation-software/pull/45)
on `codex/windows-c001-source-paths-20261010` is pushed at
`66bba1b3258c45acb5795ce1a310dde595f97241`, stacked on this master branch.
The clean short checkout `C:/Users/Mark/Documents/Codex/hgpt-source-blender-audit`
now holds that dedicated branch, **not the earlier detached checkpoint**.
Inspect its current state before any reuse; preserve the published work.

Three previously failing, unchanged record comparisons were independently
reproduced before fixing five path serialization expressions. Full differences
were exclusively Windows separators in source paths/hash keys. All **31
unchanged c001/c002 tests pass** in laptop Python (2.424 seconds) and actual
Blender 5.2.1 (2.797 seconds), including source/review hashes, unchanged internal
geometry, candidate scope, unaccepted status and retained closure defects.
No frozen records, numerical expressions or anatomy were altered.

Initial CI run `38092898558` passed Windows and source safety. The newly added
Ubuntu Blender candidate step could not import NumPy; existing native render
and source-triangle checks passed. The latest workflow explicitly installs
`python3-numpy` and runs all 31 tests on both platforms. Latest hosted CI is
pending at this checkpoint, and the inherited full suite is still red.

Next regression action: inspect exact-head PR #45 CI before claiming hosted
success, then reproduce c003 or shoulder ANSUR acromion report comparisons and
inspect every difference before further path-only corrections. See
`docs/WINDOWS_C001_PATH_REPRODUCTION_20261010.md` on PR #45. Do not rerun the
expensive full suite or completed motion sweeps. Source-bound anatomical
review and independent evidence remain separate gates; regional readiness
stays `0 READY / 9 PARTIAL / 3 BLOCKED` with no canonical promotion.

### PR #45 hosted verification completed

At exact source head `66bba1b3258c45acb5795ce1a310dde595f97241`, all three jobs
passed in [CI run 38093010487](https://github.com/anyangle1409-code/animation-software/actions/runs/38093010487).
The explicit NumPy provision fixes the initial native runner import failure.
All 31 unchanged c001/c002 tests pass in actual Ubuntu Blender 4.0.2
(0.329 seconds), and the Windows Python candidate step passes too. This closes
hosted verification for these path-only corrections, not the inherited full
suite or anatomical readiness. PR #45 remains a draft, not merged or approved.

The next read-only c003 investigation is currently running in the short
checkout: session `41234` (unchanged test module) and session `26974` (complete
report differences), local PIDs `1868`/`6180` at this checkpoint. The old c003
solver reconstructs nested rib/cartilage optimization and is slower than the
c001/c002 comparisons. Collect those existing results before starting another
reconstruction; inspect current processes because IDs are temporary. No c003
code, candidate files or geometry have been edited. If a numerical difference
appears, retain it as an unresolved finding rather than treating it as a path
serialization fix. Source-bound anatomical review remains the next separate
evidence gate.

### c003 environment diagnosis and one corrected run

Sessions `41234` and `26974` completed, superseding their running state above.
The unchanged c003 test module ran **16 tests: 15 pass, one error** in
130.610 seconds. Reconstruction stopped at `scipy.optimize` import, before a
complete record comparison. The separate difference diagnostic hit the same
missing dependency; neither supplies evidence that c003 differences are
exclusively paths. Do not edit c003 serialization on that assumption.

SciPy **1.18.1** and its NumPy **2.5.4** dependency were installed using binary
wheels into private `work/private-source-skeleton-20261010/dependencies-python312/`,
outside Git. Both versions and import locations were checked. Shared Python,
Blender and source bytes were not changed. One corrected unchanged c003 module
run is active in session **57042**, with that private directory explicitly
prepended and full comparison mismatch output enabled. A preliminary command
imported SciPy before prepending the directory and immediately errored; it ran
no tests and is not verification evidence. Collect the corrected session
before restarting any solver. Retain any numerical mismatch as unresolved;
do not change tolerances, frozen records or anatomical approval to hide it.

### Completed c003/acromion diagnosis — 11 October

Corrected session `57042` completed: **16 tests, 15 pass/one failure** in
159.474 seconds. There are 139 comparison differences, not exclusively paths:
solver coordinates and collision-pair ordering also differ. Related acromion
audit: **9 tests, eight pass/one failure** in 1.979 seconds, with one path-key
set and five rounded numerical differences. Exact numerical cause remains
unisolated. No solver, tests, candidate data or tolerance was changed. See
`docs/C003_ACROMION_REPRODUCTION_DIAGNOSIS_20261011.md` for frozen hashes and
representative mismatches. Do not rerun completed optimization or poll old
sessions. The master checkpoint's previous CI run `38093962974` passed all
three jobs, which is distinct from the intentionally retained local failures.

Next safe independent action: reuse the saved source-ordered pelvic CT viewer
for candidate image review within its two scanner groups, consulting original
PNG/header identities. Preserve the source skeleton and require independent
second review before any anatomical acceptance or geometry promotion.

### Actual Blender CT group-end candidate review — 11 October

Reused the existing 82-frame private scene without saving or changing it.
Blender 5.2.1, limited to two render threads, rendered frames 43 and 82 into
new private previews. Exactly one expected source plane was visible in each:
`cvm1842f` (group1, scanner S=-450mm) and `cvm1957f` (group2, S=-565mm).
Original PNG/header hashes for both sources match the viewer report; the
saved Blend hash remains `8775f92d...d46f7`. Both original native16 PNGs and
fixed-window Blender previews were inspected. Native16 direct previews are
dark; fixed-window shape observations are not threshold segmentation.

Metadata-only `docs/PELVIC_CT_TERMINAL_CANDIDATE_OBSERVATIONS_20261011.json`
records exact source/header/render hashes and cautious visual shape notes.
No medical source bytes or rendered pixels entered Git. No bone identity,
landmark, complete anatomical coverage or registration was accepted. The
source skeleton remains unchanged. Next action: trace the observed paired
structures through adjacent source-pinned slices in each group separately;
compare the group boundary without flattening acquisition geometry, and
require independent second review before anatomical acceptance.

### Adjacent CT candidate tracing checkpoint

The metadata-only observation ledger now includes seven inspected windowed
frames: **42/43**, **44/45**, and **80/81/82**, preserving source groups.
New private Blender previews at42/45/80/81 each render exactly one expected
source plane; the existing frame44 preview was reused. Original PNG/header
hashes for all five added sources match the pinned viewer report, all render
hashes are recorded, and the saved Blend hash remains unchanged. Factory
startup and two render threads were used, without modifying user preferences.

Candidate outlined structures persist qualitatively within each short sequence.
The cross-group43/44 resemblance is **not accepted registration**. Scanner-S
gaps across42/43/44/45 are3/1/3mm, so timeline order must not imply a uniform
3mm volume grid. No bone identity, landmark coordinates, segmentation, source
skeleton geometry or anatomical readiness was promoted.

Next executable anatomy action: trace intermediate group2 frames50/55/60/65/70/75,
using existing pinned source imagery and reusing private previews if present.
Retain explicit candidate-only observations and obtain independent second
review before accepting anatomy. Do not repeat completed c003 optimization,
source downloads/calibration or movement sweeps.

### Intermediate group2 candidate review, 13 source-pinned views total

Actual private Blender views50/55/60/65/70/75 were rendered and inspected;
each exposes exactly its expected source plane. Six original PNG/header
hash pairs match the saved viewer report and the saved Blend remains unchanged.
The ledger now has13 unique source-pinned observations. Rounded structures
within surrounding outlines at50/55 and outward-extending lateral structures
at60 provide **candidate** hip-region review cues. Distinct medial outlined
profiles remain at65/70/75 and are not grouped into an accepted segmentation.
This sparse15mm sampling does not prove continuity, bone identity, anatomical
coverage, joint contact or any landmark centre. All acceptance gates remain
false; every render and source byte stays private.

Next action: densely inspect group2 frames46–62, reusing existing50/55/60
previews and rendering missing frames only. This bounds the rounded candidate
region for independent review without repeated source acquisition, scene
rebuilds or numerical optimization. The preceding seven-view checkpoint
`ccd3d8ed7aa271a6485ad963b07ed8c42e2382c4` passed all three CI jobs in run
`38094791988`; that tooling verification is not anatomy approval.
## Dense group2 candidate review checkpoint — 11 October 2026

Completed the requested windowed review of every source-pinned frame46–62
within acquisition group2 (17 frames, scanner S=-457 through -505mm at3mm
steps). Reused50/55/60; Blender5.2.1 rendered only14 missing previews, exit0,
without saving or changing the private source scene. The paired rounded
internal structures can be followed into outward-extending lateral profiles;
separate anterior and posterior-medial outlines remain distinct candidates.
No bone identities, landmark centres, segmentation, contact, registration or
anatomical coverage are accepted. Regional readiness remains0READY/9PARTIAL/
3BLOCKED and every canonical-promotion gate remains false.

Source/preview pins and independent-review request are recorded in
`docs/PELVIC_CT_DENSE_GROUP2_CANDIDATE_REVIEW_20261011.json`.
Together with the preceding ledger,27 unique source frames have windowed
candidate observations; this is not27 independently accepted anatomical slices.
The preceding master checkpoint4477eb820300b8e0a9f46bcdbb97e69ff6d2c6a5
passed all three CI jobs in run38095073757. C003 numerical mismatch remains
diagnosed, not fixed; do not repeat its completed solver or old test sessions.

Next executable action: inspect group2 frames63–79, reusing65/70/75 and
rendering only missing views; trace lateral and medial candidate profiles
separately. Then inspect unreviewed group1 frames for candidate pelvic
landmark coverage. Require independent source-image review before accepting
identities or coordinates. Private CT bytes and Blender outputs remain outside
Git; no source skeleton or frozen candidate was modified.

### Lower group2 continuation

Frames63–79 reviewed next, reusing65/70/75 and rendering14 missing previews
with Blender5.2.1 (exit0). Original PNG/header pins were reverified, including
the extension source at79. Medial profiles taper toward79 while lateral rings
persist; no bone endpoint or accepted3D connectivity is inferred. The lower
ledger is `docs/PELVIC_CT_LOWER_GROUP2_CANDIDATE_REVIEW_20261011.json`.
All39 group2 source frames now have qualitative windowed candidate review;
41 unique frames across both groups are reviewed. Every acceptance gate
remains false. Next: inspect unreviewed group1 frames1–41 for candidate
pelvic landmark coverage; reuse existing outputs and preserve group boundaries.

## Upper group1 candidate review completed — 11 October 2026

Reviewed all41 previously unrecorded selected group1 frames1–41, reusing
frame1 and rendering40 missing previews in actual Blender5.2.1, exit0.
Original PNG/header hashes and private render hashes are recorded in
`docs/PELVIC_CT_UPPER_GROUP1_CANDIDATE_REVIEW_20261011.json`.
Paired elongated lateral profiles become visible around6 and persist through
the group; the central transition at17–22 is a candidate interval for
independent lumbosacral/endplate review, NOT an accepted S1 level or centre.
External limb contours remain distinct from torso candidates.

All82 selected slices now have first-pass qualitative windowed observations
in four source-pinned ledgers, respecting43/39 acquisition groups. This is
NOT accepted anatomical coverage: selected slices are3mm apart within each
group; missing native intervening slices and inter-group registration still
require independent source verification. No seven-landmark coordinates,
bone masks, skeletal geometry changes or canonical promotion were produced.
Readiness stays0READY/9PARTIAL/3BLOCKED. The preceding checkpoint60e65b1e
passed all three CI jobs in run38095646973. Old c003 session-poll instructions
in the machine checkpoint are now superseded by completed diagnosis.

Next: inspect existing acquisition/coverage manifests and intake scripts,
enumerate missing native source IDs between the selected3mm slices, and
acquire only absent image/header pairs privately with URL/hash/scanner
verification. Reuse verified source bytes and82-frame review; do not rerender
or reacquire completed work. Independent review remains mandatory before
identity, segmentation, landmark, registration or canonical acceptance.

### Source-spacing ruling supersedes the intervening-slice acquisition step

The existing original-CT window code documents native3mm acquisitions.
Fresh read-only parsing of all82 original pinned headers with the existing
privacy allowlist verified43/39 counts,3mm thickness,3mm nominal spacing and
3mm measured within-group gaps. Group1 spans scanner S=-324 to-450mm;
group2 spans-451 to-565mm; their centre gap is1mm, not a uniform merged grid.
Ruling: do not infer missing1mm images from filename increments or attempt
invented downloads. The preceding next-action wording was provisional;
source headers govern spacing. This verifies sampling coherence, NOT
submillimetre anatomy, complete bone coverage or anatomical readiness.

Next executable action: independently compare pinned candidate feature
intervals with qualified primary CT anatomy references and reconcile the
existing calibrated-surface/hip-bridge evidence without repeating its work.
If finer articular sampling is needed, acquire genuinely separate verified
finer-resolution evidence. Keep bone identity, seven landmarks, surfaces,
registration and canonical-promotion gates unaccepted.

## Landmark-method/source reconciliation checkpoint

Primary method definitions and the preserved calibrated/hip-bridge heads
are reconciled in `docs/PELVIC_CT_LANDMARK_EVIDENCE_RECONCILIATION_20261011.md`.
The bridge plane cvm1873f matches viewer frame54, group2, S=-481mm and exact
PNG/header pins. Intensity connectivity remains rejection evidence, never
accepted contact or segmentation. Seven true landmarks remain0/7 accepted.
Fresh unchanged feature-contract24tests and APP-frame23tests all passed
(0.048s/0.163s); those synthetic/frozen guard tests do not validate anatomy.
Master66fa1b79 passed all3CI jobs in run38095971380.

Next: reuse the existing hip-bridge private three-slice review-plate tool
for original cvm1870f/1873f/1876f and four exact candidate pixels, preserving
branch isolation. Inspect original marker locations without bright-pixel
snapping. Full independent anatomical interpretation still required.

## Private exact-pixel hip review plate prepared

Executed existing hip-bridge tool from commit-pinned private source archive
678c8c03, preserving every checkout. Four unchanged tests PASS in1.164s;
actual CLI exit0. Original53/54/55 planes are shown in two windows, with
four unchanged hypothesis pixels marked twice. Metadata-only checkpoint:
`docs/PELVIC_CT_PRIVATE_HIP_PLATE_CHECKPOINT_20261011.json`.

Six embedded windows and eight marker circles verified structurally, with
correct source pixel positions and source HU values291/305/438/510.
Saved SVG byte SHA0b9fc8336de3a1e9216cd5168d8dc7c52c0215b8aa2af9072599b2e3055b9568
differs from CLI's80cfbaf... because Windows converts the final LF to CRLF;
normalized text reproduces the CLI hash exactly. Source images/headers and
existing tool code were not changed. Keep both hashes; do not overwrite output.

Visual inspection NOT completed: browser runtime import failed for cached
browser-service.mjs26.930.61225; optional local SVG rasterizers absent.
No dependency installs, app settings or power settings changed. Prepared
private files remain outside Git. Masterf24d9dda passed all3CI checks in
run38096184421. No anatomy, segmentation, landmark or canonical gate advanced.

Next: reuse the plate; do not regenerate it. Use available native Blender
image/marker display or a repaired browser runtime for exact-pixel visual
review on53–55, retaining qualified independent reviewer acceptance gates.

## Native Blender hip-marker display reviewed

The browser visual blocker was bypassed by a private Blender5.2.1 display,
not by changing browser/app settings. Six unchanged embedded windows and
eight original circle centres were displayed with external/unpacked PNGs.
Private output: `C:/Users/Mark/Documents/Codex/hgpt-private-hip-plate-678c8c03/outputs/native_plate.blend`
and `native_plate.png`; no medical or Blender bytes entered Git.
PNG SHA2568067ea391d4b07c188e6210c6a4bbb32babf3d6c690177cf5be8bd94e5764de8.
Native render81.297s with2CPUthreads. Missing-artifact check RED, then one
display-contract test PASS in0.625s: dimensions, centres and independent
hand-derived coloured raster-ring positions. Initial short-hex SVG colour
failure corrected privately; source/tool branches remained unchanged.
Crosshairs, borders, CSS and top-level SVG captions omitted; this is NOT a
full-fidelity SVG renderer or validated pixel-to-scanner coordinate model.

Actual rendered image viewed: markers1/2 are within round bilateral internal
profiles;3/4 overlap their margins in both windows. Distinct socket-only
identity is NOT established. Adjacent slices retain round/surrounding angular
profiles, but no head, socket, articular surface or contact accepted.
No brighter-pixel snapping, classifier, segmentation or registration added.
Seven landmarks remain0/7 accepted. Previous master44e2a90 passed all3CI
checks in run38096617870; full historical regression remains NOT green.

Next executable action: do not rerender this completed display. Reconcile
the socket-hypothesis overlap with source-bound3D profile/mask evidence and
qualified independent review before choosing segmentation seeds. If that
gate is unavailable, move to independent regional source diagnostics;
never manufacture accepted landmarks from the four HU-linked pixels.

## Foot-fragment orthogonal source review checkpoint

Completed nine small X/Y,X/Z,Y/Z source-grid patches for existing calcaneus,
intermediate-cuneiform and talus diagnostic centres.5625CT/label queries in
one bounded stream invocation,24.438s; complete CRC/decoded-length checks
pass. Fresh unchanged sampler tests:7PASS+11PASS. Contact sheet actually viewed.
All centres match upstream named labels; no independent anatomy acceptance.
Stored window0..2000 is NOT HU; equal index display is NOT metric aspect.
No source fragments removed or anatomical gates advanced. Exact private
output pins/counts and limitations are in
`docs/BONEHUB_FOOT_ORTHOGONAL_CANDIDATES_20261011.md`.
Master4e564028 all3CI checks PASS, run38097339835.

Next: do not repeat completed foot views or pelvic threshold computations.
Review preserved tiny rib candidates467/111/1585 and438/116/1586 in bounded
orthogonal source-index patches, keeping raw UINT16 units and all fragments.

## Rib4-fragment orthogonal source review checkpoint

Reviewed six new bounded source-index planes around the two preserved tiny
Rib4left component centres.3750queries,17.781s; full image/label stream CRC
and decoded lengths checked. Tiny named labels lie in dark background near
a thin structured bright feature; no convincing bone profile established.
Do not identify the artefact as scanner text, delete fragments or claim
segmentation validity/invalidity. Exact private pins, counts and limits:
`docs/BONEHUB_RIB_ORTHOGONAL_CANDIDATES_20261011.md`.

Next: remaining pinned rib1left/rib3left and hamate-right component orthogonal
views; hand layer1 required. Do not repeat completed foot or Rib4 work.

## Component first-review coverage complete, not anatomical acceptance

All11previously flagged tiny components have33orthogonal first-review planes.
Hamate-right adds3main-shell control planes on layer1; it is NOT a tiny
fragment. The remaining18rib/3hamate planes were actually viewed; original
stream integrity passed,18unchanged sampler tests PASS. Exact source/output
pins and findings: `docs/BONEHUB_COMPONENT_ORTHOGONAL_COMPLETION_20261011.md`.
All fragments retained; no bone identity, registration, HU or contact accepted.
Mastera5ec99eb passed all3CI checks in run38097804597. Full suite NOT green.

Next: no repeated fragment displays. Investigate primary metadata for a
genuinely independent finer-resolution contiguous pelvic CT candidate,
verifying licensing/access, native spacing, source identity and headers before
private acquisition. A new subject is evidence only, never replacement HGPT
geometry. Qualified independent review remains mandatory for anatomy acceptance.
