from pathlib import Path

path = Path('AI_CHANGELOG.md')
text = path.read_text(encoding='utf-8')
marker = '## Unreleased\n'
entry = r'''

### ChatGPT — 2026-09-14 — joint timing, loop-range authoring, and completed shoulder biomechanics

Retained animation-workspace commit `d4340d2` adds a real review/authoring layer rather than another exercise-specific workaround. The timeline now supports custom **Set In / Set Out / Clear range** playback ranges with a visible overlay. Custom ranges are editor playback state only and never alter the exported clip; they normalise to the clip, preserve at least one frame, rescale with duration changes, reset on exercise changes, and are ignored when Loop is disabled. Playback math is isolated in `src/editor/playback.ts` and covered by dedicated tests. The Joint panel now exposes the existing phase-local bone timing system for the selected bone in the segment under the playhead: custom start delay, finish point, and optional easing override. These edits write to `Keyframe.jointTiming`, use normal undo/redo history, and preserve the existing deterministic animation pipeline. The implementation roadmap was updated to mark this animation-authoring foundation as present.

Validation for `d4340d2`: `npm run typecheck` passed; **225 tests passed / 1 optional real-character diagnostic skipped (226 total) across 23 files**; `npm run build` passed. The only build advisory remains the pre-existing Vite >500 kB chunk warning. No character asset, retarget algorithm, canonical rig, grip mapping, exercise goal or exported data format was replaced by this work.

Retained biomechanics commit `22cc1ee` resolves the isolated-action shoulder audit without weakening skin-containment rules. The medial deltoid now follows a lateral acromion-to-humerus route and uses a measured `taper: 0.84`, the largest tested visible-belly taper that stayed inside the existing containment allowance. Pectoralis keeps its previously proven visible chest-to-humerus line and gains a hidden proximal-humerus functional via point near `(0.02, 0.02, -0.02)`, making the trainer-level path shorten in both shoulder flexion (~6.6%) and adduction (~5.2%) without dragging the visible belly through the pull-up armpit. Latissimus likewise keeps its proven visible endpoints and gains a hidden proximal-humerus via point near `(0.04, 0.04, 0.04)`, producing shortening in isolated extension (~4.1%) and adduction (~4.9%). `src/muscles/functions.test.ts` now permanently checks all declared joint crossings plus elbow, wrist, knee, shoulder, scapular/trunk, hip and ankle functional actions.

Validation for `22cc1ee`: `npm run typecheck` passed; **218 tests passed / 1 optional diagnostic skipped (219 total) across 22 files**; production build passed. Rejected during that work: a high/anterior visible pectoral candidate that was mechanically correct but protruded roughly 35 mm during pull-up, and a changed visible lat insertion that missed the existing pull-up containment allowance by ~0.147 mm. The retained pattern is therefore deliberate: keep containment-safe rendered geometry and use hidden functional via points where joint-spanning length needs a more anatomical route. Functional path length remains a geometric motion diagnostic, not a force or EMG estimate.
'''

if '### ChatGPT — 2026-09-14 — joint timing, loop-range authoring, and completed shoulder biomechanics' in text:
    print('handoff already present')
else:
    if marker not in text:
        raise SystemExit('Unreleased marker missing')
    text = text.replace(marker, marker + entry, 1)
    path.write_text(text, encoding='utf-8')
    print('Updated AI_CHANGELOG.md')
