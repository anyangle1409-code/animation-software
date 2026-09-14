from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected one match, found {count}: {old[:120]!r}')
    file.write_text(text.replace(old, new, 1), encoding='utf-8')


# -------------------------------------------------------------------------
# Pure grip diagnostics. Thresholds mirror the established regression envelope.
# -------------------------------------------------------------------------
Path('src/equipment/gripDiagnostics.ts').write_text(r'''import { Vector3 } from 'three';
import type { BoneName, Side } from '../rig/boneNames';
import type { PoseEvaluation } from '../rig/skeleton';
import type { EquipmentTransform } from './attach';

interface GripContactPoint {
  bone: BoneName;
  along: number;
  reach: number;
}

export interface GripFitMeasurement {
  side: Side;
  /** Largest measured distance as a fraction of that contact's allowed reach. */
  reachUse: number;
  /** Largest angular opening between neighbouring contacts around the handle. */
  widestGapDeg: number;
  /** Complement of the widest gap; useful as an intuitive wrap readout. */
  wrapCoverageDeg: number;
  /** Same geometric envelope used by the established grip regression tests. */
  withinEnvelope: boolean;
}

export const GRIP_CLOSURE_PRESETS = [
  { id: 'loose', label: 'Loose', closure: 0.7 },
  { id: 'training', label: 'Training', closure: 0.85 },
  { id: 'closed', label: 'Closed', closure: 1 },
] as const;

export const gripContactPoints = (side: Side): GripContactPoint[] => [
  { bone: `index_02_${side}` as BoneName, along: 0.5, reach: 0.032 },
  { bone: `index_03_${side}` as BoneName, along: 1, reach: 0.04 },
  { bone: `middle_02_${side}` as BoneName, along: 0.5, reach: 0.032 },
  { bone: `middle_03_${side}` as BoneName, along: 1, reach: 0.04 },
  { bone: `ring_02_${side}` as BoneName, along: 0.5, reach: 0.034 },
  { bone: `pinky_02_${side}` as BoneName, along: 0.5, reach: 0.038 },
  { bone: `thumb_02_${side}` as BoneName, along: 0.5, reach: 0.042 },
  { bone: `thumb_03_${side}` as BoneName, along: 1, reach: 0.032 },
];

const pointOf = (evaluation: PoseEvaluation, bone: BoneName, along: number): Vector3 =>
  along >= 1 ? evaluation.tail(bone, new Vector3()) : evaluation.head(bone, new Vector3());

/**
 * Measure how the authored fingers surround a cylindrical hand-held handle.
 * This is a geometric authoring diagnostic, not a safety or force model.
 */
export function measureGripFit(
  evaluation: PoseEvaluation,
  equipment: EquipmentTransform,
  side: Side,
): GripFitMeasurement {
  const handle = equipment.position;
  const axis = new Vector3(0, 0, 1).applyQuaternion(equipment.quaternion).normalize();
  const up = new Vector3(0, 1, 0).addScaledVector(axis, -axis.y);
  if (up.lengthSq() < 1e-10) up.set(1, 0, 0).addScaledVector(axis, -axis.x);
  up.normalize();
  const across = new Vector3().crossVectors(up, axis).normalize();

  let reachUse = 0;
  const angles: number[] = [];
  for (const point of gripContactPoints(side)) {
    const offset = pointOf(evaluation, point.bone, point.along).sub(handle);
    offset.addScaledVector(axis, -offset.dot(axis));
    reachUse = Math.max(reachUse, offset.length() / point.reach);
    angles.push(Math.atan2(offset.dot(up), offset.dot(across)));
  }

  angles.sort((a, b) => a - b);
  let widest = angles[0] + Math.PI * 2 - angles[angles.length - 1];
  for (let index = 1; index < angles.length; index += 1) {
    widest = Math.max(widest, angles[index] - angles[index - 1]);
  }
  const widestGapDeg = (widest * 180) / Math.PI;
  return {
    side,
    reachUse,
    widestGapDeg,
    wrapCoverageDeg: 360 - widestGapDeg,
    withinEnvelope: reachUse < 1 && widestGapDeg < 170,
  };
}
''', encoding='utf-8')

Path('src/equipment/gripDiagnostics.test.ts').write_text(r'''import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { shoulderPress } from '../exercises/definitions/shoulderPress';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { GRIP_CLOSURE_PRESETS, measureGripFit } from './gripDiagnostics';

const skeleton = canonicalSkeleton;

describe('grip authoring diagnostics', () => {
  it('provides ordered closure presets with the authored curl default represented', () => {
    expect(GRIP_CLOSURE_PRESETS.map((preset) => preset.closure)).toEqual([0.7, 0.85, 1]);
    expect(GRIP_CLOSURE_PRESETS.some((preset) => preset.closure === bicepCurl.hands.closure)).toBe(true);
  });

  it.each([
    ['curl', bicepCurl],
    ['shoulder press', shoulderPress],
  ])('keeps %s inside the measurable grip envelope through the full rep', (_label, exercise) => {
    const clip = generateClip(skeleton, exercise);
    const evaluation = new PoseEvaluation(skeleton);
    for (let index = 0; index <= 12; index += 1) {
      const time = (index / 12) * clip.duration;
      const frame = resolveFrame(skeleton, evaluation, clip, time);
      evaluation.apply(frame.pose);
      for (const side of ['l', 'r'] as const) {
        const equipment = frame.equipment.get(`dumbbell_${side}`);
        expect(equipment).toBeDefined();
        const fit = measureGripFit(evaluation, equipment!, side);
        expect(fit.withinEnvelope, `${side} at ${time.toFixed(2)}s`).toBe(true);
        expect(fit.reachUse).toBeLessThan(1);
        expect(fit.wrapCoverageDeg).toBeGreaterThan(190);
      }
    }
  });
});
''', encoding='utf-8')

# -------------------------------------------------------------------------
# Dedicated hand/grip workspace.
# -------------------------------------------------------------------------
Path('src/editor/panels/GripPanel.tsx').write_text(r'''import { useMemo } from 'react';
import { resolveFrame } from '../../animation/pipeline';
import { GRIP_CLOSURE_PRESETS, measureGripFit } from '../../equipment/gripDiagnostics';
import { PoseEvaluation } from '../../rig/skeleton';
import { skeleton, useStudio } from '../store';

export function GripPanel() {
  const exercise = useStudio((state) => state.document.exercise);
  const clip = useStudio((state) => state.document.clip);
  const time = useStudio((state) => state.time);
  const setGripClosure = useStudio((state) => state.setGripClosure);

  const measurements = useMemo(() => {
    const evaluation = new PoseEvaluation(skeleton);
    const frame = resolveFrame(skeleton, evaluation, clip, time);
    evaluation.apply(frame.pose);
    return exercise.equipment.instances.flatMap((instance) => {
      if (instance.attachment.mode !== 'hand') return [];
      const transform = frame.equipment.get(instance.id);
      if (!transform) return [];
      return [{
        id: instance.id,
        label: instance.label ?? instance.id,
        fit: measureGripFit(evaluation, transform, instance.attachment.side),
      }];
    });
  }, [clip, exercise.equipment.instances, time]);

  return (
    <section className="panel grip-panel">
      <h2>Grip</h2>
      <p className="panel__hint">
        Tune the generated hand closure here. Individual thumb and finger segments remain available
        in Joint → Show individual finger joints for final contact corrections.
      </p>

      <h3>Closure</h3>
      <label className="field">
        <span className="field__label">Finger closure · {Math.round(exercise.hands.closure * 100)}%</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={exercise.hands.closure}
          onChange={(event) => setGripClosure(Number(event.target.value))}
        />
      </label>
      <div className="button-row grip-presets">
        {GRIP_CLOSURE_PRESETS.map((preset) => (
          <button
            type="button"
            key={preset.id}
            className={Math.abs(exercise.hands.closure - preset.closure) < 1e-6 ? 'is-active' : ''}
            onClick={() => setGripClosure(preset.closure)}
          >
            {preset.label} {Math.round(preset.closure * 100)}%
          </button>
        ))}
      </div>
      <p className="panel__note">
        Presets only change deterministic finger closure; they do not move the wrist, equipment or
        accepted arm animation. Changes remain undoable.
      </p>

      <h3>Current handle fit</h3>
      {measurements.length > 0 ? (
        <div className="grip-fit-list">
          {measurements.map(({ id, label, fit }) => (
            <div className="grip-fit" key={id}>
              <div className="grip-fit__head">
                <strong>{label}</strong>
                <span className={fit.withinEnvelope ? 'status-ok' : 'status-warn'}>
                  {fit.withinEnvelope ? 'Within envelope' : 'Review fit'}
                </span>
              </div>
              <dl className="spec-list">
                <dt>Contact reach used</dt>
                <dd>{Math.round(fit.reachUse * 100)}%</dd>
                <dt>Wrap coverage</dt>
                <dd>{fit.wrapCoverageDeg.toFixed(1)}°</dd>
                <dt>Largest open gap</dt>
                <dd>{fit.widestGapDeg.toFixed(1)}°</dd>
              </dl>
            </div>
          ))}
        </div>
      ) : (
        <p className="panel__empty">
          This exercise has no single-hand cylindrical equipment attachment to measure at the playhead.
        </p>
      )}
      <p className="panel__hint">
        “Within envelope” uses the same finger reach and wrap geometry as the Studio's grip regression.
        It is an animation-fit diagnostic, not a force or injury-safety score.
      </p>
    </section>
  );
}
''', encoding='utf-8')

# Add Grip tab beside Joint/IK/Character.
replace_once(
    'src/editor/App.tsx',
    "import { ComparisonPanel } from './panels/ComparisonPanel';",
    "import { ComparisonPanel } from './panels/ComparisonPanel';\nimport { GripPanel } from './panels/GripPanel';",
)
replace_once(
    'src/editor/App.tsx',
    "type LeftTab = 'joint' | 'ik' | 'character';",
    "type LeftTab = 'joint' | 'grip' | 'ik' | 'character';",
)
replace_once(
    'src/editor/App.tsx',
    "            <button\n              type=\"button\"\n              className={leftTab === 'ik' ? 'is-active' : ''}",
    "            <button\n              type=\"button\"\n              className={leftTab === 'grip' ? 'is-active' : ''}\n              onClick={() => setLeftTab('grip')}\n            >\n              Grip\n            </button>\n            <button\n              type=\"button\"\n              className={leftTab === 'ik' ? 'is-active' : ''}",
)
replace_once(
    'src/editor/App.tsx',
    "            {leftTab === 'joint' && <JointPanel />}\n            {leftTab === 'ik' && <IKPanel />}",
    "            {leftTab === 'joint' && <JointPanel />}\n            {leftTab === 'grip' && <GripPanel />}\n            {leftTab === 'ik' && <IKPanel />}",
)

styles = Path('src/editor/styles.css')
styles.write_text(styles.read_text(encoding='utf-8') + r'''

/* ---------- hand / grip workspace ---------- */

.grip-presets button.is-active {
  border-color: var(--accent);
  box-shadow: inset 0 0 0 1px var(--accent);
}

.grip-fit-list {
  display: grid;
  gap: 8px;
}

.grip-fit {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel-2);
  padding: 9px;
}

.grip-fit__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: baseline;
  margin-bottom: 6px;
  font-size: 11px;
}

.status-ok {
  color: #76d6a7;
}

.status-warn {
  color: #f0bd69;
}
''', encoding='utf-8')

# -------------------------------------------------------------------------
# Roadmap and Claude changelog.
# -------------------------------------------------------------------------
replace_once(
    'docs/STUDIO_CAPABILITY_ROADMAP.md',
    "- Individual finger/thumb joint authoring remains available through the same joint workspace.",
    "- Individual finger/thumb joint authoring remains available through the same joint workspace.\n- Dedicated Grip workspace provides undoable closure presets and live measured finger/handle fit using the established regression envelope.",
)

changelog = Path('AI_CHANGELOG.md')
text = changelog.read_text(encoding='utf-8')
heading = '### ChatGPT — 2026-09-14 — measurable hand/grip workspace'
entry = r'''

### ChatGPT — 2026-09-14 — measurable hand/grip workspace

Added a dedicated Grip tab for the curl/hand-authoring workflow. It keeps the existing deterministic finger generator and existing 30-joint fine-hand editing rather than introducing a second hand rig. The panel exposes an exact closure slider plus Loose 70%, Training 85%, and Closed 100% quick presets; all use the existing `setGripClosure` document edit, regenerate deterministically and remain undoable.

Added `src/equipment/gripDiagnostics.ts`, which measures each hand-held cylindrical handle against the same geometric concepts already enforced by the grip regression: maximum finger/thumb reach use and angular enclosure around the handle. The UI reports contact reach used, wrap coverage, largest open gap, and an explicit `Within envelope` / `Review fit` authoring status. This is intentionally described as animation-fit geometry, not a force or injury-safety score. New regressions confirm the preset set includes the curl's authored 85% default and that both the dumbbell curl and shoulder press remain inside the measurable envelope across 13 samples per repetition. The capability roadmap now records the Grip workspace as implemented.
'''
if heading not in text:
    marker = '## Unreleased\n'
    if marker not in text:
        raise SystemExit('AI_CHANGELOG.md: Unreleased marker missing')
    changelog.write_text(text.replace(marker, marker + entry, 1), encoding='utf-8')

print('Applied measurable grip workspace')
