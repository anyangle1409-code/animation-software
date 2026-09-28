import {
  ConeGeometry,
  CylinderGeometry,
  Group,
  Mesh,
  MeshBasicMaterial,
  TorusGeometry,
  type Object3D,
} from 'three';
import type { HgSceneRayEvent } from './scenePointerTypes';
import type { HgScenePointerRouter } from './scenePointerRouter';
import type { HgTransformMode } from './transformGizmoInteraction';

export type HgGizmoAxis = 'x' | 'y' | 'z';

const COLOURS: Record<HgGizmoAxis, string> = {
  x: '#f05a5a',
  y: '#63d471',
  z: '#5d86f7',
};
const SELECTED_COLOUR = '#ffd35a';

const SHAFT_POSITION: Record<HgGizmoAxis, [number, number, number]> = {
  x: [0.48, 0, 0],
  y: [0, 0.48, 0],
  z: [0, 0, 0.48],
};
const TIP_POSITION: Record<HgGizmoAxis, [number, number, number]> = {
  x: [1, 0, 0],
  y: [0, 1, 0],
  z: [0, 0, 1],
};
const AXIS_ROTATION: Record<HgGizmoAxis, [number, number, number]> = {
  x: [0, 0, -Math.PI / 2],
  y: [0, 0, 0],
  z: [Math.PI / 2, 0, 0],
};
const RING_ROTATION: Record<HgGizmoAxis, [number, number, number]> = {
  x: [0, Math.PI / 2, 0],
  y: [Math.PI / 2, 0, 0],
  z: [0, 0, 0],
};

export interface TransformGizmoSceneResources {
  group: Group;
  targets: ReadonlyMap<HgGizmoAxis, Object3D>;
  materials: ReadonlyMap<HgGizmoAxis, MeshBasicMaterial>;
  dispose(): void;
}

export interface TransformGizmoPointerCallbacks {
  axisDown(axis: HgGizmoAxis, event: HgSceneRayEvent): void;
  move(event: HgSceneRayEvent): void;
  up(event: HgSceneRayEvent): void;
  cancel(event: HgSceneRayEvent): void;
}

const setTransform = (
  object: Object3D,
  position: [number, number, number],
  rotation: [number, number, number],
) => {
  object.position.set(position[0], position[1], position[2]);
  object.rotation.set(rotation[0], rotation[1], rotation[2]);
};

export function createTransformGizmoScene(mode: HgTransformMode): TransformGizmoSceneResources {
  const root = new Group();
  root.name = 'hgpt-transform-gizmo';
  const targets = new Map<HgGizmoAxis, Object3D>();
  const materials = new Map<HgGizmoAxis, MeshBasicMaterial>();
  const disposables: Array<{ dispose(): void }> = [];

  for (const axis of Object.keys(COLOURS) as HgGizmoAxis[]) {
    const material = new MeshBasicMaterial({
      color: COLOURS[axis],
      depthTest: false,
      ...(mode === 'rotate' ? { transparent: true, opacity: 0.9 } : {}),
    });
    materials.set(axis, material);
    disposables.push(material);

    if (mode === 'translate') {
      const axisGroup = new Group();
      axisGroup.name = `hgpt-gizmo-axis-${axis}`;

      const shaftGeometry = new CylinderGeometry(0.026, 0.026, 0.9, 10);
      const shaft = new Mesh(shaftGeometry, material);
      setTransform(shaft, SHAFT_POSITION[axis], AXIS_ROTATION[axis]);
      disposables.push(shaftGeometry);

      const tipGeometry = new ConeGeometry(0.085, 0.22, 12);
      const tip = new Mesh(tipGeometry, material);
      setTransform(tip, TIP_POSITION[axis], AXIS_ROTATION[axis]);
      disposables.push(tipGeometry);

      const hitGeometry = new CylinderGeometry(0.12, 0.12, 1.12, 8);
      const hitMaterial = new MeshBasicMaterial({
        transparent: true,
        opacity: 0,
        depthWrite: false,
      });
      const hit = new Mesh(hitGeometry, hitMaterial);
      setTransform(hit, SHAFT_POSITION[axis], AXIS_ROTATION[axis]);
      disposables.push(hitGeometry, hitMaterial);

      axisGroup.add(shaft, tip, hit);
      root.add(axisGroup);
      targets.set(axis, axisGroup);
      continue;
    }

    const geometry = new TorusGeometry(0.82, 0.055, 10, 64);
    const ring = new Mesh(geometry, material);
    ring.name = `hgpt-gizmo-axis-${axis}`;
    ring.rotation.set(
      RING_ROTATION[axis][0],
      RING_ROTATION[axis][1],
      RING_ROTATION[axis][2],
    );
    root.add(ring);
    targets.set(axis, ring);
    disposables.push(geometry);
  }

  let disposed = false;
  return {
    group: root,
    targets,
    materials,
    dispose() {
      if (disposed) return;
      disposed = true;
      for (const disposable of disposables) disposable.dispose();
      root.clear();
    },
  };
}

export function updateTransformGizmoActiveAxis(
  resources: TransformGizmoSceneResources,
  activeAxis: HgGizmoAxis | null,
): void {
  for (const [axis, material] of resources.materials) {
    material.color.set(axis === activeAxis ? SELECTED_COLOUR : COLOURS[axis]);
  }
}

export function registerTransformGizmoPointers(
  resources: TransformGizmoSceneResources,
  pointers: Pick<HgScenePointerRouter, 'register'>,
  callbacks: TransformGizmoPointerCallbacks,
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
