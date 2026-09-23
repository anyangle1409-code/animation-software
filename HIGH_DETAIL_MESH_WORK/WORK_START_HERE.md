# Work start here

Use this file when resuming on the Blender laptop.

1. Read `LAPTOP_CONTINUATION_HANDOFF.md`.
2. Run `python scripts/preflight_resume.py`.
3. Reproduce/verify V6 before editing.
4. Continue only candidate-only work.

Current priority while the final canonical rig is being settled separately:

- First: true medial-knee retopology and anatomical patella/tendon shaping.
- Second: realistic hand/finger/thumb/palm shaping while preserving the V5/V6 push-up floor-contact guard.
- Third: skin/material work.
- Hold: final shoulder/chest/back/armpit weights and final shoulder deformation tuning until the scapula-capable canonical rig is confirmed.

For every new candidate GLB, run:

```text
python scripts/candidate_quick_check.py path/to/new_candidate.glb
```

This catches accidental rig/animation/material changes and basic topology damage before running the slower exercise/Blender validation.

Do not merge, promote, overwrite V6, alter production assets, or retune exercises to make a mesh candidate pass.
