import { BufferAttribute, BufferGeometry } from 'three';
import type { Skeleton } from '../rig/skeleton';
import { canonicalSkeleton } from '../rig/skeleton';
import { ANATOMICAL_COLOURS } from './anatomicalColours';
import { ANATOMICAL_INDICES } from './anatomicalIndices';
import { ANATOMICAL_TRIANGLE_COUNT, ANATOMICAL_VERTEX_COUNT } from './anatomicalMeta';
import { ANATOMICAL_POSITIONS } from './anatomicalPositions';
import { ANATOMICAL_SKIN_INDICES } from './anatomicalSkinIndices';
import { ANATOMICAL_SKIN_WEIGHTS } from './anatomicalSkinWeights';
import type { BodyGeometry } from './mesh';

export const ANATOMICAL_PALETTE = {
  skin: '#b9bec2',
  shorts: '#202226',
  sclera: '#eceef0',
  iris: '#343a40',
} as const;

const bytes = (encoded: string): Uint8Array => {
  const decoded = atob(encoded);
  const result = new Uint8Array(decoded.length);
  for (let index = 0; index < decoded.length; index += 1) result[index] = decoded.charCodeAt(index);
  return result;
};

const float32 = (encoded: string): Float32Array => new Float32Array(bytes(encoded).buffer);
const uint16 = (encoded: string): Uint16Array => new Uint16Array(bytes(encoded).buffer);

/** Build the reproducible anatomical surface in the canonical rig's bind pose. */
export function buildAnatomicalBodyGeometry(
  _rig: Skeleton = canonicalSkeleton,
): BodyGeometry {
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new BufferAttribute(float32(ANATOMICAL_POSITIONS), 3));
  geometry.setAttribute('skinIndex', new BufferAttribute(uint16(ANATOMICAL_SKIN_INDICES), 4));
  geometry.setAttribute('skinWeight', new BufferAttribute(float32(ANATOMICAL_SKIN_WEIGHTS), 4));
  geometry.setAttribute('color', new BufferAttribute(bytes(ANATOMICAL_COLOURS), 3, true));
  geometry.setIndex(new BufferAttribute(uint16(ANATOMICAL_INDICES), 1));
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return { geometry, vertices: ANATOMICAL_VERTEX_COUNT, triangles: ANATOMICAL_TRIANGLE_COUNT };
}
