import { useMemo, useRef } from 'react';
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

  const stepFrame = (frames: number) => {
    pause();
    setTime(time + frames / clip.fps);
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
