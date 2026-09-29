import {
  cylinderPrimitiveData,
  torusPrimitiveData,
} from '../core/primitiveGeometry';
import { HgGroup, type HgObject3D } from '../core/sceneGraph';
import {
  HgPrimitiveMaterial,
  HgPrimitiveMesh,
} from '../core/sceneMesh';
import type { HgSceneRayEvent } from './scenePointerTypes';
import type { HgScenePointerRouter } from './scenePointerRouter';
import type { HgTransformMode } from './transformGizmoInteraction';

export type HgFirstPartyGizmoAxis = 'x' | 'y' | 'z';

const COLOURS: Record<HgFirstPartyGizmoAxis, string> = {
  x: '#f05a5a',
  y: '#63d471',
  z: '#5d86f7',
};
const SELECTED_COLOUR = '#ffd35a';

const SHAFT_POSITION: Record<HgFirstPartyGizmoAxis, [number, number, number]> = {
  x: [0.48, 0, 0],
  y: [0, 0.48, 0],
  z: [0, 0, 0.48],
};
const TIP_POSITION: Record<HgFirstPartyGizmoAxis, [number, number, number]> = {
  x: [1, 0, 0],
  y: [0, 1, 0],
  z: [0, 0, 1],
};
const AXIS_ROTATION: Record<HgFirstPartyGizmoAxis, [number, number, number]> = {
  x: [0, 0, -Math.PI / 2],
  y: [0, 0, 0],
  z: [Math.PI / 2, 0, 0],
};
const RING_ROTATION: Record<HgFirstPartyGizmoAxis, [number, number, number]> = {
  x: [0, Math.PI / 2, 0],
  y: [Math.PI / 2, 0, 0],
  z: [0, 0, 0],
};

export interface HgFirstPartyTransformGizmoSceneResources {
  readonly group: HgGroup;
  readonly targets: ReadonlyMap<HgFirstPartyGizmoAxis, HgObject3D>;
  readonly materials: ReadonlyMap<HgFirstPartyGizmoAxis, HgPrimitiveMaterial>;
  dispose(): void;
}

export interface HgFirstPartyTransformGizmoPointerCallbacks {
  axisDown(axis: HgFirstPartyGizmoAxis, event: HgSceneRayEvent): void;
  move(event: HgSceneRayEvent): void;
  up(event: HgSceneRayEvent): void;
  cancel(event: HgSceneRayEvent): void;
}

const setTransform = (
  object: HgObject3D,
  position: [number, number, number],
  rotation: [number, number, number],
): void => {
  object.position.set(...position);
  object.rotation.set(...rotation);
};

const mesh = (
  geometry: ReturnType<typeof cylinderPrimitiveData> | ReturnType<typeof torusPrimitiveData>,
  material: HgPrimitiveMaterial,
): HgPrimitiveMesh => new HgPrimitiveMesh(geometry, material);

/** Project-owned transform-gizmo scene parallel to the retained legacy adapter. */
export function createHgTransformGizmoScene(
  mode: HgTransformMode,
): HgFirstPartyTransformGizmoSceneResources {
  const root = new HgGroup();
  root.name = 'hgpt-transform-gizmo';
  const targets = new Map<HgFirstPartyGizmoAxis, HgObject3D>();
  const materials = new Map<HgFirstPartyGizmoAxis, HgPrimitiveMaterial>();

  for (const axis of Object.keys(COLOURS) as HgFirstPartyGizmoAxis[]) {
    const material = new HgPrimitiveMaterial(COLOURS[axis], 'flat', {
      depthTest: false,
      depthWrite: false,
    }).setOpacity(mode === 'rotate' ? 0.9 : 1);
    materials.set(axis, material);

    if (mode === 'translate') {
      const axisGroup = new HgGroup();
      axisGroup.name = `hgpt-gizmo-axis-${axis}`;

      const shaft = mesh(
        cylinderPrimitiveData(0.026, 0.026, 0.9, 10),
        material,
      );
      setTransform(shaft, SHAFT_POSITION[axis], AXIS_ROTATION[axis]);

      const tip = mesh(
        cylinderPrimitiveData(0.085, 0, 0.22, 12),
        material,
      );
      setTransform(tip, TIP_POSITION[axis], AXIS_ROTATION[axis]);

      // Wider picking volume. Alpha zero means the first-party scene renderer
      // skips drawing it, while the pointer raycaster still sees its triangles.
      const hit = mesh(
        cylinderPrimitiveData(0.12, 0.12, 1.12, 8),
        new HgPrimitiveMaterial('#ffffff', 'flat', {
          depthWrite: false,
        }).setOpacity(0),
      );
      setTransform(hit, SHAFT_POSITION[axis], AXIS_ROTATION[axis]);

      axisGroup.add(shaft, tip, hit);
      root.add(axisGroup);
      targets.set(axis, axisGroup);
      continue;
    }

    const ring = new HgPrimitiveMesh(
      torusPrimitiveData(0.82, 0.055, Math.PI * 2, 10, 64),
      material,
    );
    ring.name = `hgpt-gizmo-axis-${axis}`;
    ring.rotation.set(...RING_ROTATION[axis]);
    root.add(ring);
    targets.set(axis, ring);
  }

  let disposed = false;
  return {
    group: root,
    targets,
    materials,
    dispose() {
      if (disposed) return;
      disposed = true;
      targets.clear();
      materials.clear();
      root.clear();
    },
  };
}

export function updateHgTransformGizmoActiveAxis(
  resources: HgFirstPartyTransformGizmoSceneResources,
  activeAxis: HgFirstPartyGizmoAxis | null,
): void {
  for (const [axis, material] of resources.materials) {
    material.setColour(axis === activeAxis ? SELECTED_COLOUR : COLOURS[axis]);
  }
}

export function registerHgTransformGizmoPointers(
  resources: HgFirstPartyTransformGizmoSceneResources,
  pointers: Pick<HgScenePointerRouter, 'register'>,
  callbacks: HgFirstPartyTransformGizmoPointerCallbacks,
): () => void {
  const remove: Array<() => void> = [];
  for (const [axis, target] of resources.targets) {
    remove.push(
      pointers.register(target, {
        pointerdown: (event) => callbacks.axisDown(axis, event),
      }),
    );
  }
  remove.push(
    pointers.register(resources.group, {
      pointermove: callbacks.move,
      pointerup: callbacks.up,
      pointercancel: callbacks.cancel,
    }),
  );
  return () => {
    for (const unregister of remove) unregister();
  };
}
