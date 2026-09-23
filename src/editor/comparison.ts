import { Vector3 } from 'three';
import { CORE_BONES, isScapula } from '../rig/boneNames';
import type { CoreBoneName } from '../rig/boneNames';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { Pose } from '../rig/types';
import type { PoseMarkerKind } from '../animation/clip';

export interface PoseSnapshot {
  pose: Pose;
  time: number;
  marker?: PoseMarkerKind;
  label?: string;
}

export interface DiagramSegment {
  bone: CoreBoneName;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

/**
 * Project the canonical rig into a normalised front-view diagram. This is an
 * inspection aid only; no camera or projection state is written back to the clip.
 */
export function frontPoseDiagram(pose: Pose): DiagramSegment[] {
  const evaluation = new PoseEvaluation(canonicalSkeleton).apply(pose);
  // The scapulae are left out: each lies in the plane of the back, so a front
  // projection would draw it as a diagonal across the chest that no limb makes.
  const raw = CORE_BONES.filter((bone) => bone !== 'root' && !isScapula(bone)).map((bone) => {
    const head = evaluation.head(bone, new Vector3());
    const tail = evaluation.tail(bone, new Vector3());
    return { bone, x1: head.x, y1: head.y, x2: tail.x, y2: tail.y };
  });

  const xs = raw.flatMap((line) => [line.x1, line.x2]);
  const ys = raw.flatMap((line) => [line.y1, line.y2]);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const width = Math.max(1e-6, maxX - minX);
  const height = Math.max(1e-6, maxY - minY);
  const padding = 0.06;
  const usable = 1 - 2 * padding;

  return raw.map((line) => ({
    bone: line.bone,
    x1: padding + ((line.x1 - minX) / width) * usable,
    y1: padding + (1 - (line.y1 - minY) / height) * usable,
    x2: padding + ((line.x2 - minX) / width) * usable,
    y2: padding + (1 - (line.y2 - minY) / height) * usable,
  }));
}
