from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected one match, found {count}: {old[:120]!r}')
    file.write_text(text.replace(old, new, 1), encoding='utf-8')

# Store: per-instance hand grip offsets are document edits and regenerate deterministically.
replace_once(
    'src/editor/store.ts',
    "  setGripClosure: (closure: number) => void;\n  setLockEnabled: (lockId: string, enabled: boolean) => void;",
    "  setGripClosure: (closure: number) => void;\n  setEquipmentGripOffset: (instanceId: string, offset: Vec3 | null) => void;\n  setLockEnabled: (lockId: string, enabled: boolean) => void;",
)
replace_once(
    'src/editor/store.ts',
    "    setGripClosure: (closure) =>\n      commit((document) => {\n        const normalized = Math.max(0, Math.min(1, closure));\n        const exercise = {\n          ...document.exercise,\n          hands: { ...document.exercise.hands, closure: normalized },\n        };\n        return { exercise, clip: generateClip(skeleton, exercise) };\n      }),\n\n    setLockEnabled:",
    "    setGripClosure: (closure) =>\n      commit((document) => {\n        const normalized = Math.max(0, Math.min(1, closure));\n        const exercise = {\n          ...document.exercise,\n          hands: { ...document.exercise.hands, closure: normalized },\n        };\n        return { exercise, clip: generateClip(skeleton, exercise) };\n      }),\n\n    setEquipmentGripOffset: (instanceId, offset) =>\n      commit((document) => {\n        const instances = document.exercise.equipment.instances.map((instance) => {\n          if (instance.id !== instanceId || instance.attachment.mode !== 'hand') return instance;\n          if (offset) {\n            return {\n              ...instance,\n              attachment: { ...instance.attachment, gripOffset: { ...offset } },\n            };\n          }\n          const { gripOffset: _gripOffset, ...attachment } = instance.attachment;\n          return { ...instance, attachment };\n        });\n        const exercise = {\n          ...document.exercise,\n          equipment: { ...document.exercise.equipment, instances },\n        };\n        return { exercise, clip: generateClip(skeleton, exercise) };\n      }),\n\n    setLockEnabled:",
)

# Grip panel: show and edit effective hand-local grip centre in mm.
replace_once(
    'src/editor/panels/GripPanel.tsx',
    "import { GRIP_CLOSURE_PRESETS, measureGripFit } from '../../equipment/gripDiagnostics';",
    "import { anatomicalGripOffset } from '../../equipment/attach';\nimport { GRIP_CLOSURE_PRESETS, measureGripFit } from '../../equipment/gripDiagnostics';\nimport type { Vec3 } from '../../rig/types';",
)
replace_once(
    'src/editor/panels/GripPanel.tsx',
    "  const setGripClosure = useStudio((state) => state.setGripClosure);",
    "  const setGripClosure = useStudio((state) => state.setGripClosure);\n  const setEquipmentGripOffset = useStudio((state) => state.setEquipmentGripOffset);",
)
replace_once(
    'src/editor/panels/GripPanel.tsx',
    "      return [{\n        id: instance.id,\n        label: instance.label ?? instance.id,\n        fit: measureGripFit(evaluation, transform, instance.attachment.side),\n      }];",
    "      return [{\n        id: instance.id,\n        label: instance.label ?? instance.id,\n        side: instance.attachment.side,\n        offset: instance.attachment.gripOffset ?? anatomicalGripOffset(instance.attachment.side),\n        isCustomOffset: Boolean(instance.attachment.gripOffset),\n        fit: measureGripFit(evaluation, transform, instance.attachment.side),\n      }];",
)
replace_once(
    'src/editor/panels/GripPanel.tsx',
    "  return (\n    <section className=\"panel grip-panel\">",
    "  const updateOffset = (id: string, current: Vec3, axis: keyof Vec3, millimetres: number) => {\n    setEquipmentGripOffset(id, { ...current, [axis]: millimetres / 1000 });\n  };\n\n  return (\n    <section className=\"panel grip-panel\">",
)
replace_once(
    'src/editor/panels/GripPanel.tsx',
    "          {measurements.map(({ id, label, fit }) => (\n            <div className=\"grip-fit\" key={id}>\n              <div className=\"grip-fit__head\">\n                <strong>{label}</strong>\n                <span className={fit.withinEnvelope ? 'status-ok' : 'status-warn'}>\n                  {fit.withinEnvelope ? 'Within envelope' : 'Review fit'}\n                </span>\n              </div>\n              <dl className=\"spec-list\">",
    "          {measurements.map(({ id, label, offset, isCustomOffset, fit }) => (\n            <div className=\"grip-fit\" key={id}>\n              <div className=\"grip-fit__head\">\n                <strong>{label}</strong>\n                <span className={fit.withinEnvelope ? 'status-ok' : 'status-warn'}>\n                  {fit.withinEnvelope ? 'Within envelope' : 'Review fit'}\n                </span>\n              </div>\n              <div className=\"grip-offset-grid\">\n                {(['x', 'y', 'z'] as const).map((axis) => (\n                  <label className=\"field\" key={axis}>\n                    <span className=\"field__label\">Grip {axis.toUpperCase()} · mm</span>\n                    <input\n                      type=\"number\"\n                      step={1}\n                      value={Math.round(offset[axis] * 1000)}\n                      onChange={(event) => updateOffset(id, offset, axis, Number(event.target.value))}\n                    />\n                  </label>\n                ))}\n              </div>\n              <div className=\"button-row\">\n                <button\n                  type=\"button\"\n                  disabled={!isCustomOffset}\n                  onClick={() => setEquipmentGripOffset(id, null)}\n                >\n                  Reset anatomical centre\n                </button>\n              </div>\n              <dl className=\"spec-list\">",
)
replace_once(
    'src/editor/panels/GripPanel.tsx',
    "        “Within envelope” uses the same finger reach and wrap geometry as the Studio's grip regression.\n        It is an animation-fit diagnostic, not a force or injury-safety score.",
    "        Grip X/Y/Z is the handle centre in hand-local millimetres. “Within envelope” uses the same\n        finger reach and wrap geometry as the Studio's grip regression. It is an animation-fit diagnostic,\n        not a force or injury-safety score.",
)

styles = Path('src/editor/styles.css')
styles.write_text(styles.read_text(encoding='utf-8') + r'''

.grip-offset-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
  margin: 8px 0;
}

.grip-offset-grid input {
  min-width: 0;
  width: 100%;
}
''', encoding='utf-8')

# Store regression: custom grip centre is undoable and actually drives the resolved handle.
store_test = Path('src/editor/store.test.ts')
store_text = store_test.read_text(encoding='utf-8')
store_text += r'''

describe('equipment grip-offset calibration', () => {
  beforeEach(() => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('stores an undoable custom hand-local grip centre', () => {
    const custom = { x: -0.02, y: 0.08, z: 0.006 };
    useStudio.getState().setEquipmentGripOffset('dumbbell_l', custom);
    const instance = useStudio.getState().document.exercise.equipment.instances.find(
      (entry) => entry.id === 'dumbbell_l',
    )!;
    expect(instance.attachment.mode).toBe('hand');
    if (instance.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(instance.attachment.gripOffset).toEqual(custom);

    useStudio.getState().undo();
    const restored = useStudio.getState().document.exercise.equipment.instances.find(
      (entry) => entry.id === 'dumbbell_l',
    )!;
    expect(restored.attachment.mode).toBe('hand');
    if (restored.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(restored.attachment.gripOffset).toBeUndefined();
  });

  it('moves the resolved dumbbell to the authored local grip centre and can reset it', () => {
    const custom = { x: -0.018, y: 0.082, z: 0.004 };
    useStudio.getState().setEquipmentGripOffset('dumbbell_l', custom);
    const clip = useStudio.getState().document.clip;
    const evaluation = new (require('../rig/skeleton').PoseEvaluation)(
      require('../rig/skeleton').canonicalSkeleton,
    );
    const frame = require('../animation/pipeline').resolveFrame(
      require('../rig/skeleton').canonicalSkeleton,
      evaluation,
      clip,
      0,
    );
    evaluation.apply(frame.pose);
    const expected = evaluation.localToWorld('hand_l', custom, new (require('three').Vector3)());
    expect(frame.equipment.get('dumbbell_l')!.position.distanceTo(expected)).toBeLessThan(1e-9);

    useStudio.getState().setEquipmentGripOffset('dumbbell_l', null);
    const reset = useStudio.getState().document.exercise.equipment.instances.find(
      (entry) => entry.id === 'dumbbell_l',
    )!;
    if (reset.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(reset.attachment.gripOffset).toBeUndefined();
  });
});
'''
store_test.write_text(store_text, encoding='utf-8')

# The repository uses ESM TypeScript, so replace the temporary require-based test fragment with imports.
replace_once(
    'src/editor/store.test.ts',
    "import { useStudio } from './store';",
    "import { Vector3 } from 'three';\nimport { resolveFrame } from '../animation/pipeline';\nimport { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';\nimport { useStudio } from './store';",
)
replace_once(
    'src/editor/store.test.ts',
    "    const evaluation = new (require('../rig/skeleton').PoseEvaluation)(\n      require('../rig/skeleton').canonicalSkeleton,\n    );\n    const frame = require('../animation/pipeline').resolveFrame(\n      require('../rig/skeleton').canonicalSkeleton,\n      evaluation,\n      clip,\n      0,\n    );\n    evaluation.apply(frame.pose);\n    const expected = evaluation.localToWorld('hand_l', custom, new (require('three').Vector3)());",
    "    const evaluation = new PoseEvaluation(canonicalSkeleton);\n    const frame = resolveFrame(canonicalSkeleton, evaluation, clip, 0);\n    evaluation.apply(frame.pose);\n    const expected = evaluation.localToWorld('hand_l', custom, new Vector3());",
)

# Roadmap and Claude handoff.
replace_once(
    'docs/STUDIO_CAPABILITY_ROADMAP.md',
    "- Dedicated Grip workspace provides undoable closure presets and live measured finger/handle fit using the established regression envelope.",
    "- Dedicated Grip workspace provides undoable closure presets and live measured finger/handle fit using the established regression envelope.\n- Per-instance hand-local grip-centre calibration edits handle X/Y/Z in millimetres, updates diagnostics live, and can reset to the anatomical default.",
)

changelog = Path('AI_CHANGELOG.md')
text = changelog.read_text(encoding='utf-8')
heading = '### ChatGPT — 2026-09-14 — hand-local grip-centre calibration'
entry = r'''

### ChatGPT — 2026-09-14 — hand-local grip-centre calibration

Extended the Grip workspace with per-instance handle-centre calibration. Each hand-attached dumbbell now exposes X/Y/Z in hand-local millimetres. Editing writes `attachment.gripOffset` through the normal Studio document history, regenerates the deterministic clip, and therefore updates both the rendered equipment position and live grip-fit diagnostics immediately. `Reset anatomical centre` removes the override and returns to `anatomicalGripOffset(side)` rather than baking a duplicate default value.

The calibration is deliberately equipment-only: it does not change wrist, elbow, shoulder or finger animation automatically. This makes it suitable for fixing the visual case where a handle sits too deep/shallow in the hand without corrupting an accepted curl motion. Regressions verify custom offsets are undoable, actually drive the resolved dumbbell to the requested hand-local point, and reset back to the implicit anatomical default. The capability roadmap now records grip-centre calibration as implemented.
'''
if heading not in text:
    marker = '## Unreleased\n'
    if marker not in text:
        raise SystemExit('AI_CHANGELOG.md: Unreleased marker missing')
    changelog.write_text(text.replace(marker, marker + entry, 1), encoding='utf-8')

print('Applied hand-local grip-centre calibration')
