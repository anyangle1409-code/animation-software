import { Scene } from 'three';
import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import type { MuscleInvolvement } from '../exercises/types';
import { canonicalSkeleton } from '../rig/skeleton';
import { createSceneState } from './sceneStateCore';
import {
  createMuscleViewRuntime,
  type MuscleViewState,
  type MuscleViewStorePort,
} from './muscleViewRuntime';

function createStore(initial: MuscleViewState): MuscleViewStorePort & {
  setMuscles(muscles: MuscleInvolvement): void;
} {
  let state = initial;
  const listeners = new Set<() => void>();
  return {
    getState: () => state,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    setMuscles(muscles) {
      state = { document: { exercise: { muscles } } };
      for (const listener of [...listeners]) listener();
    },
  };
}

describe('framework-neutral muscle view runtime', () => {
  it('mounts, follows frames, rebuilds on exercise muscles and disposes', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const sceneState = createSceneState();
    sceneState.frame = resolveFrame(
      canonicalSkeleton,
      sceneState.evaluation,
      clip,
      0.8,
    );
    sceneState.evaluation.apply(sceneState.frame.pose);

    const root = new Scene();
    const store = createStore({
      document: { exercise: { muscles: bicepCurl.muscles } },
    });

    const runtime = createMuscleViewRuntime({ sceneState, root, store });

    expect(root.children).toContain(runtime.resources.group);
    expect(sceneState.consumers.subscriberCount).toBe(1);
    expect(runtime.resources.meshes.size).toBeGreaterThan(0);

    sceneState.consumers.dispatch({ delta: 0.016, elapsed: 1, timestampMs: 1000 });
    const biceps = runtime.resources.meshes.get('biceps_l');
    expect(biceps).toBeDefined();
    expect(Number.isFinite(biceps!.position.x)).toBe(true);
    expect(biceps!.scale.length()).toBeGreaterThan(0);

    const previousGroup = runtime.resources.group;
    store.setMuscles({ primary: [], secondary: [], stabilisers: [] });
    expect(root.children).not.toContain(previousGroup);
    expect(root.children).toContain(runtime.resources.group);

    runtime.dispose();
    runtime.dispose();
    expect(root.children).not.toContain(runtime.resources.group);
    expect(sceneState.consumers.subscriberCount).toBe(0);
  });
});
