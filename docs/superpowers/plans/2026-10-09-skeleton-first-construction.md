# Skeleton-first construction implementation plan

> **For agentic workers:** Execute inline with superpowers:executing-plans; the owner has requested autonomous completion.

**Goal:** Explicit skeletal-data construction with no mesh-driven coordinate changes.
**Architecture:** Pure construction/validation module plus a diagnostic CLI; preserve legacy builder. Replay adapter reproduces existing records but cannot establish independent anatomy.
**Tech stack:** Python, NumPy, existing CP2 validator.
**Spec:** `docs/superpowers/specs/2026-10-09-skeleton-first-construction.md`.

## Global constraints
- No c005, no canonical promotion, no edits to a003/c001–c004 or production assets.
- Units metres; HGPT left +X, posterior +Y, up +Z.
- Missing independent evidence is UNVERIFIED, never PASS.

## Review focus
- NaN/Infinity, incorrect unit/frame metadata: reject.
- Callback/input/result aliasing: coordinates remain unchanged.
- Legacy records mistaken for evidence: explicit historical replay status.
- Bad length/joint semantics: reject invalid references and report mismatches.
- Partial anatomy coverage: retain existing CP2 failures/unverified checks.

## Task 1: Constructor and skin diagnostic
Files: `scripts/anatomy_fit/skeleton_first_builder.py`, `scripts/test_skeleton_first_builder.py`.
Interfaces: `replay_contract(record, label)`, `construct(contract)`, `skin_diagnostic(record, clearance)`.
- [x] Write tests asserting exact a003/c004 reproduction and adversarial failures.
- [x] Observe missing-feature failure.
- [x] Implement explicit-coordinate copying, metadata and constraint validation; run CP2 without changing data.
- [x] Run focused tests and retain diagnostic evidence.
- [x] Commit verified tooling and findings.

## Task 2: Evidence queue and laptop procedure
Files: standalone per-region/peak readiness reports and a documented Blender procedure.
- [x] Recompute all 78 unsourced peaks from current specs and group by measurement semantics.
- [x] Retrieve primary evidence, retaining context mismatches as blockers.
- [x] Verify stored solver/Blender captures and static anatomical validators.
- [x] Record precise gates/remaining targets; push and independently verify remote files.

Task completion describes diagnostic tooling and evidence preparation only. Full independent anatomical construction and canonical acceptance remain blocked.
