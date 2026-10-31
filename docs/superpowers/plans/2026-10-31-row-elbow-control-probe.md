# W8 Row Elbow Control Probe Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans; retain one fresh-context final review.

**Goal:** Observe elbow bending on the unchanged frozen bent-over-row path and distinguish authored target, local control rotation and included point-chain angle.
**Architecture:** A separate in-memory native probe reuses the forearm probe's hash, control and quaternion validation helpers. It captures nine bilateral upperarm/forearm/hand control records, derives unsigned included elbow angles, and records existing whole-body benchmark flags without claiming elbow-local deformation metrics.
**Tech Stack:** Python, Blender 5.2, unittest, existing GitHub Actions.
**Spec:** docs/HGPT_W8_FOREARM_AUTHORED_PATH_20261031.md and docs/PHONE_CLOUD_EXECUTION_LEDGER_20261023.md.

## Global Constraints
- Exact W8 source SHA and r57 revision remain pinned; never save a blend or change protected assets.
- Row combines shoulder movement and elbow bending. No standalone elbow test, anatomical sides, ISB coordinates, radius/ulna evidence, contact, safety, corrective-skin or movement approval.
- The frozen row target holds elbow0deg through sample4 then reaches100deg at sample8; shoulder target reaches45deg at sample4 and ends-40deg. Targets are not observed anatomical angles.
- All nine records, strict numeric types, source/rest guards, quaternion/angle consistency and measured-angle recomputation must validate before output.

## Review Focus
- Non-dict nested rows, invalid numeric types and huge finite coordinates must return errors.
- Zero-length point chains must fail closed; quaternions q/-q must agree.
- Commanded and measured angles must be separate; measured included geometry may differ from authored targets.
- Whole-body flags are not elbow-local failures; no invented geometry acceptance threshold.
- The path ends flexed; do not claim return-to-neutral.

### Task 1: Native row-control evidence
Files: scripts/phone_blender/row_elbow_pose_state_probe.py; scripts/cloud_body_analysis/tests/test_row_elbow_pose_state_probe.py; .github/workflows/phone-blender-workbench.yml.
Interfaces: authored_targets(t), included_elbow_angle_deg(controls), validate_report(data), markdown(data); output w8_row_elbow_pose_state.json/.md and separate phone-w8-row-elbow-pose-state artifact.
- [ ] Write synthetic tests with hand-derived targets [0,0,0,0,0,15.625,50,84.375,100], right-angle/asymmetric points, invalid/degenerate evidence and tampered metrics. Observe RED missing module.
- [ ] Implement native capture via frozen bench.run(only=['bent_over_row']) with before/after source and rest signatures. Derive included angle from upperarm head, forearm head and hand head.
- [ ] Run focused and full report-only suites, compile and diff checks.
- [ ] Add focused tests, isolated probe step and dedicated artifact upload to existing pose job; keep existing steps intact.
- [ ] Fresh-context review; address Important/Critical findings test-first. Commit to existing isolated cloud lane and verify seven jobs plus independent artifact CRC/SHA256 and report replay.
- [ ] Record native findings and next task in method, machine record and ledger. No model improvement or anatomical approval claim.

Ruling: this increment captures control geometry and existing whole-body flags only; elbow-local skin measurements require a separately pinned region/vertex contract and are not invented here. User has already requested autonomous continuation without design check-ins.
