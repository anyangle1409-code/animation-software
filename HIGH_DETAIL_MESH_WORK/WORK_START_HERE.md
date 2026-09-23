# Work start here

Use this file when resuming on the Blender laptop.

1. Read `CURRENT_STATE.md`.
2. Read `LAPTOP_CONTINUATION_HANDOFF.md`.
3. Run `RESUME_WORK.bat` (or `python scripts/preflight_resume.py`).
4. Reproduce/verify V6 before editing.
5. Read `CANDIDATE_OUTPUT_CONTRACT.md`.
6. Use `START_CANDIDATE.bat <version>` for a fresh editable working copy.
7. Continue only candidate-only work.

Current priority while the final canonical rig is being settled separately:

- First: true medial-knee retopology and anatomical patella/tendon shaping.
- Second: realistic hand/finger/thumb/palm shaping while preserving the V5/V6 push-up floor-contact guard.
- Third: skin/material work.
- Hold: final shoulder/chest/back/armpit weights and final shoulder deformation tuning until the scapula-capable canonical rig is confirmed.

After every exported candidate, the shortest path is:

```text
FINISH_CANDIDATE.bat <version> <task>
```

where `<task>` is `knee`, `hand`, or `material`. This runs the standard gates, task-specific audit, visual review pack, and checkpoint automatically. The lower-level `RUN_CANDIDATE_GATES.bat` and `RUN_REVIEW_PACK.bat` remain available for partial reruns.

Do not merge, promote, overwrite V6, alter production assets, or retune exercises to make a mesh candidate pass. Older handoff/review files are historical unless `CURRENT_STATE.md` points to them.
