import { describe, expect, it } from 'vitest';
import { createSceneState } from './sceneStateCore';
import { skeleton } from '../editor/store';

describe('framework-neutral scene state', () => {
  it('starts with no resolved frame and an evaluation for the canonical runtime skeleton', () => {
    const state = createSceneState();
    expect(state.frame).toBeNull();
    expect(state.evaluation.matrix(skeleton.names[0]).elements).toHaveLength(16);
  });

  it('creates independent mutable state objects', () => {
    const first = createSceneState();
    const second = createSceneState();
    expect(first).not.toBe(second);
    expect(first.evaluation).not.toBe(second.evaluation);
    first.frame = null;
    expect(second.frame).toBeNull();
  });
});
