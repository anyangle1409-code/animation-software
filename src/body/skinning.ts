import { canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';

/** A four-slot skin attribute, read by component. */
export interface SlotAttribute {
  getComponent(index: number, component: number): number;
}

/** Total skin weight a vertex carries from a set of bones. */
export function boneInfluence(
  skinIndex: SlotAttribute,
  skinWeight: SlotAttribute,
  vertex: number,
  bones: ReadonlySet<string>,
  rig: Skeleton = canonicalSkeleton,
): number {
  let total = 0;
  for (let slot = 0; slot < 4; slot += 1) {
    const weight = skinWeight.getComponent(vertex, slot);
    if (weight <= 0) continue;
    const bone = rig.bones[skinIndex.getComponent(vertex, slot)];
    if (bone && bones.has(bone.name)) total += weight;
  }
  return total;
}

export const smoothstep = (edge0: number, edge1: number, value: number): number => {
  if (edge1 <= edge0) return value >= edge1 ? 1 : 0;
  const t = Math.min(1, Math.max(0, (value - edge0) / (edge1 - edge0)));
  return t * t * (3 - 2 * t);
};
