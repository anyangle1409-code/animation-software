from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected one match, found {count}: {old[:120]!r}')
    file.write_text(text.replace(old, new, 1), encoding='utf-8')


# -------------------------------------------------------------------------
# Clip model: semantic pose markers live on keyframes and export with them.
# -------------------------------------------------------------------------
replace_once(
    'src/animation/clip.ts',
    "export interface KeyframeIK {\n",
    "export type PoseMarkerKind = 'start' | 'transition' | 'peak' | 'return';\n\nexport interface KeyframeIK {\n",
)
replace_once(
    'src/animation/clip.ts',
    "  /** Optional per-bone timing used from this keyframe to the next. */\n  jointTiming?: Partial<Record<BoneName, PhaseJointTiming>>;\n  label?: string;",
    "  /** Optional per-bone timing used from this keyframe to the next. */\n  jointTiming?: Partial<Record<BoneName, PhaseJointTiming>>;\n  /** Semantic landmark used by the Studio timeline; it does not alter motion. */\n  marker?: PoseMarkerKind;\n  label?: string;",
)

# -------------------------------------------------------------------------
# Deterministic generated defaults: Start, first Peak, transitions, Return.
# -------------------------------------------------------------------------
replace_once(
    'src/animation/generate.ts',
    "import type { Keyframe, KeyframeIK, StudioClip } from './clip';",
    "import type { Keyframe, KeyframeIK, PoseMarkerKind, StudioClip } from './clip';",
)
replace_once(
    'src/animation/generate.ts',
    "    phaseId: phases[0].id,\n    label: exercise.startPose.label,",
    "    phaseId: phases[0].id,\n    marker: 'start',\n    label: exercise.startPose.label,",
)
replace_once(
    'src/animation/generate.ts',
    "  phases.forEach((phase, index) => {\n    time += phaseDuration(exercise, phase);\n    const next = phases[index + 1];\n    keyframes.push({",
    "  phases.forEach((phase, index) => {\n    time += phaseDuration(exercise, phase);\n    const next = phases[index + 1];\n    const previous = phases[index - 1];\n    const isLast = index === phases.length - 1;\n    const marker: PoseMarkerKind = isLast\n      ? 'return'\n      : phase.to === 'peak' && previous?.to !== 'peak'\n        ? 'peak'\n        : 'transition';\n    keyframes.push({",
)
replace_once(
    'src/animation/generate.ts',
    "      phaseId: next?.id,\n      label: phase.to === 'peak' ? exercise.peakPose.label : exercise.startPose.label,",
    "      phaseId: next?.id,\n      marker,\n      label: phase.to === 'peak' ? exercise.peakPose.label : exercise.startPose.label,",
)

# -------------------------------------------------------------------------
# Store: undoable marker edits.
# -------------------------------------------------------------------------
replace_once(
    'src/editor/store.ts',
    "import type { StudioClip, Keyframe } from '../animation/clip';",
    "import type { StudioClip, Keyframe, PoseMarkerKind } from '../animation/clip';",
)
replace_once(
    'src/editor/store.ts',
    "  setKeyframeEasing: (id: string, easing: Keyframe['easing']) => void;\n  setJointTiming: (id: string, bone: BoneName, timing: PhaseJointTiming | null) => void;",
    "  setKeyframeEasing: (id: string, easing: Keyframe['easing']) => void;\n  setKeyframeMarker: (id: string, marker: PoseMarkerKind | null) => void;\n  setJointTiming: (id: string, bone: BoneName, timing: PhaseJointTiming | null) => void;",
)
replace_once(
    'src/editor/store.ts',
    "    setKeyframeEasing: (id, easing) =>\n      editClip((clip) => ({\n        ...clip,\n        keyframes: clip.keyframes.map((frame) => (frame.id === id ? { ...frame, easing } : frame)),\n      })),\n\n    setJointTiming:",
    "    setKeyframeEasing: (id, easing) =>\n      editClip((clip) => ({\n        ...clip,\n        keyframes: clip.keyframes.map((frame) => (frame.id === id ? { ...frame, easing } : frame)),\n      })),\n\n    setKeyframeMarker: (id, marker) =>\n      editClip((clip) => ({\n        ...clip,\n        keyframes: clip.keyframes.map((frame) =>\n          frame.id === id ? { ...frame, marker: marker ?? undefined } : frame,\n        ),\n      })),\n\n    setJointTiming:",
)

# -------------------------------------------------------------------------
# Timeline: editable marker selector + labelled semantic landmarks.
# -------------------------------------------------------------------------
replace_once(
    'src/editor/Timeline.tsx',
    "import { sortedKeyframes } from '../animation/clip';",
    "import { sortedKeyframes } from '../animation/clip';\nimport type { PoseMarkerKind } from '../animation/clip';",
)
replace_once(
    'src/editor/Timeline.tsx',
    "const PHASE_COLOURS: Record<string, string> = {\n  concentric: '#2f5d4a',\n  eccentric: '#3a4a6b',\n  isometric: '#4a4030',\n};",
    "const PHASE_COLOURS: Record<string, string> = {\n  concentric: '#2f5d4a',\n  eccentric: '#3a4a6b',\n  isometric: '#4a4030',\n};\n\nconst POSE_MARKER_LABELS: Record<PoseMarkerKind, string> = {\n  start: 'Start',\n  transition: 'Transition',\n  peak: 'Peak',\n  return: 'Return',\n};",
)
replace_once(
    'src/editor/Timeline.tsx',
    "  const setKeyframeEasing = useStudio((state) => state.setKeyframeEasing);\n  const setDuration = useStudio((state) => state.setDuration);",
    "  const setKeyframeEasing = useStudio((state) => state.setKeyframeEasing);\n  const setKeyframeMarker = useStudio((state) => state.setKeyframeMarker);\n  const setDuration = useStudio((state) => state.setDuration);",
)
replace_once(
    'src/editor/Timeline.tsx',
    "        {current && (\n          <label className=\"field field--inline\">\n            <span className=\"field__label\">Easing</span>",
    "        {current && (\n          <label className=\"field field--inline\">\n            <span className=\"field__label\">Marker</span>\n            <select\n              value={current.marker ?? ''}\n              onChange={(event) =>\n                setKeyframeMarker(\n                  current.id,\n                  event.target.value ? (event.target.value as PoseMarkerKind) : null,\n                )\n              }\n            >\n              <option value=\"\">None</option>\n              {Object.entries(POSE_MARKER_LABELS).map(([kind, label]) => (\n                <option key={kind} value={kind}>\n                  {label}\n                </option>\n              ))}\n            </select>\n          </label>\n        )}\n        {current && (\n          <label className=\"field field--inline\">\n            <span className=\"field__label\">Easing</span>",
)
replace_once(
    'src/editor/Timeline.tsx',
    "            className={`timeline__key ${current?.id === frame.id ? 'is-current' : ''}`}\n            style={{ left: `${(frame.time / clip.duration) * 100}%` }}\n            title={`${frame.label ?? 'Keyframe'} at ${frame.time.toFixed(2)}s`}",
    "            className={`timeline__key ${frame.marker ? `has-marker marker-${frame.marker}` : ''} ${current?.id === frame.id ? 'is-current' : ''}`}\n            data-marker-label={frame.marker ? POSE_MARKER_LABELS[frame.marker] : undefined}\n            style={{ left: `${(frame.time / clip.duration) * 100}%` }}\n            title={`${frame.marker ? `${POSE_MARKER_LABELS[frame.marker]} · ` : ''}${frame.label ?? 'Keyframe'} at ${frame.time.toFixed(2)}s`}",
)

styles = Path('src/editor/styles.css')
styles.write_text(styles.read_text(encoding='utf-8') + r'''

/* ---------- semantic pose markers ---------- */

.timeline__key.has-marker::after {
  content: attr(data-marker-label);
  position: absolute;
  left: 50%;
  top: -19px;
  transform: translateX(-50%) rotate(-45deg);
  transform-origin: center;
  white-space: nowrap;
  font-size: 9px;
  line-height: 1;
  color: var(--muted);
  pointer-events: none;
}

.timeline__key.marker-start {
  box-shadow: 0 0 0 2px rgba(79, 214, 160, 0.34);
}

.timeline__key.marker-peak {
  box-shadow: 0 0 0 2px rgba(255, 196, 92, 0.42);
}

.timeline__key.marker-return {
  box-shadow: 0 0 0 2px rgba(111, 190, 255, 0.38);
}

.timeline__key.marker-transition {
  box-shadow: 0 0 0 2px rgba(177, 139, 255, 0.3);
}
''', encoding='utf-8')

# -------------------------------------------------------------------------
# Regression tests.
# -------------------------------------------------------------------------
replace_once(
    'src/animation/animation.test.ts',
    "    expect(clip.name).toBe('bicep_curl');\n  });",
    "    expect(clip.name).toBe('bicep_curl');\n  });\n\n  it('adds deterministic semantic pose markers for review', () => {\n    expect(clip.keyframes.map((frame) => frame.marker)).toEqual([\n      'start',\n      'peak',\n      'transition',\n      'transition',\n      'return',\n    ]);\n  });",
)

store_test = Path('src/editor/store.test.ts')
store_text = store_test.read_text(encoding='utf-8')
store_text += r'''

describe('pose marker authoring', () => {
  beforeEach(() => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('edits a keyframe marker through undoable document history', () => {
    const frame = useStudio.getState().document.clip.keyframes[1];
    expect(frame.marker).toBe('peak');

    useStudio.getState().setKeyframeMarker(frame.id, 'transition');
    expect(useStudio.getState().document.clip.keyframes[1].marker).toBe('transition');

    useStudio.getState().undo();
    expect(useStudio.getState().document.clip.keyframes[1].marker).toBe('peak');
  });

  it('can clear a generated marker without changing the keyframe motion', () => {
    const before = useStudio.getState().document.clip.keyframes[0];
    const x = before.pose.rotations.forearm_l?.x;
    useStudio.getState().setKeyframeMarker(before.id, null);
    const after = useStudio.getState().document.clip.keyframes[0];
    expect(after.marker).toBeUndefined();
    expect(after.pose.rotations.forearm_l?.x).toBe(x);
  });
});
'''
store_test.write_text(store_text, encoding='utf-8')

# -------------------------------------------------------------------------
# Roadmap + Claude handoff, committed only if the full gate passes.
# -------------------------------------------------------------------------
replace_once(
    'docs/STUDIO_CAPABILITY_ROADMAP.md',
    "- Selected-bone timing authoring for delay, finish point and easing on each keyframe segment.\n- Individual finger/thumb joint authoring remains available through the same joint workspace.",
    "- Selected-bone timing authoring for delay, finish point and easing on each keyframe segment.\n- Semantic Start / Transition / Peak / Return pose markers are generated deterministically and editable on keyframes.\n- Individual finger/thumb joint authoring remains available through the same joint workspace.",
)

changelog = Path('AI_CHANGELOG.md')
text = changelog.read_text(encoding='utf-8')
heading = '### ChatGPT — 2026-09-14 — semantic pose-marker authoring'
entry = r'''

### ChatGPT — 2026-09-14 — semantic pose-marker authoring

Added semantic pose landmarks directly to `Keyframe` as `marker?: 'start' | 'transition' | 'peak' | 'return'`. Generated exercise clips now classify their deterministic boundaries as Start, first arrival at Peak, intermediate Transition boundaries, and final Return. Markers are metadata only: they do not change pose interpolation, IK, joint timing, contacts, equipment or export motion. The Timeline renders the landmarks as labelled keyframes and exposes an editable Marker selector for the keyframe under the playhead. Marker edits use the existing document history, so undo/redo works normally and clearing a marker leaves the underlying pose untouched.

The bicep-curl template now generates `[start, peak, transition, transition, return]` across its existing five keyframes. Regression coverage checks deterministic marker generation, undoable marker editing and marker clearing without pose mutation. The Studio capability roadmap now records pose markers as implemented.
'''
if heading not in text:
    marker = '## Unreleased\n'
    if marker not in text:
        raise SystemExit('AI_CHANGELOG.md: Unreleased marker missing')
    changelog.write_text(text.replace(marker, marker + entry, 1), encoding='utf-8')

print('Applied semantic pose-marker authoring')
