# Experimental muscle foundation implementation plan

Spec: docs/WORK_TO_CLAUDE_EXPERIMENTAL_MUSCLE_HANDOFF_20261022.md and associated research.
User authorizes autonomous implementation, separate experimental branch, no production changes.

Architecture: Python standard-library authoring utilities, independent of app runtime. A bilateral semantic catalogue preserves unverified landmarks as null; an explicit rig-local binding contract feeds a pure geometry kernel. A guarded copy/inspection tool prepares native work without editing the source. No automatic production integration.

- [x] Expand 60 seed records bilaterally; preserve source, crossing, depth and interaction information. Validate IDs, sides, references, finite coordinates, actual supplied bone IDs, review provenance and readiness separately.
- [x] Implement anchored paths, via-point clearance diagnostics, volume-preserving elliptical belly response with independent visual activation, and normalized region-local skin displacement. Reject invalid inputs; do not claim physical simulation or physiological activation.
- [x] Test with analytic synthetic geometry: transforms, two-joint paths, blocked bone penetration, constant-volume shortening/lengthening/isometric activation, deep masks and bounded blends.
- [x] Prepare hash-checked exclusive source copy and read-only Blender scene inventory. Test copy failure cases; label native execution blocked if unavailable.
- [x] Record source snapshots, benchmark reuse, actual test output and precise Claude instructions; commit and open draft PR.

Review focus: anatomical side is not runtime suffix; missing landmarks must not become zeros; NaN/negative geometry must fail; skin mask outside region stays unchanged; source copy must never overwrite existing files or follow aliases back to source.

Rulings: retain PR123 as code base, with newer R57 source pinned externally rather than merging unrelated experimental model branches. Latest application branch a4f0c100 is Body v2 WIP, not a validated ORIGINAL_v1 replacement. No existing production files will be changed. New binding coordinates require local review, not inference from control rods.

## Execution ledger
All five foundation tasks executed; native/actual-anatomy work remains blocked as itemized in CLAUDE_HANDOFF.md. 24 pure tests PASS; native inventory script syntax PASS only. App suite blocked: Vitest absent. Independent code review found overflow false-clear and empty-readiness gaps; both reproduced RED then fixed GREEN. Full final suite 24/24. Compressed source-copy guard corrected against actual R41 zstd bytes, with regression test. No production files changed.
