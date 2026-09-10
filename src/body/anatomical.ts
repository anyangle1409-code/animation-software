import { BufferAttribute, BufferGeometry } from 'three';
import type { Skeleton } from '../rig/skeleton';
import { correctNeckLedge, correctNeckWeights } from './neck';
import { buildArmpitCorrectives, correctArmpitWeights, smoothShoulderFins } from './shoulder';
import { shapeHead } from './head';
import { canonicalSkeleton } from '../rig/skeleton';
import { ANATOMICAL_COLOURS } from './anatomicalColours';
import { ANATOMICAL_INDICES } from './anatomicalIndices';
import { ANATOMICAL_TRIANGLE_COUNT, ANATOMICAL_VERTEX_COUNT } from './anatomicalMeta';
import { ANATOMICAL_POSITIONS } from './anatomicalPositions';
import { ANATOMICAL_SKIN_INDICES } from './anatomicalSkinIndices';
import { ANATOMICAL_SKIN_WEIGHTS } from './anatomicalSkinWeights';
import type { BodyGeometry } from './mesh';

export { ANATOMICAL_PALETTE } from './anatomicalPalette';

const bytes = (encoded: string): Uint8Array => {
  const decoded = atob(encoded);
  const result = new Uint8Array(decoded.length);
  for (let index = 0; index < decoded.length; index += 1) result[index] = decoded.charCodeAt(index);
  return result;
};

const float32 = (encoded: string): Float32Array => new Float32Array(bytes(encoded).buffer);
const uint16 = (encoded: string): Uint16Array => new Uint16Array(bytes(encoded).buffer);

/** Build the reproducible anatomical surface in the canonical rig's bind pose. */
export interface AnatomicalOptions {
  /**
   * The shared repairs, all of them. Off gives the surface exactly as the
   * source encodes it, which is what the before-and-after tests measure
   * against.
   */
  repair?: boolean;
  /** The skull's proportions, the eyes and the hair. */
  head?: boolean;
  /** The head-to-neck binding and the ledge at the nape. */
  neck?: boolean;
  /** The folds at the neck-to-shoulder junction. */
  fins?: boolean;
  /** The armpit's binding and the shoulder correctives. */
  shoulder?: boolean;
}

export function buildAnatomicalBodyGeometry(
  _rig: Skeleton = canonicalSkeleton,
  options: AnatomicalOptions = {},
): BodyGeometry {
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new BufferAttribute(float32(ANATOMICAL_POSITIONS), 3));
  geometry.setAttribute('skinIndex', new BufferAttribute(uint16(ANATOMICAL_SKIN_INDICES), 4));
  geometry.setAttribute('skinWeight', new BufferAttribute(float32(ANATOMICAL_SKIN_WEIGHTS), 4));
  geometry.setAttribute('color', new BufferAttribute(bytes(ANATOMICAL_COLOURS), 3, true));
  geometry.setIndex(new BufferAttribute(uint16(ANATOMICAL_INDICES), 1));
  // The source binds everything above 1.50 m in its own space to the head alone.
  // That leaves the neck rigid with the skull, and it carries the head through a
  // different conversion transform from the surface below it, which leaves a
  // ledge at the nape. Both are repaired here, once, so the character, the
  // anatomy view and the GLB export share one corrected base surface.
  const repair = options.repair !== false;
  if (repair && options.head !== false) {
    // The head first: it only moves head-owned surface, and the neck repair
    // below reads the source's head binding, which this does not touch.
    geometry.userData.head = shapeHead(geometry, _rig);
  }
  if (repair && options.neck !== false) {
    // Positions before weights: the ledge is found from the source's own head
    // binding, which the weight repair is about to rewrite.
    geometry.userData.ledge = correctNeckLedge(geometry, _rig);
  }
  if (repair && options.fins !== false) {
    geometry.userData.fins = smoothShoulderFins(geometry);
  }
  if (repair && options.neck !== false) {
    geometry.userData.neck = correctNeckWeights(geometry, _rig);
  }
  if (repair && options.shoulder !== false) {
    geometry.userData.armpit = correctArmpitWeights(geometry, _rig);
    buildArmpitCorrectives(geometry, _rig);
  }
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return { geometry, vertices: ANATOMICAL_VERTEX_COUNT, triangles: ANATOMICAL_TRIANGLE_COUNT };
}
