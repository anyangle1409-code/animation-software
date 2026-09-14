import { useMemo, useState } from 'react';
import type { BoneName } from '../../rig/boneNames';
import { boneLabel, isFingerBone } from '../../rig/boneNames';
import { AXES } from '../../rig/types';
import type { Axis } from '../../rig/types';
import { sortedKeyframes, sampleClip } from '../../animation/clip';
import { EASING_LABELS } from '../../animation/easing';
import type { EasingKind, PhaseJointTiming } from '../../exercises/types';
import { toDeg, toRad } from '../../core/math';
import { skeleton, useStudio } from '../store';
import { measureJointMotion } from '../motionDiagnostics';

/** Numeric, limit-aware control for one joint axis. */
function AxisRow({ bone, axis, value }: { bone: BoneName; axis: Axis; value: number }) {
  const setBoneAxis = useStudio((state) => state.setBoneAxis);
  const limit = skeleton.bone(bone).definition.limits[axis];

  if (!limit) {
    return (
      <div className="axis axis--locked">
        <span className="axis__name">{axis.toUpperCase()}</span>
        <span className="axis__locked">Locked — this joint has no {axis} axis</span>
      </div>
    );
  }

  const degrees = toDeg(value);
  const direction = degrees >= 0 ? limit.positive : limit.negative;

  return (
    <div className="axis">
      <div className="axis__head">
        <span className="axis__name">{axis.toUpperCase()}</span>
        <span className="axis__direction">{direction}</span>
        <input
          className="axis__number"
          type="number"
          step={1}
          min={limit.min}
          max={limit.max}
          value={Number(degrees.toFixed(1))}
          onChange={(event) => setBoneAxis(bone, axis, toRad(Number(event.target.value)))}
        />
        <span className="axis__unit">°</span>
      </div>
      <input
        className="axis__slider"
        type="range"
        min={limit.min}
        max={limit.max}
        step={0.5}
        value={degrees}
        onChange={(event) => setBoneAxis(bone, axis, toRad(Number(event.target.value)))}
      />
      <div className="axis__range">
        <span>
          {limit.min}° {limit.negative}
        </span>
        <span>
          {limit.positive} {limit.max}°
        </span>
      </div>
    </div>
  );
}

export function JointPanel() {
  const selected = useStudio((state) => state.selection.bone);
  const selectBone = useStudio((state) => state.selectBone);
  const clip = useStudio((state) => state.document.clip);
  const time = useStudio((state) => state.time);
  const setTime = useStudio((state) => state.setTime);
  const copyPose = useStudio((state) => state.copyPose);
  const pastePose = useStudio((state) => state.pastePose);
  const mirrorCurrentPose = useStudio((state) => state.mirrorCurrentPose);
  const mirrorSide = useStudio((state) => state.mirrorSide);
  const setJointTiming = useStudio((state) => state.setJointTiming);
  const hasClipboard = useStudio((state) => state.clipboard !== null);
  const [showFingerJoints, setShowFingerJoints] = useState(false);

  const pose = useMemo(() => sampleClip(clip, time).pose, [clip, time]);
  const rotation = selected ? pose.rotations[selected] : undefined;
  const motion = useMemo(
    () => (selected ? measureJointMotion(clip, selected) : null),
    [clip, selected],
  );
  const keyframes = useMemo(() => sortedKeyframes(clip), [clip]);
  const segmentIndex = useMemo(() => {
    let index = 0;
    for (let i = 0; i < keyframes.length; i += 1) {
      if (keyframes[i].time <= time + 1e-9) index = i;
    }
    return index;
  }, [keyframes, time]);
  const segmentFrom = keyframes[segmentIndex];
  const segmentTo = keyframes[segmentIndex + 1];
  const timing = selected && segmentFrom ? segmentFrom.jointTiming?.[selected] : undefined;

  const bones = useMemo(
    () =>
      skeleton.names.filter(
        (name) =>
          name !== 'root' &&
          (showFingerJoints || !isFingerBone(name) || name === selected),
      ),
    [selected, showFingerJoints],
  );

  const updateTiming = (patch: Partial<PhaseJointTiming>) => {
    if (!selected || !segmentFrom) return;
    setJointTiming(segmentFrom.id, selected, {
      delay: timing?.delay ?? 0,
      finish: timing?.finish ?? 1,
      ...(timing?.easing ? { easing: timing.easing } : {}),
      ...patch,
    });
  };

  return (
    <section className="panel">
      <h2>Joint</h2>

      <label className="field">
        <span className="field__label">Selected bone</span>
        <select
          value={selected ?? ''}
          onChange={(event) => selectBone((event.target.value || null) as BoneName | null)}
        >
          <option value="">— none —</option>
          {bones.map((name) => (
            <option key={name} value={name}>
              {boneLabel(name)}
            </option>
          ))}
        </select>
      </label>

      <label className="field field--check">
        <input
          type="checkbox"
          checked={showFingerJoints}
          onChange={(event) => setShowFingerJoints(event.target.checked)}
        />
        <span>Show individual finger joints</span>
      </label>
      <p className="panel__hint">
        Fine hand mode exposes all 30 thumb/finger segments. They use the same anatomical limits,
        keyframing, undo/redo, mirroring and Focus selected camera as the larger joints.
      </p>

      {selected ? (
        <>
          <div className="panel__hint">
            Rotations apply to the keyframe under the playhead; editing between keys creates one.
          </div>
          {AXES.map((axis) => (
            <AxisRow key={axis} bone={selected} axis={axis} value={rotation?.[axis] ?? 0} />
          ))}
        </>
      ) : (
        <p className="panel__empty">
          Click a joint in the viewport, or choose one above, to rotate it.
        </p>
      )}

      <h3>Motion quality</h3>
      {selected && motion ? (
        <div className="joint-motion-diagnostic">
          <p className="panel__hint">
            Frame-by-frame at {motion.fps} fps using shortest-path joint angles. These are animation
            diagnostics, not force or injury thresholds.
          </p>
          <dl className="spec-list">
            <dt>Highest angular speed</dt>
            <dd>
              {motion.maxSpeed.value.toFixed(1)}°/s · {motion.maxSpeed.axis.toUpperCase()} · {motion.maxSpeed.time.toFixed(2)}s
            </dd>
            <dt>Highest angular acceleration</dt>
            <dd>
              {motion.maxAcceleration.value.toFixed(0)}°/s² · {motion.maxAcceleration.axis.toUpperCase()} · {motion.maxAcceleration.time.toFixed(2)}s
            </dd>
          </dl>
          <div className="button-row">
            <button type="button" onClick={() => setTime(motion.maxSpeed.time)}>
              Jump to fastest frame
            </button>
            <button type="button" onClick={() => setTime(motion.maxAcceleration.time)}>
              Jump to sharpest change
            </button>
          </div>
          <details>
            <summary>Per-axis motion</summary>
            <dl className="spec-list">
              {AXES.map((axis) => (
                <div className="spec-list__pair" key={`motion-${axis}`}>
                  <dt>{axis.toUpperCase()}</dt>
                  <dd>
                    {motion.axes[axis].maxSpeedDegPerSec.toFixed(1)}°/s · {motion.axes[axis].maxAccelerationDegPerSec2.toFixed(0)}°/s²
                  </dd>
                </div>
              ))}
            </dl>
          </details>
        </div>
      ) : (
        <p className="panel__empty">Select a joint to inspect its motion through the full rep.</p>
      )}

      <h3>Segment timing</h3>
      {selected && segmentFrom && segmentTo ? (
        <div className="joint-timing">
          <p className="panel__hint">
            {segmentFrom.label ?? `${segmentFrom.time.toFixed(2)}s`} →{' '}
            {segmentTo.label ?? `${segmentTo.time.toFixed(2)}s`}. Timing affects only{' '}
            <strong>{boneLabel(selected)}</strong> in this segment.
          </p>
          <label className="field field--check">
            <input
              type="checkbox"
              checked={Boolean(timing)}
              onChange={(event) =>
                setJointTiming(
                  segmentFrom.id,
                  selected,
                  event.target.checked ? { delay: 0, finish: 1 } : null,
                )
              }
            />
            <span>Custom timing for this joint</span>
          </label>
          {timing && (
            <>
              <label className="field">
                <span className="field__label">
                  Start delay · {Math.round((timing.delay ?? 0) * 100)}%
                </span>
                <input
                  type="range"
                  min={0}
                  max={timing.finish ?? 1}
                  step={0.01}
                  value={timing.delay ?? 0}
                  onChange={(event) => updateTiming({ delay: Number(event.target.value) })}
                />
              </label>
              <label className="field">
                <span className="field__label">
                  Finish · {Math.round((timing.finish ?? 1) * 100)}%
                </span>
                <input
                  type="range"
                  min={timing.delay ?? 0}
                  max={1}
                  step={0.01}
                  value={timing.finish ?? 1}
                  onChange={(event) => updateTiming({ finish: Number(event.target.value) })}
                />
              </label>
              <label className="field">
                <span className="field__label">Joint easing</span>
                <select
                  value={timing.easing ?? ''}
                  onChange={(event) =>
                    updateTiming({
                      easing: (event.target.value || undefined) as EasingKind | undefined,
                    })
                  }
                >
                  <option value="">Use phase easing ({EASING_LABELS[segmentFrom.easing]})</option>
                  {Object.entries(EASING_LABELS).map(([kind, label]) => (
                    <option key={kind} value={kind}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <p className="panel__note">
                Use this for sequencing secondary joints—such as allowing the elbow to lead before
                the shoulder joins a curl—without inserting stop/start keyframes.
              </p>
            </>
          )}
        </div>
      ) : (
        <p className="panel__empty">
          {selected
            ? 'Move the playhead before the final keyframe to edit timing for a segment.'
            : 'Select a joint to edit its timing through the current segment.'}
        </p>
      )}

      <h3>Pose</h3>
      <div className="button-row">
        <button type="button" onClick={copyPose}>
          Copy pose
        </button>
        <button type="button" onClick={pastePose} disabled={!hasClipboard}>
          Paste pose
        </button>
      </div>
      <div className="button-row">
        <button type="button" onClick={mirrorCurrentPose}>
          Mirror pose
        </button>
        <button type="button" onClick={() => mirrorSide('l')}>
          Left → right
        </button>
        <button type="button" onClick={() => mirrorSide('r')}>
          Right → left
        </button>
      </div>
    </section>
  );
}
