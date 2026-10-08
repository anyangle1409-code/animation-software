# Independent review of Claude's recent skeleton work

Reviewed live branch `codex/whole-body-biomechanics-audit-20261007` at `6570e750fdf0b6fbd899b3ab594ba1a84bd248e4`: 21 newer commits after the checkpoint-plan commit `c956b25c`. All are preserved. This review adds evidence and recommendations; it does not change their implementation or anatomical targets.

## Results accepted within their scope

- CP2 now has a whole-body structural preflight and a readiness ledger covering all 206 bones. It independently detects a003's 22 zero centre-line disc gaps. Coverage is bookkeeping, not anatomical acceptance.
- Claude's CP3 rehearsals exercised the empty-scene builder with a003 data and a mirrored copy. The roll-reference fallback and quaternion marker storage address concrete construction weaknesses. The committed run-002 reports record small round-trip errors. This was a builder rehearsal, not a new canonical skeleton.
- The direct ANSUR forearm report independently reproduces from the committed dataset; the limb proposal also reproduces. Source endpoint and stature caveats remain essential.
- PMCID grouping, talus partial-measure exclusion, C2 dispersion quarantine, partial-ulna endpoint recording and mandible quarantine improve the evidence register. These are conservative corrections, not new numerical targets.
- BodyParts3D is explicitly a grade-D single-specimen layout comparison. It can illustrate spatial relationships and expose schematic representations; it cannot independently establish population corridors or selected anatomy.
- The 1.82 m male skeleton-first owner policy is recorded. Confirmed anatomy must not change to accommodate the old mesh.
- Claude withdrew the de-Leva-only thigh-shortness claim. ANSUR and the alternative methods conflict; a003 femur shortening/lengthening is not established. The later hyoid review also correctly replaces an assumed mandatory horn bend with a landmark-definition dependency.

## Findings requiring action before checkpoint acceptance

| Finding | Independent evidence | Required next action |
|---|---|---|
| **CONFIRMED: CP2 crashes on a zero-length vertebra.** | Collapse C3 head/tail: `ZeroDivisionError` in centre-gap projection. The existing zero-length test only mutates the lunate. | Report the degenerate participant as invalid and skip dependent calculations; add vertebral mutations. |
| **CONFIRMED: parent-relation vocabulary is unchecked for non-root, non-articular entries.** | Replace radius-left relation with `{"type":"banana"}`: parent check still returns PASS. | Validate approved relation types and each type's required semantics, preserving legitimate carrier relations. |
| **CONFIRMED: supplied disc surfaces are not bound to candidate geometry.** | Give a synthetically gapped a003 23 tiny positive plane footprints at X/Y = 100 metres: clearance PASS and overall `STRUCTURE_PASS_EVIDENCE_REVIEW_STILL_REQUIRED`. | Bind endplates to their vertebral participants, coordinate transforms and actual envelopes; verify footprint coverage and surface approximation limits before interpreting clearance as anatomical. |
| **REOPENED: scapular height overclaim reappears.** | Claude's review calls a003's 211.7 mm GH-to-inferior-angle distance "shorter than full height" and compares it with 148.2 mm height. An oblique 3D distance has no such guaranteed inequality. | Preserve the earlier method-conflict correction in `canonical_shoulder_girdle_audit_v1.json`. Compare matched landmarks and definitions; a single specimen's ~145 mm proxy span cannot establish exact population shortening. Clavicle rebuild remains independently justified. |
| **PROVISIONAL: specimen spine clearance is a plane-fit diagnostic.** | Axial script samples inside 60% of the disc footprint, fits planes, and tests an axis-aligned ellipse. Fit residuals are recorded but not incorporated into the clearance verdict. | Do not claim full actual endplate clearance. Establish actual footprint coverage, curvature and conservative error bounds or direct surface-contact checks. Positive fitted-plane gaps alone are insufficient. |
| **UNVERIFIED: three de Leva values are recalled.** | Proposal explicitly labels shank, upper-arm and forearm values `UNVERIFIED_RECALL`; its forearm narrative nevertheless cites all methods agreeing. | Reread the primary table and mapping before treating these as independent corroboration. Retain endpoint-offset sensitivity and stature-regression inversion caveats. |

The forearm direction is **STRONGLY SUPPORTED**, but the proposed 293.1 mm is a converted ANSUR surface-landmark span, not a selected radius length. Moving the wrist centre 5–10 mm proximally changes the estimate to 283.1–288.1 mm. The ulna still needs its own endpoint-matched target. Proposed upper-arm and shank agreement is provisional. None of these numbers authorizes a uniform limb scale.

Two statistical qualifications remain: per-bone versus per-person sampling changes independence and effective sample size; it does not by itself prove that a reported SD understates between-person spread. C2's printed 0.66 remains unclassified dispersion; "probable standard error" is a hypothesis, not an established source definition.

## Verification and checkpoint position

- 52 focused tests pass: CP2, CP3 comparator, both specimen reports, limb proposal, owner/source fixes, report comparison, source identity and direct forearm provenance.
- Full discovery: **787 tests, five failures and four errors**. The nine named failures/errors exactly match the retained pre-Claude 740-test baseline. No whole-project green claim.
- Target-selection validator passes with `freeze_ready=false`; atlas validator retains 206 bones, 427 articulations and 30 semantic frames within its static coverage scope.
- The three adversarial observations above are retained in `ORIGINAL_V1_WORK/anatomy/audit/runs/work_claude_review_20261008_001/`, with a read-only reproduction script and raw test logs. They reveal missing rejection/validation coverage despite the focused suite passing.
- Blender was **not freshly rerun in this review**. Run 002 retains summary comparison reports and hashes, but neither its raw captures nor its .blend files. Its numerical results remain archived observations pending independent fresh rehearsal; run 001 does retain a capture. The previous scratch bpy environment is no longer present.

CP1 remains PROVISIONAL/BLOCKED for exact anatomical target closure. CP2 implementation exists but is not accepted for anatomical clearance. CP3 builder rehearsal is PROVISIONAL; the immutable corrected canonical skeleton has not been created. CP4 visual review is blocked by that absence. Gates 6/8/9 and Phase 10 remain open/deferred. Production geometry, weights, runtime drivers and a003 are unchanged.

Next: repair and adversarially verify CP2 rejection paths, then continue CP1a endpoint-compatible shoulder mapping and the unresolved regional targets. Rehearse the builder afresh with retained captures before constructing the new canonical revision.
