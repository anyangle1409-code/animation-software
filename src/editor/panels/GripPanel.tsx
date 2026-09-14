import { useMemo } from 'react';
import { resolveFrame } from '../../animation/pipeline';
import { anatomicalGripOffset } from '../../equipment/attach';
import { GRIP_CLOSURE_PRESETS, measureGripFit, measureTwoHandFit } from '../../equipment/gripDiagnostics';
import { equipmentSocketForInstance } from '../../equipment/library';
import type { Vec3 } from '../../rig/types';
import { FINGERS, type Finger } from '../../rig/boneNames';
import { GRIP_PROFILE_LIST } from '../../exercises/gripProfiles';
import { PoseEvaluation } from '../../rig/skeleton';
import { skeleton, useStudio } from '../store';
import { scanGripWorstCases } from '../gripReview';

export function GripPanel() {
  const exercise = useStudio((state) => state.document.exercise);
  const clip = useStudio((state) => state.document.clip);
  const time = useStudio((state) => state.time);
  const setTime = useStudio((state) => state.setTime);
  const setGripClosure = useStudio((state) => state.setGripClosure);
  const setGripPreset = useStudio((state) => state.setGripPreset);
  const setGripDigitClosure = useStudio((state) => state.setGripDigitClosure);
  const clearGripDigitClosures = useStudio((state) => state.clearGripDigitClosures);
  const setEquipmentGripOffset = useStudio((state) => state.setEquipmentGripOffset);
  const setEquipmentGripRotation = useStudio((state) => state.setEquipmentGripRotation);
  const setTwoHandGripWidth = useStudio((state) => state.setTwoHandGripWidth);
  const setTwoHandGripRoll = useStudio((state) => state.setTwoHandGripRoll);

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

  const wholeRepById = useMemo(
    () => new Map(scanGripWorstCases(skeleton, clip).map((sweep) => [sweep.instanceId, sweep])),
    [clip],
  );

  const twoHandMeasurements = useMemo(() => {
    const evaluation = new PoseEvaluation(skeleton);
    const frame = resolveFrame(skeleton, evaluation, clip, time);
    evaluation.apply(frame.pose);
    return exercise.equipment.instances.flatMap((instance) => {
      if (instance.attachment.mode !== 'hands') return [];
      const transform = frame.equipment.get(instance.id);
      if (!transform) return [];
      const fit = measureTwoHandFit(evaluation, instance, transform);
      const left = equipmentSocketForInstance(instance, instance.attachment.leftSocket);
      const right = equipmentSocketForInstance(instance, instance.attachment.rightSocket);
      if (!fit || !left || !right) return [];
      return [{
        id: instance.id,
        label: instance.label ?? instance.id,
        fit,
        width: Math.hypot(
          right.position.x - left.position.x,
          right.position.y - left.position.y,
          right.position.z - left.position.z,
        ),
        roll: instance.attachment.gripRoll ?? 0,
        hasWidthOverride: Boolean(
          instance.socketOverrides?.[instance.attachment.leftSocket]?.position ||
          instance.socketOverrides?.[instance.attachment.rightSocket]?.position
        ),
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

      <details className="grip-digit-details">
        <summary>Fine-tune individual digits</summary>
        <p className="panel__hint">
          Use these only when one digit needs less or more wrap. Unchanged digits continue to follow
          the global closure above, so the authored grip profile stays deterministic.
        </p>
        {FINGERS.map((finger: Finger) => {
          const overridden = exercise.hands.digitClosure?.[finger];
          const value = overridden ?? exercise.hands.closure;
          return (
            <label className="field" key={finger}>
              <span className="field__label">
                {finger.charAt(0).toUpperCase() + finger.slice(1)} · {Math.round(value * 100)}%
                {overridden !== undefined ? ' · custom' : ''}
              </span>
              <input
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={value}
                onChange={(event) => setGripDigitClosure(finger, Number(event.target.value))}
              />
            </label>
          );
        })}
        <div className="button-row">
          <button
            type="button"
            disabled={!exercise.hands.digitClosure}
            onClick={clearGripDigitClosures}
          >
            Reset all digits to global closure
          </button>
        </div>
      </details>

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
              <h4>Digit reach</h4>
              <dl className="spec-list">
                {FINGERS.map((finger) => {
                  const reach = fit.digitReachUse[finger];
                  return (
                    <div key={`digit-reach-${finger}`} className="spec-list__pair">
                      <dt>{finger.charAt(0).toUpperCase() + finger.slice(1)}</dt>
                      <dd className={reach >= 1 ? 'status-warn' : undefined}>
                        {Math.round(reach * 100)}%
                      </dd>
                    </div>
                  );
                })}
              </dl>
              {wholeRepById.get(id) && (
                <>
                  <h4>Worst points in rep</h4>
                  <div className="button-row grip-worst-points">
                    {FINGERS.map((finger) => {
                      const worst = wholeRepById.get(id)!.digits[finger];
                      return (
                        <button
                          type="button"
                          key={`worst-${id}-${finger}`}
                          className={worst.reachUse >= 1 ? 'status-warn' : undefined}
                          onClick={() => setTime(worst.time)}
                          title={`Jump to ${finger} worst point`}
                        >
                          {finger.charAt(0).toUpperCase() + finger.slice(1)} · {Math.round(worst.reachUse * 100)}% · {worst.time.toFixed(2)}s
                        </button>
                      );
                    })}
                  </div>
                  <p className="panel__note">
                    Frame-by-frame at {clip.fps} fps. Tap a digit to inspect its worst measured frame.
                  </p>
                </>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="panel__empty">
          This exercise has no single-hand cylindrical equipment attachment to measure at the playhead.
        </p>
      )}
      <p className="panel__hint">
        Grip X/Y/Z is the handle centre in hand-local millimetres; orientation is a hand-local Euler calibration in degrees. “Within envelope” and each digit percentage use the same
        contact-reach and wrap geometry as the Studio's grip regression. Whole-rep worst points scan every authored animation frame at the clip FPS. A digit above 100% has exceeded that authored geometric envelope; this is not a literal mesh-penetration, force or injury-safety score.
      </p>


      {twoHandMeasurements.length > 0 && (
        <>
          <h3>Two-hand rigid fit</h3>
          <div className="grip-fit-list">
            {twoHandMeasurements.map(({ id, label, fit, width, roll, hasWidthOverride }) => (
              <div className="grip-fit" key={`two-hand-${id}`}>
                <div className="grip-fit__head">
                  <strong>{label}</strong>
                  <span className={fit.withinEnvelope ? 'status-ok' : 'status-warn'}>
                    {fit.withinEnvelope ? 'Sockets aligned' : 'Calibrate spacing'}
                  </span>
                </div>
                <div className="grip-offset-grid">
                  <label className="field">
                    <span className="field__label">Grip width · cm</span>
                    <input
                      type="number"
                      step={1}
                      min={10}
                      max={200}
                      value={Number((width * 100).toFixed(1))}
                      onChange={(event) => setTwoHandGripWidth(id, Number(event.target.value) / 100)}
                    />
                  </label>
                  <label className="field">
                    <span className="field__label">Bar roll · °</span>
                    <input
                      type="number"
                      step={1}
                      value={Number(roll.toFixed(1))}
                      onChange={(event) => setTwoHandGripRoll(id, Number(event.target.value))}
                    />
                  </label>
                </div>
                <div className="button-row">
                  <button
                    type="button"
                    disabled={!hasWidthOverride}
                    onClick={() => setTwoHandGripWidth(id, null)}
                  >
                    Reset grip width
                  </button>
                  <button
                    type="button"
                    disabled={Math.abs(roll) < 1e-9}
                    onClick={() => setTwoHandGripRoll(id, null)}
                  >
                    Reset roll
                  </button>
                </div>
                <dl className="spec-list">
                  <dt>Left socket error</dt>
                  <dd>{(fit.leftError * 1000).toFixed(1)} mm</dd>
                  <dt>Right socket error</dt>
                  <dd>{(fit.rightError * 1000).toFixed(1)} mm</dd>
                  <dt>Hands separation</dt>
                  <dd>{(fit.targetSeparation * 100).toFixed(1)} cm</dd>
                  <dt>Socket separation</dt>
                  <dd>{(fit.socketSeparation * 100).toFixed(1)} cm</dd>
                </dl>
              </div>
            ))}
          </div>
          <p className="panel__hint">
            Two-hand equipment is always rigid. Grip width moves only the authored contact sockets
            along the item; the solver never scales the bar or moves wrists/shoulders to hide a mismatch.
          </p>
        </>
      )}
    </section>
  );
}
