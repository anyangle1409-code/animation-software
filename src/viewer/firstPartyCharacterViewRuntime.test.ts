import { describe, expect, it, vi } from 'vitest';
import { HgBone, HgGroup } from '../core/sceneGraph';
import {
  HgBufferAttribute,
  HgBufferGeometry,
  HgSkeleton,
  HgSkinnedMesh,
  HgStandardMaterial,
} from '../core/sceneSkin';
import type { CharacterBuild, CharacterSource } from '../character';
import { canonicalSkeleton } from '../rig/skeleton';
import { createSceneState } from './sceneStateCore';
import { createFirstPartyCharacterViewRuntime } from './firstPartyCharacterViewRuntime';

const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

const buildFixture = (): CharacterBuild => {
  const bone = new HgBone();
  bone.name = 'pelvis';
  const geometry = new HgBufferGeometry();
  geometry.setAttribute(
    'position',
    new HgBufferAttribute(new Float32Array([0, 0, 0, 0.2, 0, 0, 0, 0.2, 0]), 3),
  );
  geometry.setAttribute(
    'skinIndex',
    new HgBufferAttribute(new Uint16Array([0,0,0,0, 0,0,0,0, 0,0,0,0]), 4),
  );
  geometry.setAttribute(
    'skinWeight',
    new HgBufferAttribute(new Float32Array([1,0,0,0, 1,0,0,0, 1,0,0,0]), 4),
  );
  geometry.setIndex([0, 1, 2]);
  geometry.computeVertexNormals();
  const mesh = new HgSkinnedMesh(geometry, new HgStandardMaterial({ color: '#ffffff' }));
  mesh.bind(new HgSkeleton([bone]));
  mesh.add(bone);
  return {
    source: 'fixture',
    root: bone as never,
    bones: [bone] as never,
    boneByName: new Map([['pelvis', bone]]) as never,
    skeleton: mesh.skeleton as never,
    object: mesh as never,
    meshes: [mesh] as never,
    deformation: null,
    capabilities: { anatomy: false, textured: false },
    dispose: vi.fn(),
  };
};

describe('first-party character view runtime', () => {
  it('mounts a project-owned visual snapshot instead of the character source object', async () => {
    const sceneState = createSceneState();
    const root = new HgGroup();
    const build = buildFixture();
    const source: CharacterSource = {
      id: 'fixture',
      label: 'Fixture',
      capabilities: { anatomy: false, textured: false },
      async build() {
        return build;
      },
    };
    const state = {
      sourceId: 'fixture',
      correctivesPreview: true,
      active: null as CharacterBuild | null,
      setSourceStatus: vi.fn(),
      setActive(value: CharacterBuild | null) {
        this.active = value;
      },
    };
    const store = {
      getState: () => state,
      subscribe: () => () => {},
    };
    const runtime = createFirstPartyCharacterViewRuntime({
      sceneState,
      root,
      studioStore: {
        getState: () => ({
          document: {
            exercise: {
              hands: { grip: 'none', orientation: 'neutral', closure: 0 },
            },
          },
        }),
      },
      characterStore: store,
      skeleton: canonicalSkeleton,
      sourceForId: () => source,
    });

    await flush();
    expect(runtime.build).toBe(build);
    expect(runtime.visualRoot).not.toBeNull();
    expect(root.children).toEqual([runtime.visualRoot]);
    expect(root.children).not.toContain(build.object as never);
    expect(runtime.visualRoot?.children).toHaveLength(1);

    runtime.dispose();
    expect(root.children).toHaveLength(0);
    expect(build.dispose).toHaveBeenCalledTimes(1);
  });
});
