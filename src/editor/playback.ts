import { clamp } from '../core/math';

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
