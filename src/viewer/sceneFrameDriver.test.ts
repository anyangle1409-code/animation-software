import { describe, expect, it, vi } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { createSceneState } from './sceneStateCore';
import { driveSceneFrame, type ScenePlaybackPort } from './sceneFrameDriver';

function playback(overrides: Partial<ScenePlaybackPort> = {}): ScenePlaybackPort {
  return {
    time: 0,
    playing: false,
    loop: false,
    speed: 1,
    loopRange: null,
    setTime: vi.fn(),
    pause: vi.fn(),
    ...overrides,
  };
}

describe('renderer-neutral scene frame driver', () => {
  const skeleton = canonicalSkeleton;
  const clip = generateClip(skeleton, bicepCurl);

  it('resolves a paused frame before dispatching visual consumers', () => {
    const scene = createSceneState();
    const state = playback({ time: 1.25 });
    const seen: Array<{ time: number | null; dispatchedElapsed: number }> = [];
    scene.consumers.add((frame) => {
      seen.push({ time: scene.frame?.time ?? null, dispatchedElapsed: frame.elapsed });
    });

    const resolved = driveSceneFrame({
      scene,
      skeleton,
      clip,
      playback: state,
      frame: { delta: 0.016, elapsed: 3.5, timestampMs: 3500 },
    });

    expect(resolved).toBe(scene.frame);
    expect(resolved.time).toBe(1.25);
    expect(seen).toEqual([{ time: 1.25, dispatchedElapsed: 3.5 }]);
    expect(state.setTime).not.toHaveBeenCalled();
    expect(state.pause).not.toHaveBeenCalled();
  });

  it('advances playback with the existing 100 ms host-delta clamp before resolving', () => {
    const scene = createSceneState();
    const state = playback({ time: 0.5, playing: true, speed: 2 });

    const resolved = driveSceneFrame({
      scene,
      skeleton,
      clip,
      playback: state,
      frame: { delta: 0.75, elapsed: 2, timestampMs: 2000 },
    });

    expect(resolved.time).toBeCloseTo(0.7, 12);
    expect(state.setTime).toHaveBeenCalledTimes(1);
    expect(state.setTime).toHaveBeenCalledWith(resolved.time);
    expect(state.pause).not.toHaveBeenCalled();
  });

  it('pauses non-looping playback exactly at the clip end and still dispatches that frame', () => {
    const scene = createSceneState();
    const state = playback({
      time: clip.duration - 0.02,
      playing: true,
      speed: 1,
      loop: false,
    });
    const dispatched = vi.fn();
    scene.consumers.add(dispatched);

    const resolved = driveSceneFrame({
      scene,
      skeleton,
      clip,
      playback: state,
      frame: { delta: 0.05, elapsed: 9, timestampMs: 9000 },
    });

    expect(resolved.time).toBe(clip.duration);
    expect(state.setTime).toHaveBeenCalledWith(clip.duration);
    expect(state.pause).toHaveBeenCalledTimes(1);
    expect(dispatched).toHaveBeenCalledTimes(1);
  });

  it('preserves loop-range playback semantics without host-specific state', () => {
    const scene = createSceneState();
    const state = playback({
      time: 1.19,
      playing: true,
      loop: true,
      loopRange: { start: 1, end: 1.2 },
    });

    const resolved = driveSceneFrame({
      scene,
      skeleton,
      clip,
      playback: state,
      frame: { delta: 0.03, elapsed: 1, timestampMs: 1000 },
    });

    expect(resolved.time).toBeCloseTo(1.02, 12);
    expect(state.pause).not.toHaveBeenCalled();
  });
});
