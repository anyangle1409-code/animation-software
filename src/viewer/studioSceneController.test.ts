import { Group, Scene } from 'three';
import { HgPerspectiveCamera } from '../core/sceneGraph';
import { describe, expect, it, vi } from 'vitest';
import type { CharacterBuild, CharacterSource } from '../character';
import { createStore } from '../core/observableStore';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import type { CharacterState } from '../editor/characterStoreCore';
import { createSceneState } from './sceneStateCore';
import { createStudioSceneController } from './studioSceneController';

class FakeCanvas extends EventTarget {
  style = { touchAction: '' };
  clientHeight = 800;
  setPointerCapture = vi.fn();
  releasePointerCapture = vi.fn();
  hasPointerCapture = vi.fn(() => false);
}

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

describe('framework-neutral Studio scene controller', () => {
  it('composes current view state, reacts to mode/toggle changes and disposes', async () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const actions = {
      selectBone: vi.fn(),
      selectHandle: vi.fn(),
      selectEquipment: vi.fn(),
      setBoneRotation: vi.fn(),
      setIKTarget: vi.fn(),
      setEquipmentTransform: vi.fn(),
      setEquipmentSocketTransform: vi.fn(),
    };
    const studio = createStore<any>(() => ({
      document: { exercise: bicepCurl, clip },
      time: 0,
      playing: false,
      loop: true,
      speed: 1,
      loopRange: null,
      selection: { bone: null, handle: null, equipmentId: null, socketId: null },
      viewMode: 'combined',
      showJoints: true,
      showEquipment: true,
      showIkHandles: true,
      showGrid: true,
      backdrop: 'studio',
      gizmoMode: 'rotate',
      camera: 'recommended',
      ...actions,
    }));

    let characterState!: CharacterState;
    const character = createStore<CharacterState>((set) => {
      characterState = {
        sourceId: 'procedural',
        sourceStatus: { kind: 'idle' },
        bindMode: 'preserve',
        rebind: null,
        imported: null,
        active: null,
        correctivesPreview: true,
        deformationRevision: 0,
        name: null,
        mapping: null,
        report: null,
        status: { kind: 'idle' },
        setSource: (sourceId) => set({ sourceId }),
        setSourceStatus: (sourceStatus) => set({ sourceStatus }),
        setActive: (active) => set({ active }),
        setCorrectivesPreview: (correctivesPreview) => set({ correctivesPreview }),
        setDeformationControl: vi.fn(),
        setBindMode: vi.fn(),
        load: vi.fn(),
        setBone: vi.fn(),
        clear: vi.fn(),
        persist: vi.fn(),
      };
      return characterState;
    });

    const root = new Scene();
    const camera = new HgPerspectiveCamera();
    camera.position.set(2.3, 1.35, 2.7);
    const element = new FakeCanvas() as unknown as HTMLCanvasElement;
    const pointerHandlers = new Map<object, object>();
    const pointers = {
      register(object: object, handlers: object) {
        pointerHandlers.set(object, handlers);
        return () => pointerHandlers.delete(object);
      },
    };

    const sourceForId = (id: string): CharacterSource => ({
      id,
      label: id,
      capabilities: { anatomy: false, textured: false },
      async build() {
        return fakeBuild(id);
      },
    });

    const sceneState = createSceneState();
    const controller = createStudioSceneController({
      sceneState,
      bindings: { camera, scene: root, element, pointers: pointers as any },
      studioStore: studio as any,
      characterStore: character,
      skeleton: canonicalSkeleton,
      characterSourceForId: sourceForId,
    });

    expect(root.getObjectByName('hgpt-studio-stage')).not.toBeNull();
    expect(root.getObjectByName('hgpt-skeleton-view')).not.toBeNull();
    expect(root.getObjectByName('hgpt-muscle-view')).not.toBeNull();

    studio.setState({ viewMode: 'character', showEquipment: false, showIkHandles: false });
    await Promise.resolve();
    await Promise.resolve();

    expect(root.getObjectByName('hgpt-skeleton-view')).toBeUndefined();
    expect(root.getObjectByName('hgpt-muscle-view')).toBeUndefined();
    expect(root.getObjectByName('build-procedural')).not.toBeNull();

    studio.setState({ viewMode: 'skeleton' });
    await Promise.resolve();

    expect(root.getObjectByName('build-procedural')).toBeUndefined();
    expect(root.getObjectByName('hgpt-skeleton-view')).not.toBeNull();

    controller.dispose();
    controller.dispose();

    expect(sceneState.consumers.subscriberCount).toBe(0);
    expect(pointerHandlers.size).toBe(0);
    expect(root.children).toHaveLength(0);
  });
});
