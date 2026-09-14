from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected one match, found {count}: {old[:100]!r}')
    file.write_text(text.replace(old, new, 1), encoding='utf-8')


# -------------------------------------------------------------------------
# Pure playback helpers: loop-range normalisation and deterministic advance.
# -------------------------------------------------------------------------
Path('src/editor/playback.ts').write_text(r'''import { clamp } from '../core/math';

export interface LoopRange {
  start: number;
  end: number;
}

/**
 * Clamp an editor loop range to the clip and guarantee at least one frame.
 * Loop ranges are playback state only; they never alter the exported clip.
 */
export function normalizeLoopRange(
  range: LoopRange | null,
  duration: number,
  fps: number,
): LoopRange | null {
  if (!range || !Number.isFinite(range.start) || !Number.isFinite(range.end)) return null;
  const safeDuration = Math.max(0, duration);
  if (safeDuration <= 0) return null;
  const frame = Math.min(safeDuration, 1 / Math.max(1, fps));
  let start = clamp(Math.min(range.start, range.end), 0, safeDuration);
  let end = clamp(Math.max(range.start, range.end), 0, safeDuration);
  if (end - start < frame) {
    if (start + frame <= safeDuration) end = start + frame;
    else {
      end = safeDuration;
      start = Math.max(0, end - frame);
    }
  }
  return { start, end };
}

export interface PlaybackAdvance {
  time: number;
  ended: boolean;
}

/** Advance positive playback without coupling the math to React/Three. */
export function advancePlaybackTime(
  time: number,
  elapsed: number,
  duration: number,
  loop: boolean,
  range: LoopRange | null,
): PlaybackAdvance {
  const step = Math.max(0, elapsed);
  const safeDuration = Math.max(0, duration);

  if (loop && range) {
    const start = clamp(range.start, 0, safeDuration);
    const end = clamp(range.end, start, safeDuration);
    const span = end - start;
    if (span > 1e-9) {
      const base = time < start || time >= end ? start : time;
      const offset = ((base + step - start) % span + span) % span;
      return { time: start + offset, ended: false };
    }
  }

  const next = Math.max(0, time) + step;
  if (next >= safeDuration) {
    if (loop && safeDuration > 1e-9) return { time: next % safeDuration, ended: false };
    return { time: safeDuration, ended: true };
  }
  return { time: next, ended: false };
}
''', encoding='utf-8')

Path('src/editor/playback.test.ts').write_text(r'''import { describe, expect, it } from 'vitest';
import { advancePlaybackTime, normalizeLoopRange } from './playback';

describe('editor playback ranges', () => {
  it('sorts and clamps a range while preserving at least one frame', () => {
    expect(normalizeLoopRange({ start: 4, end: 1 }, 5, 30)).toEqual({ start: 1, end: 4 });
    const tiny = normalizeLoopRange({ start: 5, end: 5 }, 5, 30);
    expect(tiny?.end).toBe(5);
    expect((tiny?.end ?? 0) - (tiny?.start ?? 0)).toBeCloseTo(1 / 30, 8);
  });

  it('loops only inside the custom range when loop playback is enabled', () => {
    const range = { start: 1, end: 2 };
    expect(advancePlaybackTime(1.9, 0.25, 5, true, range)).toEqual({ time: 1.15, ended: false });
    expect(advancePlaybackTime(4, 0.1, 5, true, range)).toEqual({ time: 1.1, ended: false });
  });

  it('ignores a custom range when looping is disabled', () => {
    expect(advancePlaybackTime(1.9, 0.25, 5, false, { start: 1, end: 2 })).toEqual({
      time: 2.15,
      ended: false,
    });
  });

  it('preserves the full-clip loop and stop behaviours', () => {
    expect(advancePlaybackTime(4.9, 0.25, 5, true, null)).toEqual({ time: 0.15, ended: false });
    expect(advancePlaybackTime(4.9, 0.25, 5, false, null)).toEqual({ time: 5, ended: true });
  });
});
''', encoding='utf-8')

# -------------------------------------------------------------------------
# Store: playback range + per-bone timing authoring.
# -------------------------------------------------------------------------
replace_once(
    'src/editor/store.ts',
    "import type { ExerciseDefinition, Tempo } from '../exercises/types';",
    "import type { ExerciseDefinition, PhaseJointTiming, Tempo } from '../exercises/types';",
)
replace_once(
    'src/editor/store.ts',
    "import type { CameraPresetId } from '../viewer/cameraTypes';",
    "import type { CameraPresetId } from '../viewer/cameraTypes';\nimport { normalizeLoopRange, type LoopRange } from './playback';",
)
replace_once(
    'src/editor/store.ts',
    "  loop: boolean;\n  speed: number;",
    "  loop: boolean;\n  speed: number;\n  loopRange: LoopRange | null;",
)
replace_once(
    'src/editor/store.ts',
    "  setLoop: (loop: boolean) => void;\n  setSpeed: (speed: number) => void;",
    "  setLoop: (loop: boolean) => void;\n  setSpeed: (speed: number) => void;\n  setLoopRange: (range: LoopRange | null) => void;",
)
replace_once(
    'src/editor/store.ts',
    "  setKeyframeEasing: (id: string, easing: Keyframe['easing']) => void;",
    "  setKeyframeEasing: (id: string, easing: Keyframe['easing']) => void;\n  setJointTiming: (id: string, bone: BoneName, timing: PhaseJointTiming | null) => void;",
)
replace_once(
    'src/editor/store.ts',
    "    loop: true,\n    speed: 1,",
    "    loop: true,\n    speed: 1,\n    loopRange: null,",
)
replace_once(
    'src/editor/store.ts',
    "    setLoop: (loop) => set({ loop }),\n    setSpeed: (speed) => set({ speed }),",
    """    setLoop: (loop) => set({ loop }),
    setSpeed: (speed) => set({ speed }),
    setLoopRange: (range) => {
      const clip = get().document.clip;
      set({ loopRange: normalizeLoopRange(range, clip.duration, clip.fps) });
    },""",
)
replace_once(
    'src/editor/store.ts',
    "        playing: false,\n        validation: null,",
    "        playing: false,\n        loopRange: null,\n        validation: null,",
)
replace_once(
    'src/editor/store.ts',
    """    setKeyframeEasing: (id, easing) =>
      editClip((clip) => ({
        ...clip,
        keyframes: clip.keyframes.map((frame) => (frame.id === id ? { ...frame, easing } : frame)),
      })),
""",
    """    setKeyframeEasing: (id, easing) =>
      editClip((clip) => ({
        ...clip,
        keyframes: clip.keyframes.map((frame) => (frame.id === id ? { ...frame, easing } : frame)),
      })),

    setJointTiming: (id, bone, timing) =>
      editClip((clip) => ({
        ...clip,
        keyframes: clip.keyframes.map((frame) => {
          if (frame.id !== id) return frame;
          const jointTiming: Partial<Record<BoneName, PhaseJointTiming>> = {
            ...(frame.jointTiming ?? {}),
          };
          if (!timing) delete jointTiming[bone];
          else {
            const delay = Math.max(0, Math.min(1, timing.delay ?? 0));
            const finish = Math.max(delay, Math.max(0, Math.min(1, timing.finish ?? 1)));
            jointTiming[bone] = {
              delay,
              finish,
              ...(timing.easing ? { easing: timing.easing } : {}),
            };
          }
          return {
            ...frame,
            jointTiming: Object.keys(jointTiming).length > 0 ? jointTiming : undefined,
          };
        }),
      })),
""",
)
replace_once(
    'src/editor/store.ts',
    """    setDuration: (duration) => {
      const next = Math.max(0.2, duration);
      editClip((clip) => {
        const scale = next / clip.duration;
        return {
          ...clip,
          duration: next,
          keyframes: clip.keyframes.map((frame) => ({
            ...frame,
            time: Math.round(frame.time * scale * 1e6) / 1e6,
          })),
        };
      });
      set({ time: Math.min(get().time, next) });
    },
""",
    """    setDuration: (duration) => {
      const previous = get().document.clip;
      const next = Math.max(0.2, duration);
      editClip((clip) => {
        const scale = next / clip.duration;
        return {
          ...clip,
          duration: next,
          keyframes: clip.keyframes.map((frame) => ({
            ...frame,
            time: Math.round(frame.time * scale * 1e6) / 1e6,
          })),
        };
      });
      const range = get().loopRange;
      const scale = next / previous.duration;
      set({
        time: Math.min(get().time, next),
        loopRange: range
          ? normalizeLoopRange(
              { start: range.start * scale, end: range.end * scale },
              next,
              previous.fps,
            )
          : null,
      });
    },
""",
)

# -------------------------------------------------------------------------
# Viewport playback uses the pure helper, preserving old full-clip behaviour.
# -------------------------------------------------------------------------
replace_once(
    'src/viewer/Viewport.tsx',
    "import { resolveCamera } from './cameras';",
    "import { resolveCamera } from './cameras';\nimport { advancePlaybackTime } from '../editor/playback';",
)
replace_once(
    'src/viewer/Viewport.tsx',
    """    let time = store.time;
    if (store.playing) {
      time += Math.min(delta, 0.1) * store.speed;
      if (time >= clip.duration) {
        if (store.loop) time %= clip.duration;
        else {
          time = clip.duration;
          store.pause();
        }
      }
      store.setTime(time);
    }
""",
    """    let time = store.time;
    if (store.playing) {
      const advanced = advancePlaybackTime(
        time,
        Math.min(delta, 0.1) * store.speed,
        clip.duration,
        store.loop,
        store.loopRange,
      );
      time = advanced.time;
      if (advanced.ended) store.pause();
      store.setTime(time);
    }
""",
)

# -------------------------------------------------------------------------
# Timeline: loop In/Out controls and visual range overlay.
# -------------------------------------------------------------------------
Path('src/editor/Timeline.tsx').write_text(r'''import { useMemo, useRef } from 'react';
import { EASING_LABELS } from '../animation/easing';
import type { EasingKind } from '../exercises/types';
import { phaseBoundaries } from '../animation/generate';
import { sortedKeyframes } from '../animation/clip';
import { useStudio } from './store';

const PHASE_COLOURS: Record<string, string> = {
  concentric: '#2f5d4a',
  eccentric: '#3a4a6b',
  isometric: '#4a4030',
};

export function Timeline() {
  const clip = useStudio((state) => state.document.clip);
  const exercise = useStudio((state) => state.document.exercise);
  const time = useStudio((state) => state.time);
  const setTime = useStudio((state) => state.setTime);
  const playing = useStudio((state) => state.playing);
  const pause = useStudio((state) => state.pause);
  const togglePlay = useStudio((state) => state.togglePlay);
  const loop = useStudio((state) => state.loop);
  const setLoop = useStudio((state) => state.setLoop);
  const loopRange = useStudio((state) => state.loopRange);
  const setLoopRange = useStudio((state) => state.setLoopRange);
  const speed = useStudio((state) => state.speed);
  const setSpeed = useStudio((state) => state.setSpeed);
  const setKeyframe = useStudio((state) => state.setKeyframe);
  const deleteKeyframe = useStudio((state) => state.deleteKeyframe);
  const setKeyframeEasing = useStudio((state) => state.setKeyframeEasing);
  const setDuration = useStudio((state) => state.setDuration);

  const track = useRef<HTMLDivElement | null>(null);
  const keyframes = useMemo(() => sortedKeyframes(clip), [clip]);
  const phases = useMemo(() => phaseBoundaries(exercise), [exercise]);
  const current = keyframes.find((frame) => Math.abs(frame.time - time) < 0.5 / clip.fps);
  const currentFrame = Math.round(time * clip.fps);
  const totalFrames = Math.round(clip.duration * clip.fps);
  const oneFrame = 1 / clip.fps;

  const stepFrame = (frames: number) => {
    pause();
    setTime(time + frames / clip.fps);
  };

  const setLoopIn = () => {
    const end = Math.max(loopRange?.end ?? clip.duration, time + oneFrame);
    setLoopRange({ start: time, end });
    setLoop(true);
  };

  const setLoopOut = () => {
    const start = Math.min(loopRange?.start ?? 0, time - oneFrame);
    setLoopRange({ start, end: time });
    setLoop(true);
  };

  const scrub = (event: React.PointerEvent<HTMLDivElement>) => {
    const element = track.current;
    if (!element) return;
    const bounds = element.getBoundingClientRect();
    const ratio = (event.clientX - bounds.left) / bounds.width;
    setTime(Math.max(0, Math.min(1, ratio)) * clip.duration);
  };

  return (
    <section className="timeline">
      <div className="timeline__controls">
        <button type="button" className="primary" onClick={togglePlay}>
          {playing ? 'Pause' : 'Play'}
        </button>
        <button
          type="button"
          onClick={() => stepFrame(-1)}
          disabled={time <= 0}
          title="Previous animation frame (Left Arrow)"
        >
          ‹ Frame
        </button>
        <button
          type="button"
          onClick={() => stepFrame(1)}
          disabled={time >= clip.duration}
          title="Next animation frame (Right Arrow)"
        >
          Frame ›
        </button>
        <span className="timeline__time">
          {time.toFixed(2)}s / {clip.duration.toFixed(2)}s
        </span>
        <span className="timeline__time">
          {currentFrame}f / {totalFrames}f
        </span>
        <label className="field field--inline">
          <span className="field__label">Speed</span>
          <select value={speed} onChange={(event) => setSpeed(Number(event.target.value))}>
            {[0.25, 0.5, 1, 1.5, 2].map((value) => (
              <option key={value} value={value}>
                {value}×
              </option>
            ))}
          </select>
        </label>
        <label className="field field--inline field--check">
          <input type="checkbox" checked={loop} onChange={(event) => setLoop(event.target.checked)} />
          <span>Loop</span>
        </label>
        <div className="timeline__range-controls" aria-label="Loop range controls">
          <button type="button" onClick={setLoopIn} title="Set loop start to playhead">
            Set In
          </button>
          <button type="button" onClick={setLoopOut} title="Set loop end to playhead">
            Set Out
          </button>
          <button type="button" onClick={() => setLoopRange(null)} disabled={!loopRange}>
            Clear range
          </button>
          {loopRange && (
            <span className="timeline__range-readout">
              {loopRange.start.toFixed(2)}–{loopRange.end.toFixed(2)}s
            </span>
          )}
        </div>
        <label className="field field--inline">
          <span className="field__label">Duration</span>
          <input
            type="number"
            min={0.5}
            max={30}
            step={0.1}
            value={clip.duration}
            onChange={(event) => setDuration(Number(event.target.value))}
          />
        </label>

        <div className="timeline__spacer" />

        <button type="button" onClick={setKeyframe}>
          Set keyframe
        </button>
        <button
          type="button"
          onClick={() => current && deleteKeyframe(current.id)}
          disabled={!current || keyframes.length <= 2}
        >
          Delete keyframe
        </button>
        {current && (
          <label className="field field--inline">
            <span className="field__label">Easing</span>
            <select
              value={current.easing}
              onChange={(event) =>
                setKeyframeEasing(current.id, event.target.value as EasingKind)
              }
            >
              {Object.entries(EASING_LABELS).map(([kind, label]) => (
                <option key={kind} value={kind}>
                  {label}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      <div
        className="timeline__track"
        ref={track}
        onPointerDown={(event) => {
          event.currentTarget.setPointerCapture(event.pointerId);
          scrub(event);
        }}
        onPointerMove={(event) => {
          if (event.buttons === 1) scrub(event);
        }}
      >
        {phases.map(({ phase, start, end }) => (
          <div
            key={phase.id}
            className="timeline__phase"
            style={{
              left: `${(start / clip.duration) * 100}%`,
              width: `${((end - start) / clip.duration) * 100}%`,
              background: PHASE_COLOURS[phase.contraction] ?? '#333a45',
            }}
            title={`${phase.label} — ${(end - start).toFixed(2)}s ${phase.contraction}`}
          >
            <span>{phase.label}</span>
          </div>
        ))}

        {loopRange && (
          <div
            className={`timeline__loop-range ${loop ? 'is-active' : ''}`}
            style={{
              left: `${(loopRange.start / clip.duration) * 100}%`,
              width: `${((loopRange.end - loopRange.start) / clip.duration) * 100}%`,
            }}
            title={`Loop range ${loopRange.start.toFixed(2)}–${loopRange.end.toFixed(2)}s`}
          />
        )}

        {keyframes.map((frame) => (
          <button
            key={frame.id}
            type="button"
            className={`timeline__key ${current?.id === frame.id ? 'is-current' : ''}`}
            style={{ left: `${(frame.time / clip.duration) * 100}%` }}
            title={`${frame.label ?? 'Keyframe'} at ${frame.time.toFixed(2)}s`}
            onPointerDown={(event) => {
              event.stopPropagation();
              setTime(frame.time);
            }}
          />
        ))}

        <div className="timeline__playhead" style={{ left: `${(time / clip.duration) * 100}%` }} />
      </div>
    </section>
  );
}
''', encoding='utf-8')

# -------------------------------------------------------------------------
# Joint panel: expose per-bone timing for the segment under the playhead.
# -------------------------------------------------------------------------
Path('src/editor/panels/JointPanel.tsx').write_text(r'''import { useMemo, useState } from 'react';
import type { BoneName } from '../../rig/boneNames';
import { boneLabel, isFingerBone } from '../../rig/boneNames';
import { AXES } from '../../rig/types';
import type { Axis } from '../../rig/types';
import { sortedKeyframes, sampleClip } from '../../animation/clip';
import { EASING_LABELS } from '../../animation/easing';
import type { EasingKind, PhaseJointTiming } from '../../exercises/types';
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
  const setJointTiming = useStudio((state) => state.setJointTiming);
  const hasClipboard = useStudio((state) => state.clipboard !== null);
  const [showFingerJoints, setShowFingerJoints] = useState(false);

  const pose = useMemo(() => sampleClip(clip, time).pose, [clip, time]);
  const rotation = selected ? pose.rotations[selected] : undefined;
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
''', encoding='utf-8')

# -------------------------------------------------------------------------
# Store tests cover undoable joint timing and playback-state range behaviour.
# -------------------------------------------------------------------------
Path('src/editor/store.test.ts').write_text(r'''import { beforeEach, describe, expect, it } from 'vitest';
import { useStudio } from './store';

const radians = (degrees: number) => (degrees * Math.PI) / 180;

describe('live grip closure tuning', () => {
  beforeEach(() => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('regenerates the deterministic grip while leaving the authored default available to undo', () => {
    expect(useStudio.getState().document.exercise.hands.closure).toBe(0.85);

    useStudio.getState().setGripClosure(0.5);
    const tuned = useStudio.getState().document;
    expect(tuned.exercise.hands.closure).toBe(0.5);
    expect(tuned.clip.keyframes[0].pose.rotations.index_01_l?.z).toBeCloseTo(radians(78 * 0.5), 8);
    expect(tuned.clip.keyframes[0].pose.rotations.index_01_r?.z).toBeCloseTo(-radians(78 * 0.5), 8);

    useStudio.getState().undo();
    expect(useStudio.getState().document.exercise.hands.closure).toBe(0.85);
  });

  it('clamps editor input to the grip generator range', () => {
    useStudio.getState().setGripClosure(2);
    expect(useStudio.getState().document.exercise.hands.closure).toBe(1);
    useStudio.getState().setGripClosure(-1);
    expect(useStudio.getState().document.exercise.hands.closure).toBe(0);
  });
});

describe('animation workspace authoring state', () => {
  beforeEach(() => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('authors per-joint segment timing through normal undo history', () => {
    const first = useStudio.getState().document.clip.keyframes[0];
    expect(first.jointTiming?.head).toBeUndefined();

    useStudio.getState().setJointTiming(first.id, 'head', {
      delay: 0.2,
      finish: 0.75,
      easing: 'minimumJerk',
    });
    const timing = useStudio.getState().document.clip.keyframes.find((frame) => frame.id === first.id)
      ?.jointTiming?.head;
    expect(timing).toEqual({ delay: 0.2, finish: 0.75, easing: 'minimumJerk' });

    useStudio.getState().undo();
    expect(
      useStudio.getState().document.clip.keyframes.find((frame) => frame.id === first.id)?.jointTiming
        ?.head,
    ).toBeUndefined();
  });

  it('normalises invalid joint timing rather than creating an impossible segment', () => {
    const first = useStudio.getState().document.clip.keyframes[0];
    useStudio.getState().setJointTiming(first.id, 'head', { delay: 2, finish: -1 });
    expect(
      useStudio.getState().document.clip.keyframes.find((frame) => frame.id === first.id)?.jointTiming
        ?.head,
    ).toEqual({ delay: 1, finish: 1 });
  });

  it('stores, rescales and resets a custom playback loop independently of the clip', () => {
    const duration = useStudio.getState().document.clip.duration;
    useStudio.getState().setLoopRange({ start: 2, end: 1 });
    expect(useStudio.getState().loopRange).toEqual({ start: 1, end: 2 });

    useStudio.getState().setDuration(duration * 2);
    expect(useStudio.getState().loopRange?.start).toBeCloseTo(2, 8);
    expect(useStudio.getState().loopRange?.end).toBeCloseTo(4, 8);

    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    expect(useStudio.getState().loopRange).toBeNull();
  });
});
''', encoding='utf-8')

# -------------------------------------------------------------------------
# Compact styling, appended once.
# -------------------------------------------------------------------------
styles = Path('src/editor/styles.css')
css = styles.read_text(encoding='utf-8')
marker = '/* ---------- animation authoring diagnostics ---------- */'
if marker not in css:
    css += r'''

/* ---------- animation authoring diagnostics ---------- */

.joint-timing {
  border: 1px solid var(--line);
  background: var(--panel-2);
  border-radius: var(--radius);
  padding: 9px;
}

.joint-timing .field:last-of-type {
  margin-bottom: 6px;
}

.timeline__range-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.timeline__range-readout {
  color: var(--accent);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
  min-width: 72px;
}

.timeline__loop-range {
  position: absolute;
  top: 0;
  bottom: 0;
  z-index: 2;
  pointer-events: none;
  border-left: 1px solid rgba(79, 214, 160, 0.55);
  border-right: 1px solid rgba(79, 214, 160, 0.55);
  background: rgba(79, 214, 160, 0.07);
}

.timeline__loop-range.is-active {
  background: rgba(79, 214, 160, 0.14);
  box-shadow: inset 0 0 0 1px rgba(79, 214, 160, 0.18);
}

.timeline__key {
  z-index: 3;
}

.timeline__playhead {
  z-index: 4;
}
'''
    styles.write_text(css, encoding='utf-8')

# Roadmap gets an implementation note, not a claim of full Blender parity.
roadmap = Path('docs/STUDIO_CAPABILITY_ROADMAP.md')
text = roadmap.read_text(encoding='utf-8')
needle = '## 4. Hand / grip workspace\n'
note = '''### Implemented animation-authoring foundation\n\n- Exact one-frame stepping plus 1/4× and 1/2× review speeds.\n- Custom In/Out loop ranges for repeated inspection of a difficult rep segment.\n- Selected-bone timing authoring for delay, finish point and easing on each keyframe segment.\n- Individual finger/thumb joint authoring remains available through the same joint workspace.\n\n'''
if note not in text:
    if needle not in text:
        raise SystemExit('roadmap insertion point missing')
    text = text.replace(needle, note + needle, 1)
    roadmap.write_text(text, encoding='utf-8')

print('Applied joint timing and loop-range authoring workspace')
