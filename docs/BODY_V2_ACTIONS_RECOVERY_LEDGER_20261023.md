# Body v2 isolated Actions recovery — execution ledger

Scope: execute the owner's 23 October recovery request from Claude's existing reconstruction scripts. No repeated muscle research.
Isolated branch: `work/body-v2-actions-recovery-20261023`.
Source branch stays at its independently owned HEAD; no merge, deployment or production asset replacement is authorized here.

## Pinned inputs

- Recovery sources: `9fb56a2763cda3036421c075013277bd5dee262e`.
- R57 read-only source checkout: `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`.
- PR124 muscle checkout: `7c820d68de69dcdef7d567e836302123df953446`.
- R41 SHA256: `4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e`.
- Python 3.13 / bpy 5.2.0 selected explicitly. Actual wheel/dependency versions are recorded by each run.

## Completed and verified locally

- Handover and blend-source docs read; PR124 handoff, exercise contract and screenshot findings reconciled.
- Isolated local worktree and remote branch created. Claude's branch not edited.
- First workflow committed at `ca444ce7fd749d607e698e1d70922212567e04a2`.
- First cloud run: https://github.com/anyangle1409-code/animation-software/actions/runs/39916468327 .
  GitHub job API confirms Blender/dependency installation passed and reconstruction started. Models/results still pending at this ledger checkpoint.
- Archived evidence audit: 18 PASS, 0 FAIL. This is archive consistency, not reconstruction acceptance.
- PR124 Python suite: 38 tests PASS; visual-QA metadata PASS, native validation correctly NOT_RUN.
- Regression tests first reproduced verifier exit-status failure and invalid multiline JSON manifest; fixes pass.
- New completeness/quality summary rejects empty results, missing frames/metrics and existing deformation failures.
- New artifact finalizer and muscle-preparation gates tested. No invented anatomical bindings.
- Python compilation, bash syntax and parsed workflow-command syntax checked.
- Existing app suite: 887 PASS, 1 skipped across 74 files; TypeScript typecheck PASS.
- Independent review caught v14 report mismatch exit propagation and swallowed suite statuses; both reproduced and fixed with regressions.

## Cloud work configured; not complete until actual evidence exists

1. Reconstruct W8, v14 and separate R120; retain partial files on failures.
2. Compare archived W8 offsets/reports/rig edits and v14 report; run read-only native structural verification.
3. Render front, back, side and three-quarter directly in Blender. Cloud samples/skin resolution are lower than archive for compute; this is recorded, not pixel-identical evidence.
4. Independently inventory and run all 13 unchanged R57 movement paths at all nine frames on R41, W8, v14 and R120.
5. Run application tests/type checks and pinned Python and Blender test suites; retain logs and individual exit codes. Legacy tests are identified as legacy, not recovered-model acceptance.
6. Prepare only a byte-identical, unapproved muscle staging copy when W8/v14 archive/structure gates pass; preserve IDs and compile all curl/press/squat phases at fixed pose progress with independent activation.
7. Aggregate hashes, missing checks, quality failures and artifact locations. Update recovery handover only on this isolated branch.
8. Prepare a draft prerelease only after reconstruction gates pass. It is explicitly unapproved and does not promote production assets.

## Rulings and limits

- Ruling: use explicit bpy 5.2.0 with Python 3.13, as the source reconstruction environment was the 5.2 wheel; do not silently substitute a Blender major/minor. Exact original save patch remains unknown. Cost if different: content comparisons may expose a version-related discrepancy.
- Ruling: native movement execution and deformation quality are separate statuses. Zero intersection/collapse/stretch is reported separately; completing a diagnostic suite cannot approve anatomy. Raw counts across changed topologies are not like-for-like improvement evidence.
- Ruling: run movements independently after transient setup, preserving original benchmark paths/metrics and source bytes. One failing path must not suppress other paths. Runtime setup does not save the source.
- Ruling: allow later independent reconstruction/check/render tasks to run after nonfatal v14/R120 or verification failures; keep a nonzero aggregate exit status and preserve every discrepancy.
- Ruling: independent review found the saved remesh vertex-count declaration is stale. Native benchmark setup may update that declaration in memory only after the exact source hash and measured vertex count match its passing native verification report. The production guard and saved .blend are unchanged. Cost if wrong: native setup fails and is recorded, never an anatomy pass.
- No R52/R57 unsaved increment or screenshot provenance is invented. The exact original W8 bytes remain unavailable.
- Historical PR107/113 and R54/R55/R57 failures stay failed. R52/R57 sparse-array native validators depend on their original topology/response inputs and cannot be silently re-labelled as validated on remeshed W8/v14; the full native benchmark paths are reused explicitly.
- Anatomical side and reviewed attachment coordinates remain gates. A semantic muscle registry or staging copy is not a muscle-rigged model.
- PT_MODEL_VERSION remains 1.0. Existing source models, production assets and validated skeletal data are unchanged.

## Remaining / blocked

Actual reconstruction hashes, archive discrepancy results, native movement results, renders, native muscle inventory and accessible artifact/release locations await the cloud jobs. No reconstruction or anatomical success is claimed at this checkpoint.
Independent visual/anatomical review and actual landmark/tissue authoring remain after source recovery.

Independent review: three Important findings (remesh setup, test-status propagation, v14 mismatch propagation) addressed; 13 guard tests pass. Minor path wording corrected. Actual native execution remains pending.

## Additional executed legacy suite

Pinned R57 `python -m unittest discover -s scripts/tests -v`: 228 tests executed, 41 environment errors.
All error records are absent historical fixture environment variables (including HGPT_CONTOUR_NPZ,
HGPT_R41_NATIVE_AREA, HGPT_STRAIN_CANDIDATE and HGPT_R42–R52 response/solution/report paths).
These historical experiments cannot be certified by substituting reconstructed W8 arrays with a different topology.
Cloud logs retain each named error; no legacy suite pass is claimed. Independent recovery/native checks continue.

Ruling: the expanded run may reuse exact .blend bytes from the first cloud run if all three outputs exist,
then repeat archive/structural verification with the corrected tools. Original build provenance is preserved.
This avoids rebuilding completed outputs solely because validation coverage improved. Force fresh reconstruction
with the workflow_dispatch reuse_initial=false input if script reconstruction changes are being investigated.
