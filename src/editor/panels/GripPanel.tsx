import { useMemo } from 'react';
import { resolveFrame } from '../../animation/pipeline';
import { anatomicalGripOffset } from '../../equipment/attach';
import { GRIP_CLOSURE_PRESETS, measureGripFit } from '../../equipment/gripDiagnostics';
import type { Vec3 } from '../../rig/types';
import { GRIP_PROFILE_LIST } from '../../exercises/gripProfiles';
import { PoseEvaluation } from '../../rig/skeleton';
import { skeleton, useStudio } from '../store';

export function GripPanel() {
  const exercise = useStudio((state) => state.document.exercise);
  const clip = useStudio((state) => state.document.clip);
  const time = useStudio((state) => state.time);
  const setGripClosure = useStudio((state) => state.setGripClosure);
  const setGripPreset = useStudio((state) => state.setGripPreset);
  const setEquipmentGripOffset = useStudio((state) => state.setEquipmentGripOffset);
  const setEquipmentGripRotation = useStudio((state) => state.setEquipmentGripRotation);

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
        side: instance.attachment.side,
        offset: instance.attachment.gripOffset ?? anatomicalGripOffset(instance.attachment.side),
        isCustomOffset: Boolean(instance.attachment.gripOffset),
        rotation: instance.attachment.gripRotation ?? { x: 0, y: 0, z: 0 },
        isCustomRotation: Boolean(instance.attachment.gripRotation),
        fit: measureGripFit(evaluation, transform, instance.attachment.side),
      }];
    });
  }, [clip, exercise.equipment.instances, time]);

  const updateOffset = (id: string, current: Vec3, axis: keyof Vec3, millimetres: number) => {
    setEquipmentGripOffset(id, { ...current, [axis]: millimetres / 1000 });
  };

  const updateRotation = (id: string, current: Vec3, axis: keyof Vec3, degrees: number) => {
    setEquipmentGripRotation(id, { ...current, [axis]: degrees });
  };

  return (
    <section className="panel grip-panel">
      <h2>Grip</h2>
      <p className="panel__hint">
        Tune the generated hand closure here. Individual thumb and finger segments remain available
        in Joint → Show individual finger joints for final contact corrections.
      </p>

      <h3>Hand shape</h3>
      <label className="field">
        <span className="field__label">Grip profile</span>
        <select
          value={exercise.hands.gripPreset ?? exercise.hands.grip}
          onChange={(event) => {
            const value = event.target.value as typeof exercise.hands.grip;
            setGripPreset(value === exercise.hands.grip ? null : value);
          }}
        >
          {GRIP_PROFILE_LIST.map((profile) => (
            <option key={profile.id} value={profile.id}>{profile.label}</option>
          ))}
        </select>
      </label>
      <p className="panel__note">
        The exercise still records its semantic grip as <strong>{exercise.hands.grip}</strong>. This
        selector only overrides the generated finger/thumb shape for authoring.
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
          {measurements.map(({ id, label, offset, isCustomOffset, rotation, isCustomRotation, fit }) => (
            <div className="grip-fit" key={id}>
              <div className="grip-fit__head">
                <strong>{label}</strong>
                <span className={fit.withinEnvelope ? 'status-ok' : 'status-warn'}>
                  {fit.withinEnvelope ? 'Within envelope' : 'Review fit'}
                </span>
              </div>
              <div className="grip-offset-grid">
                {(['x', 'y', 'z'] as const).map((axis) => (
                  <label className="field" key={axis}>
                    <span className="field__label">Grip {axis.toUpperCase()} · mm</span>
                    <input
                      type="number"
                      step={1}
                      value={Math.round(offset[axis] * 1000)}
                      onChange={(event) => updateOffset(id, offset, axis, Number(event.target.value))}
                    />
                  </label>
                ))}
              </div>
              <h4>Handle orientation</h4>
              <div className="grip-offset-grid">
                {(['x', 'y', 'z'] as const).map((axis) => (
                  <label className="field" key={`rotation-${axis}`}>
                    <span className="field__label">Grip {axis.toUpperCase()} · °</span>
                    <input
                      type="number"
                      step={1}
                      value={Number(rotation[axis].toFixed(1))}
                      onChange={(event) => updateRotation(id, rotation, axis, Number(event.target.value))}
                    />
                  </label>
                ))}
              </div>
              <div className="button-row">
                <button
                  type="button"
                  disabled={!isCustomOffset}
                  onClick={() => setEquipmentGripOffset(id, null)}
                >
                  Reset anatomical centre
                </button>
                <button
                  type="button"
                  disabled={!isCustomRotation}
                  onClick={() => setEquipmentGripRotation(id, null)}
                >
                  Reset orientation
                </button>
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
        Grip X/Y/Z is the handle centre in hand-local millimetres; orientation is a hand-local Euler calibration in degrees. “Within envelope” uses the same
        finger reach and wrap geometry as the Studio's grip regression. It is an animation-fit diagnostic,
        not a force or injury-safety score.
      </p>
    </section>
  );
}
