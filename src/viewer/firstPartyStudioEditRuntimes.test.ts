import { HgObject3D, HgPerspectiveCamera, HgScene } from '../core/sceneGraph';
import { HgVec3 } from '../core/linearMath';
import { describe, expect, it, vi } from 'vitest';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { IK_CHAIN_IDS } from '../ik/chains';
import type { IKChainId } from '../ik/types';
import type { HgSceneRayEvent } from './scenePointerTypes';
import type { HgScenePointerHandlers } from './scenePointerRouter';
import { createSceneState } from './sceneStateCore';
import {
  createFirstPartyStudioHandleGizmoRuntime,
  createFirstPartyStudioSelectionGizmoRuntime,
  type FirstPartyStudioEditState,
  type FirstPartyStudioEditStorePort,
} from './firstPartyStudioEditRuntimes';

const findByName = (root: HgObject3D, name: string): HgObject3D | null => {
  let found: HgObject3D | null = null;
  root.traverse((object) => {
    if (!found && object.name === name) found = object;
  });
  return found;
};

function createStore(initial: FirstPartyStudioEditState): FirstPartyStudioEditStorePort & {
  set(next: Partial<FirstPartyStudioEditState>): void;
} {
  let state = initial;
  const listeners = new Set<() => void>();
  return {
    getState: () => state,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    set(next) {
      state = { ...state, ...next };
      for (const listener of [...listeners]) listener();
    },
  };
}

const rayEvent = (pointerId = 1): HgSceneRayEvent => ({
  pointerId,
  ray: {
    origin: { x: 1, y: 2, z: 3 },
    direction: { x: 0, y: -1, z: 0 },
  },
  target: {
    setPointerCapture: vi.fn(),
    releasePointerCapture: vi.fn(),
  } as unknown as EventTarget,
  stopPropagation: vi.fn(),
});

describe('first-party Studio edit runtimes', () => {
  it('mounts/removes the selection gizmo and suspends orbit during drag', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const store = createStore({
      document: { clip },
      time: 0,
      selection: {
        bone: 'upperarm_l',
        handle: null,
        equipmentId: null,
        socketId: null,
      },
      gizmoMode: 'rotate',
      setBoneRotation: vi.fn(),
      setIKTarget: vi.fn(),
      setEquipmentTransform: vi.fn(),
      setEquipmentSocketTransform: vi.fn(),
    });
    const sceneState = createSceneState();
    const root = new HgScene();
    const camera = new HgPerspectiveCamera();
    camera.position.set(0, 0, 5);
    const registered = new Map<HgObject3D, HgScenePointerHandlers>();
    const pointers = {
      register(object: HgObject3D, handlers: HgScenePointerHandlers) {
        registered.set(object, handlers);
        return () => registered.delete(object);
      },
    };
    const orbit = {
      target: new HgVec3(),
      enabled: true,
      update: vi.fn(),
    };

    const runtime = createFirstPartyStudioSelectionGizmoRuntime({
      sceneState,
      root,
      pointers,
      camera,
      store,
      skeleton: canonicalSkeleton,
      controls: () => orbit,
    });

    sceneState.consumers.dispatch({ delta: 0.016, elapsed: 1, timestampMs: 1000 });
    const gizmo = findByName(root, 'hgpt-transform-gizmo')!;
    const x = findByName(root, 'hgpt-gizmo-axis-x')!;
    expect(gizmo).toBeTruthy();

    registered.get(x)?.pointerdown?.(rayEvent(4));
    expect(orbit.enabled).toBe(false);
    registered.get(gizmo)?.pointerup?.(rayEvent(4));
    expect(orbit.enabled).toBe(true);

    store.set({
      selection: { bone: null, handle: null, equipmentId: null, socketId: null },
    });
    expect(findByName(root, 'hgpt-transform-gizmo')).toBeNull();

    runtime.dispose();
    expect(sceneState.consumers.subscriberCount).toBe(0);
    expect(registered.size).toBe(0);
  });

  it('tracks the selected IK target with a translate gizmo', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const chain = IK_CHAIN_IDS[0] as IKChainId;
    clip.keyframes[0].ik = {
      ...clip.keyframes[0].ik,
      [chain]: {
        enabled: true,
        target: { x: 0.25, y: 1.15, z: 0.1 },
        pole: { x: 0.4, y: 1.0, z: 0.5 },
      },
    };
    const sample = sampleClip(clip, 0);

    const store = createStore({
      document: { clip },
      time: 0,
      selection: {
        bone: null,
        handle: { chain, kind: 'target' },
        equipmentId: null,
        socketId: null,
      },
      gizmoMode: 'translate',
      setBoneRotation: vi.fn(),
      setIKTarget: vi.fn(),
      setEquipmentTransform: vi.fn(),
      setEquipmentSocketTransform: vi.fn(),
    });
    const sceneState = createSceneState();
    sceneState.frame = {
      time: 0,
      pose: sample.pose,
      equipment: new Map(),
      ikResults: [],
      contacts: [],
    };
    const root = new HgScene();
    const camera = new HgPerspectiveCamera();
    camera.position.set(0, 0, 5);
    const pointers = { register: () => () => undefined };
    const orbit = {
      target: new HgVec3(),
      enabled: true,
      update: vi.fn(),
    };

    const runtime = createFirstPartyStudioHandleGizmoRuntime({
      sceneState,
      root,
      pointers,
      camera,
      store,
      skeleton: canonicalSkeleton,
      controls: () => orbit,
    });

    sceneState.consumers.dispatch({ delta: 0.016, elapsed: 1, timestampMs: 1000 });
    const gizmo = findByName(root, 'hgpt-transform-gizmo')!;
    const goal = sample.ik[chain]!;
    expect(gizmo.position.x).toBeCloseTo(goal.target.x, 9);
    expect(gizmo.position.y).toBeCloseTo(goal.target.y, 9);
    expect(gizmo.position.z).toBeCloseTo(goal.target.z, 9);

    store.set({
      selection: { bone: null, handle: null, equipmentId: null, socketId: null },
    });
    expect(findByName(root, 'hgpt-transform-gizmo')).toBeNull();

    runtime.dispose();
    expect(sceneState.consumers.subscriberCount).toBe(0);
  });
  it('keeps edit calculations and gizmo resources entirely first-party', async () => {
    const source = await import('node:fs').then(({ readFileSync }) =>
      readFileSync(new URL('./firstPartyStudioEditRuntimes.ts', import.meta.url), 'utf8'));
    expect(source).toContain("from '../core/linearMath'");
    expect(source).toContain("from './firstPartyTransformGizmoRuntime'");
    expect(source).not.toContain('threeSceneBoundary');
  });

});
