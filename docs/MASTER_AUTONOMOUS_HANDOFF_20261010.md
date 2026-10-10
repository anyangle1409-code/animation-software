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
That new CI step awaits execution on the next published commit.
