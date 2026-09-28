import { Group, Scene } from 'three';
import { describe, expect, it, vi } from 'vitest';
import type {
  CharacterBuild,
  CharacterSource,
  CharacterVariant,
} from '../character';
import type { HandSpec } from '../exercises/types';
import { canonicalSkeleton } from '../rig/skeleton';
import { createSceneState } from './sceneStateCore';
import {
  createCharacterViewRuntime,
  type CharacterViewCharacterState,
  type CharacterViewCharacterStorePort,
} from './characterViewRuntime';

function fakeBuild(source: string): CharacterBuild {
  const object = new Group();
  object.name = `build-${source}`;
  return {
    source,
    root: null!,
    bones: [],
    boneByName: new Map(),
    skeleton: null!,
    object,
    meshes: [],
    deformation: null,
    capabilities: { anatomy: false, textured: false },
    dispose: vi.fn(),
  };
}

function characterStore(sourceId: string): CharacterViewCharacterStorePort & {
  setSource(id: string): void;
  statuses: Array<{ kind: 'idle' | 'loading' | 'error'; message?: string }>;
} {
  const listeners = new Set<() => void>();
  const statuses: Array<{ kind: 'idle' | 'loading' | 'error'; message?: string }> = [];
  let state!: CharacterViewCharacterState;
  state = {
    sourceId,
    correctivesPreview: true,
    active: null,
    setSourceStatus(status) {
      statuses.push(status);
    },
    setActive(active) {
      state = { ...state, active };
    },
  };
  return {
    getState: () => state,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    setSource(id) {
      state = { ...state, sourceId: id };
      for (const listener of [...listeners]) listener();
    },
    statuses,
  };
}

describe('framework-neutral character view runtime', () => {
  it('replaces async builds by source and disposes scene resources deterministically', async () => {
    const sceneState = createSceneState();
    const root = new Scene();
    const store = characterStore('one');
    const builds = new Map<string, CharacterBuild>([
      ['one', fakeBuild('one')],
      ['two', fakeBuild('two')],
    ]);
    const sourceForId = (id: string): CharacterSource => ({
      id,
      label: id,
      capabilities: { anatomy: false, textured: false },
      async build(_rig, _options?: { variant?: CharacterVariant }) {
        return builds.get(id)!;
      },
    });
    const hands: HandSpec = {
      grip: 'none',
      orientation: 'neutral',
      closure: 0,
    };

    const runtime = createCharacterViewRuntime({
      sceneState,
      root,
      studioStore: { getState: () => ({ document: { exercise: { hands } } }) },
      characterStore: store,
      skeleton: canonicalSkeleton,
      sourceForId,
    });

    await Promise.resolve();
    await Promise.resolve();

    expect(root.children).toContain(builds.get('one')!.object);
    expect(store.getState().active).toBe(builds.get('one'));
    expect(store.statuses.at(-1)?.kind).toBe('idle');

    store.setSource('two');
    await Promise.resolve();
    await Promise.resolve();

    expect(root.children).not.toContain(builds.get('one')!.object);
    expect(builds.get('one')!.dispose).toHaveBeenCalledTimes(1);
    expect(root.children).toContain(builds.get('two')!.object);
    expect(store.getState().active).toBe(builds.get('two'));

    runtime.dispose();
    runtime.dispose();

    expect(root.children).not.toContain(builds.get('two')!.object);
    expect(builds.get('two')!.dispose).toHaveBeenCalledTimes(1);
    expect(store.getState().active).toBeNull();
    expect(sceneState.consumers.subscriberCount).toBe(0);
  });
});
