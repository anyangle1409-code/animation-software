import { useRef, useState } from 'react';
import { Group, Object3D, Quaternion, Vector3 } from 'three';
import type { Camera } from 'three';
import { HgQuat, HgVec3 } from '../core/linearMath';
import {
  HgTransformDrag,
  type HgTransformMode,
} from './transformGizmoInteraction';
import type { HgSceneRayEvent } from './scenePointerTypes';
import { SCENE_FRAME_PRIORITY, useSceneFrame } from './sceneState';

type AxisName = 'x' | 'y' | 'z';

interface FirstPartyTransformGizmoProps {
  object: Object3D;
  camera: Camera;
  mode: HgTransformMode;
  size?: number;
  onDragStart?: () => void;
  onDragEnd?: () => void;
  onObjectChange?: () => void;
}

const AXES: Record<AxisName, HgVec3> = {
  x: new HgVec3(1, 0, 0),
  y: new HgVec3(0, 1, 0),
  z: new HgVec3(0, 0, 1),
};

const COLOURS: Record<AxisName, string> = {
  x: '#f05a5a',
  y: '#63d471',
  z: '#5d86f7',
};

const SHAFT_POSITION: Record<AxisName, [number, number, number]> = {
  x: [0.48, 0, 0],
  y: [0, 0.48, 0],
  z: [0, 0, 0.48],
};

const TIP_POSITION: Record<AxisName, [number, number, number]> = {
  x: [1, 0, 0],
  y: [0, 1, 0],
  z: [0, 0, 1],
};

const AXIS_ROTATION: Record<AxisName, [number, number, number]> = {
  x: [0, 0, -Math.PI / 2],
  y: [0, 0, 0],
  z: [Math.PI / 2, 0, 0],
};

const RING_ROTATION: Record<AxisName, [number, number, number]> = {
  x: [0, Math.PI / 2, 0],
  y: [Math.PI / 2, 0, 0],
  z: [0, 0, 0],
};

const hgVector = (value: { x: number; y: number; z: number }) =>
  new HgVec3(value.x, value.y, value.z);

const hgQuaternion = (value: { x: number; y: number; z: number; w: number }) =>
  new HgQuat(value.x, value.y, value.z, value.w);

const hgRay = (event: HgSceneRayEvent) => ({
  origin: hgVector(event.ray.origin),
  direction: hgVector(event.ray.direction),
});

interface ActiveDrag {
  pointerId: number;
  interaction: HgTransformDrag;
}

/** Project-owned world-axis translation/rotation gizmo for the current renderer. */
export function FirstPartyTransformGizmo({
  object,
  camera,
  mode,
  size = 0.8,
  onDragStart,
  onDragEnd,
  onObjectChange,
}: FirstPartyTransformGizmoProps) {
  const group = useRef<Group>(null);
  const drag = useRef<ActiveDrag | null>(null);
  const [activeAxis, setActiveAxis] = useState<AxisName | null>(null);
  const worldPosition = useRef(new Vector3());
  const worldQuaternion = useRef(new Quaternion());
  const parentQuaternion = useRef(new Quaternion());

  useSceneFrame(() => {
    if (!group.current) return;
    object.updateWorldMatrix(true, false);
    object.getWorldPosition(worldPosition.current);
    group.current.position.copy(worldPosition.current);
    const distance = camera.position.distanceTo(worldPosition.current);
    const scale = Math.max(0.04, distance * 0.12 * size);
    group.current.scale.setScalar(scale);
  }, SCENE_FRAME_PRIORITY.gizmo);

  const begin = (axis: AxisName) => (event: HgSceneRayEvent) => {
    event.stopPropagation();
    object.updateWorldMatrix(true, false);
    object.getWorldPosition(worldPosition.current);
    object.getWorldQuaternion(worldQuaternion.current);
    drag.current = {
      pointerId: event.pointerId,
      interaction: new HgTransformDrag(
        mode,
        AXES[axis],
        hgRay(event),
        hgVector(worldPosition.current),
        hgQuaternion(worldQuaternion.current),
      ),
    };
    setActiveAxis(axis);
    (event.target as EventTarget & {
      setPointerCapture?: (pointerId: number) => void;
    } | null)?.setPointerCapture?.(event.pointerId);
    onDragStart?.();
  };

  const move = (event: HgSceneRayEvent) => {
    const active = drag.current;
    if (!active || active.pointerId !== event.pointerId) return;
    event.stopPropagation();
    const result = active.interaction.update(hgRay(event));
    if (!result) return;
    worldPosition.current.set(result.position.x, result.position.y, result.position.z);
    worldQuaternion.current.set(
      result.quaternion.x,
      result.quaternion.y,
      result.quaternion.z,
      result.quaternion.w,
    );
    if (object.parent) {
      object.parent.updateWorldMatrix(true, false);
      object.position.copy(object.parent.worldToLocal(worldPosition.current));
      object.parent.getWorldQuaternion(parentQuaternion.current);
      object.quaternion.copy(
        parentQuaternion.current.invert().multiply(worldQuaternion.current),
      );
    } else {
      object.position.copy(worldPosition.current);
      object.quaternion.copy(worldQuaternion.current);
    }
    object.updateMatrix();
    object.updateMatrixWorld(true);
    onObjectChange?.();
  };

  const end = (event: HgSceneRayEvent) => {
    const active = drag.current;
    if (!active || active.pointerId !== event.pointerId) return;
    event.stopPropagation();
    (event.target as EventTarget & {
      releasePointerCapture?: (pointerId: number) => void;
    } | null)?.releasePointerCapture?.(event.pointerId);
    drag.current = null;
    setActiveAxis(null);
    onDragEnd?.();
  };

  const colour = (axis: AxisName) => activeAxis === axis ? '#ffd35a' : COLOURS[axis];

  return (
    <group
      ref={group}
      name="hgpt-transform-gizmo"
      onPointerMove={move}
      onPointerUp={end}
      onPointerCancel={end}
    >
      {(Object.keys(AXES) as AxisName[]).map((axis) => (
        mode === 'translate' ? (
          <group key={axis} onPointerDown={begin(axis)}>
            <mesh position={SHAFT_POSITION[axis]} rotation={AXIS_ROTATION[axis]}>
              <cylinderGeometry args={[0.026, 0.026, 0.9, 10]} />
              <meshBasicMaterial color={colour(axis)} depthTest={false} />
            </mesh>
            <mesh position={TIP_POSITION[axis]} rotation={AXIS_ROTATION[axis]}>
              <coneGeometry args={[0.085, 0.22, 12]} />
              <meshBasicMaterial color={colour(axis)} depthTest={false} />
            </mesh>
            <mesh position={SHAFT_POSITION[axis]} rotation={AXIS_ROTATION[axis]}>
              <cylinderGeometry args={[0.12, 0.12, 1.12, 8]} />
              <meshBasicMaterial transparent opacity={0} depthWrite={false} />
            </mesh>
          </group>
        ) : (
          <mesh key={axis} rotation={RING_ROTATION[axis]} onPointerDown={begin(axis)}>
            <torusGeometry args={[0.82, 0.055, 10, 64]} />
            <meshBasicMaterial color={colour(axis)} depthTest={false} transparent opacity={0.9} />
          </mesh>
        )
      ))}
    </group>
  );
}
