import { describe, expect, it } from 'vitest';
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
    const wrapped = advancePlaybackTime(4.9, 0.25, 5, true, null);
    expect(wrapped.ended).toBe(false);
    expect(wrapped.time).toBeCloseTo(0.15, 10);
    expect(advancePlaybackTime(4.9, 0.25, 5, false, null)).toEqual({ time: 5, ended: true });
  });
});
