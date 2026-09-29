import { describe, expect, it, vi } from 'vitest';
import { generateClip } from '../animation/generate';
import type { CharacterBuild, CharacterSource } from '../character';
import { createStore } from '../core/observableStore';
import {
  HgGroup,
  HgPerspectiveCamera,
  HgScene,
  type HgObject3D,
} from '../core/sceneGraph';
import type { CharacterState } from '../editor/characterStoreCore';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { createSceneState } from './sceneStateCore';
import { createFirstPartyStudioSceneController } from './firstPartyStudioSceneController';

class FakeCanvas extends EventTarget {
  style = { touchAction: '' };
  clientHeight = 800;
  setPointerCapture = vi.fn();
  releasePointerCapture = vi.fn();
  hasPointerCapture = vi.fn(() => false);
}

const findByName = (root: HgObject3D, name: string): HgObject3D | null => {
  let found: HgObject3D | null = null;
  root.traverse((object) => {
    if (!found && object.name === name) found = object;
  });
  return found;
};

function fakeBuild(source: string): CharacterBuild {
  const object = new HgGroup();
  object.name = 'fixture-source-' + source;
  return {
    source,
    root: null!,
    bones: [],
    boneByName: new Map(),
    skeleton: null!,
    object: object as never,
    meshes: [],
    deformation: null,
    capabilities: { anatomy: false, textured: false },
    dispose: vi.fn(),
  };
}

describe('first-party Studio scene controller', () => {
  it('composes view state on HgScene, reacts to toggles and disposes cleanly', async () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
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
      selectBone: vi.fn(),
      selectHandle: vi.fn(),
      selectEquipment: vi.fn(),
      setBoneRotation: vi.fn(),
      setIKTarget: vi.fn(),
      setEquipmentTransform: vi.fn(),
      setEquipmentSocketTransform: vi.fn(),
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

    const root = new HgScene();
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
      async build() { return fakeBuild(id); },
    });

    const sceneState = createSceneState();
    const controller = createFirstPartyStudioSceneController({
      sceneState,
      bindings: {
        camera,
        scene: root,
        element,
        pointers: pointers as never,
      },
      studioStore: studio as never,
      characterStore: character,
      skeleton: canonicalSkeleton,
      characterSourceForId: sourceForId,
    });

    expect(findByName(root, 'hgpt-studio-stage')).not.toBeNull();
    expect(findByName(root, 'hgpt-skeleton-view')).not.toBeNull();
    expect(findByName(root, 'hgpt-muscle-view')).not.toBeNull();
    expect(findByName(root, 'hgpt-equipment-view')).not.toBeNull();
    expect(findByName(root, 'hgpt-ik-handles')).not.toBeNull();

    studio.setState({
      viewMode: 'character',
      showEquipment: false,
      showIkHandles: false,
    });
    await Promise.resolve();
    await Promise.resolve();

    expect(findByName(root, 'hgpt-skeleton-view')).toBeNull();
    expect(findByName(root, 'hgpt-muscle-view')).toBeNull();
    expect(findByName(root, 'hgpt-equipment-view')).toBeNull();
    expect(findByName(root, 'hgpt-ik-handles')).toBeNull();
    expect(findByName(root, 'hgpt-character-view')).not.toBeNull();

    studio.setState({ viewMode: 'skeleton' });
    await Promise.resolve();
    expect(findByName(root, 'hgpt-character-view')).toBeNull();
    expect(findByName(root, 'hgpt-skeleton-view')).not.toBeNull();

    controller.dispose();
    controller.dispose();
    expect(sceneState.consumers.subscriberCount).toBe(0);
    expect(pointerHandlers.size).toBe(0);
    expect(root.children).toHaveLength(0);
  });
});
