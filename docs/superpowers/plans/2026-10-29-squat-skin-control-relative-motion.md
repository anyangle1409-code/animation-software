# Squat Skin-Control Relative Motion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only, arithmetic-verified comparison between each authored W8 foot-control head and its evaluated foot/toe-dominant skin lower centroid across the existing nine squat samples.

**Architecture:** Extend the existing squat pose report only. A pure-Python helper derives per-side head-minus-centroid vectors and sample-zero deltas from already captured native values; report validation recomputes every field, and the phone Markdown labels the record descriptive and non-contact.

**Tech Stack:** Python standard library, unittest, Blender 5.2 GitHub Actions probe.

**Spec:** `docs/HGPT_W8_AUTHORED_SQUAT_CONTROL_OBSERVATIONS_20261029.md`

## Global Constraints

- Read-only diagnostics only; never save or modify a `.blend`.
- Preserve immutable source hashes and all validated skeletal data.
- Do not infer floor contact, support, pressure, force, friction, slip, balance, tissue safety, anatomical joint centres, or movement approval.
- Population range-of-motion averages are not hard limits.
- No muscle attachment/highlighting, PT-App, PT_MODEL_VERSION 1.0, Claude branch, production, merge, or deployment change.

## Review Focus

- Missing or nonfinite head/centroid vectors must fail closed.
- Sample-zero deltas must be exact zero within the existing numeric tolerance.
- Tampered derived vectors or deltas must be rejected by report validation.
- Runtime suffixes must remain exactly `l` and `r`.
- The phone report must preserve explicit non-contact and non-anatomical wording.

---

### Task 1: Skin-control relative-motion record

**Files:**
- Modify: `scripts/phone_blender/squat_pose_state_probe.py`
- Modify: `scripts/cloud_body_analysis/tests/test_squat_pose_state_probe.py`
- Modify after native verification: `docs/HGPT_W8_AUTHORED_SQUAT_CONTROL_OBSERVATIONS_20261029.md`
- Modify after native verification: `docs/PHONE_CLOUD_EXECUTION_LEDGER_20261023.md`
- Create after native verification: `recovery_20261023/cloud_verification_20261029_run<id>.json`

**Interfaces:**
- Consumes: each sample's `sides[side].foot.head_world_m_not_anatomical_joint_centre` and `foot_skin_lower_envelope.sides[side].lower_centroid_world_m`.
- Produces: `skin_control_relative_motion(samples) -> dict` with status, `contact_claimed=false`, and per-sample/per-side head-minus-centroid vectors plus changes from sample 0.

- [ ] **Step 1: Write failing pure-Python tests**

Add tests for exact vector/delta arithmetic, nonfinite/missing inputs, validation rejection of tampered derived data, and explicit phone-report non-contact wording.

- [ ] **Step 2: Run focused tests to verify RED**

Run: `python -m unittest scripts/cloud_body_analysis/tests/test_squat_pose_state_probe.py -v`

Expected: new tests fail because `skin_control_relative_motion` and report fields do not exist.

- [ ] **Step 3: Implement minimal derivation and validation**

Add the helper, attach its output at report level after all nine samples are captured, recompute it during `validate_report`, and add a compact phone table. Use existing `vector3`, `_subtract`, `_valid_vector`, and `_vectors_close` conventions.

- [ ] **Step 4: Run focused and full tests**

Run focused command above, then `python -m unittest discover -s scripts/cloud_body_analysis/tests -v`.

Expected: all focused and full tests pass, with no model writes.

- [ ] **Step 5: Publish to the isolated branch and verify cloud-native evidence**

Commit only the two source/test files, wait for all seven workflow jobs, independently download/CRC/hash the exact squat artifact, inspect native values, update the method document, ledger, and recovery JSON, and identify the next unblocked task.
