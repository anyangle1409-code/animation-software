# Phase 9 isolated movement run on c003 (coupled thorax and shoulder audit candidate)

**Results:** 135/135 integrity PASS; 41/43 mirror PASS (`hip_rotation_at_0/90_flexion` are side-specific by source). All of these PASS:
- the shoulder-complex and scapulothoracic-rhythm tests;
- the GH tests;
- the rib 1–7 pump-handle tests on the rotated ribs.

The source blend (`3962215043cebbcf…`) is unchanged.

**Inputs:**
- A run-local record copy from `prepare_candidate_movement_run.py`; its only change is the provenance blend hash.
- The test blend and the duplicate samples are not committed (regenerable; hashes in the report).

**Clips** (`clips/`): a003 vs c003 side-by-side GIFs and keyframe sheets, front and rear. Bone sticks are parented to the armature bones; the mesh is unskinned.

This is implementation-integrity evidence, not anatomical acceptance or Gate 9.
