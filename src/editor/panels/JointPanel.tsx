import { useMemo } from 'react';
import type { BoneName } from '../../rig/boneNames';
import { boneLabel, isFingerBone } from '../../rig/boneNames';
import { AXES } from '../../rig/types';
import type { Axis } from '../../rig/types';
import { sampleClip } from '../../animation/clip';
import { toDeg, toRad } from '../../core/math';
import { skeleton, useStudio } from '../store';

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
  const copyPose = useStudio((state) => state.copyPose);
  const pastePose = useStudio((state) => state.pastePose);
  const mirrorCurrentPose = useStudio((state) => state.mirrorCurrentPose);
  const mirrorSide = useStudio((state) => state.mirrorSide);
  const hasClipboard = useStudio((state) => state.clipboard !== null);

  const pose = useMemo(() => sampleClip(clip, time).pose, [clip, time]);
  const rotation = selected ? pose.rotations[selected] : undefined;

  const bones = useMemo(
    () => skeleton.names.filter((name) => name !== 'root' && !isFingerBone(name)),
    [],
  );

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

      {selected ? (
        <>
          <div className="panel__hint">
            Rotations apply to the keyframe under the playhead; editing between
            keys creates one.
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
