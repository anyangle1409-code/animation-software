# Phase 9 isolated movement run on c004 (arm skeleton_input resync of c003)

**Results:** 135/135 integrity PASS; 41/43 mirror PASS (the same two side-specific hip pairs as a003 and c003).

**Source blend:** the c003 blend `3962215043cebbcf…`, reused byte-identically (c004 geometry is c003's); it is unchanged after the run.

**Inputs:**
- A run-local copy of `candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json` from `prepare_candidate_movement_run.py`; its only change is the provenance blend hash.
- The test blend and the run-local record are not committed (regenerable; hashes in the report).

**Against c003:** 111 test sample sets are byte-identical. The 24 hand, thumb and wrist tests that changed reproduce a003's rotations and measured angles within float32 bounds (`../../candidates/shoulder_thorax_c004_arm_inputs/run_comparison.json`). The wrist sweeps no longer open the radiocarpal joint; c003's opened it by 16.7 mm.

This is implementation-integrity evidence, not anatomical acceptance or Gate 9.
