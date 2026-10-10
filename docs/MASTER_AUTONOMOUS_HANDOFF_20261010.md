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
