# Work start here

1. Read `CURRENT_STATE.md` and `RIG_55_BASELINE.md`.
2. Run `RESUME_WORK.bat`. It prepares the exact 55-bone validation source at `c2372c1`.
3. Read `CANDIDATE_OUTPUT_CONTRACT.md`.
4. Use `START_CANDIDATE.bat <version>` for a fresh editable working copy.
5. Keep all work candidate-only.

Current priority:
- first: true medial-knee retopology and patella/tendon/medial-knee shaping
- second: realistic hand/finger/thumb/palm/wrist geometry, preserving push-up floor contact
- third: skin/material work
- fourth, if time remains: shoulder/back/chest/armpit topology/geometry preparation for the confirmed scapula structure

The 55-bone rig is confirmed. Do **not** finalise hand weights yet, do not enable scapular rhythm, and do not claim final scapula weighting until a candidate character asset explicitly contains/uses scapula deform influences and neutral equivalence is re-proven.

After export:

```text
FINISH_CANDIDATE.bat <version> <task>
```

Task is `knee`, `hand`, `material`, or `shoulder`.

Do not merge, promote, overwrite V6, alter production assets, or retune exercises to make a mesh candidate pass.
