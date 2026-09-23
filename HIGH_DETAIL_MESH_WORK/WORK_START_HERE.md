# Work start here

Use this file when resuming on the Blender laptop.

1. Read `CURRENT_STATE.md`.
2. Read `LAPTOP_CONTINUATION_HANDOFF.md`.
3. Run `RESUME_WORK.bat` (or `python scripts/preflight_resume.py`).
4. Reproduce/verify V6 before editing.
5. Continue only candidate-only work.

Current priority while the final canonical rig is being settled separately:

- First: true medial-knee retopology and anatomical patella/tendon shaping.
- Second: realistic hand/finger/thumb/palm shaping while preserving the V5/V6 push-up floor-contact guard.
- Third: skin/material work.
- Hold: final shoulder/chest/back/armpit weights and final shoulder deformation tuning until the scapula-capable canonical rig is confirmed.

After every exported candidate, prefer the one-command Windows path:

```text
RUN_CANDIDATE_GATES.bat <version>
RUN_REVIEW_PACK.bat <version>
```

For hand work also run `scripts/guard_hand_floor_vertices.py`; for knee work also run `scripts/audit_knee_topology_candidate.py`.

Do not merge, promote, overwrite V6, alter production assets, or retune exercises to make a mesh candidate pass. Older handoff/review files are historical unless `CURRENT_STATE.md` points to them.
