# W8 Authored Forearm Path Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capture phone-readable, read-only native W8 evidence for the frozen r57 nine-frame forearm-rotation benchmark without treating its single forearm control as independent radius/ulna anatomy.

**Architecture:** Add a separate Blender probe that imports the pinned r57 benchmark, observes its callback state in memory, and emits strictly validated JSON and Markdown. Integrate it into the existing W8 pose job as its own artifact so synthetic contract tests and native model evidence remain distinguishable.

**Tech Stack:** Python 3.13, Blender `bpy==5.2.0`, `unittest`, GitHub Actions.

**Spec:** `docs/HGPT_NATIVE_FOREARM_CHAIN_READINESS_20261028.md`; `docs/HGPT_HUMAN_JOINT_ROM_AND_MOVEMENT_PLAN_20261023.md`; user constraints in `docs/PHONE_CLOUD_EXECUTION_LEDGER_20261023.md`.

## Global Constraints

- Read the exact pinned W8 reconstruction and frozen r57 commit `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`; never save a `.blend`.
- Report authored suffixes as `l` and `r`, not anatomical laterality.
- Report local control rotations and evaluated geometry as diagnostic evidence, not ISB joint coordinates, anatomical ROM, tissue safety, or movement approval.
- Fail closed if source hashes, source/rest signatures, nine-frame ordering, expected controls, finite values, or explicit radius/ulna limitations are missing.
- Do not modify production assets, validated skeletal data, permanent muscle IDs, muscle attachments/highlighting, PT-App, or `PT_MODEL_VERSION 1.0`.

## Review Focus

- Malformed nested report objects must return validation errors instead of raising incidental exceptions.
- Quaternion sign equivalence must not create false motion discontinuities.
- The pronation-to-supination reversal must be represented as an authored target path, not inferred anatomical direction.
- Twist-helper rotation must be measured independently rather than copied from the frozen constants.
- Return-to-neutral is out of scope unless explicitly measured; the report must not imply it.

---

### Task 1: Read-only authored forearm path evidence

**Files:**
- Create: `scripts/phone_blender/forearm_pose_state_probe.py`
- Create: `scripts/cloud_body_analysis/tests/test_forearm_pose_state_probe.py`
- Modify: `.github/workflows/phone-blender-workbench.yml`

**Interfaces:**
- Consumes: pinned W8 reconstruction, frozen r57 `run(..., only={"forearm_rotation"})`, callback state for `forearm`, `forearm_tw0`, `forearm_tw1`, and `hand` on both authored suffixes.
- Produces: `w8_forearm_pose_state.json`, `w8_forearm_pose_state.md`, strict `validate_report(report) -> list[str]`, and a dedicated `phone-w8-forearm-pose-state-${{ github.run_id }}` artifact.

- [ ] **Step 1: Write failing pure-Python contract tests**

Cover a valid nine-sample fixture; hand-derived authored target reversal; independent local control/twist/hand observations; malformed nested mappings; nonfinite values; wrong source/signature/sample sequence; unexpected radius/ulna evidence; missing limitations; and synthetic/native labeling.

- [ ] **Step 2: Run the focused tests and observe RED**

Run: `python -m unittest discover -s scripts/cloud_body_analysis/tests -p test_forearm_pose_state_probe.py -v`

Expected: FAIL because the new probe module does not exist.

- [ ] **Step 3: Implement the minimal probe and strict validator**

The Blender entry point hashes the source once, imports the pinned benchmark, captures nine callback samples and evaluated forearm slice metrics, verifies the source/rest signatures remain unchanged, and writes JSON/Markdown. It explicitly records `separate_radius_ulna_controls_observed=false`, `anatomical_joint_coordinate_system_verified=false`, and `pronation_supination_approved=false`.

- [ ] **Step 4: Run focused and full report-only suites**

Run: `python -m unittest discover -s scripts/cloud_body_analysis/tests -p test_forearm_pose_state_probe.py -v`

Run: `python -m unittest discover -s scripts/cloud_body_analysis/tests -v`

Expected: all tests PASS.

- [ ] **Step 5: Integrate the cloud job**

Add the focused suite, the read-only probe invocation, and a dedicated 90-day artifact upload to `pose-state-w8`; do not alter existing artifact names or native source retrieval.

- [ ] **Step 6: Review, commit, and execute in cloud**

Request a fresh-context code review, fix Important/Critical findings test-first, rerun focused/full suites, commit to the isolated branch, and verify the resulting seven-job workflow plus artifact CRC/SHA256 before updating method/recovery documentation and the execution ledger.
