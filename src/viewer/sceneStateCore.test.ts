import { describe, expect, it } from 'vitest';
import { createSceneState, SCENE_FRAME_PRIORITY } from './sceneStateCore';
import { skeleton } from '../editor/store';

describe('framework-neutral scene state', () => {
  it('starts with no resolved frame and an evaluation for the canonical runtime skeleton', () => {
    const state = createSceneState();
    expect(state.frame).toBeNull();
    expect(state.evaluation.matrix(skeleton.names[0]).elements).toHaveLength(16);
    expect(state.consumers.subscriberCount).toBe(0);
  });

  it('creates independent mutable state and consumer registries', () => {
    const first = createSceneState();
    const second = createSceneState();
    expect(first).not.toBe(second);
    expect(first.evaluation).not.toBe(second.evaluation);
    expect(first.consumers).not.toBe(second.consumers);
    first.consumers.add(() => {});
    expect(first.consumers.subscriberCount).toBe(1);
    expect(second.consumers.subscriberCount).toBe(0);
  });

  it('orders visual consumers explicitly so character pose precedes held equipment', () => {
    const state = createSceneState();
    const calls: string[] = [];
    state.consumers.add(() => calls.push('equipment'), SCENE_FRAME_PRIORITY.equipment);
    state.consumers.add(() => calls.push('character'), SCENE_FRAME_PRIORITY.character);
    state.consumers.add(() => calls.push('bone'), SCENE_FRAME_PRIORITY.bone);
    state.consumers.dispatch({ delta: 0.016, elapsed: 1, timestampMs: 1000 });
    expect(calls).toEqual(['character', 'bone', 'equipment']);
  });
});
