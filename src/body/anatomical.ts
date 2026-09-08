import { BufferAttribute, BufferGeometry } from 'three';
import type { Skeleton } from '../rig/skeleton';
import { canonicalSkeleton } from '../rig/skeleton';
import { MUSCLE_GROUP_IDS } from '../muscles/groups';
import type { MuscleGroupId } from '../muscles/groups';
import type { BodyGeometry } from './mesh';
import {
  ANATOMICAL_TRIANGLE_COUNT,
  ANATOMICAL_VERTEX_COUNT,
} from './anatomicalMeta';
import { ANATOMICAL_POSITIONS } from './anatomicalPositions';
import { ANATOMICAL_INDICES } from './anatomicalIndices';
import { ANATOMICAL_SKIN_INDICES } from './anatomicalSkinIndices';
import { ANATOMICAL_SKIN_WEIGHTS } from './anatomicalSkinWeights';
import { ANATOMICAL_COLOURS } from './anatomicalColours';

const decode = (encoded: string): Uint8Array => {
  const binary = atob(encoded);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  return bytes;
};

const float32 = (encoded: string): Float32Array => {
  const bytes = decode(encoded);
  return new Float32Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / Float32Array.BYTES_PER_ELEMENT);
};

const uint16 = (encoded: string): Uint16Array => {
  const bytes = decode(encoded);
  return new Uint16Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / Uint16Array.BYTES_PER_ELEMENT);
};

const muscleIndex = (group: MuscleGroupId | null): number =>
  group === null ? 0 : MUSCLE_GROUP_IDS.indexOf(group) + 1;

function surfaceMuscle(
  bone: string,
  x: number,
  y: number,
  z: number,
): MuscleGroupId | null {
  const front = z >= 0;
  if (bone.startsWith('clavicle_')) return front ? 'deltoid_anterior' : 'trapezius_upper';
  if (bone.startsWith('upperarm_')) {
    if (y > 1.34) return front ? 'deltoid_anterior' : 'deltoid_posterior';
    // The source arm's local forward surface sits just behind the torso's
    // centre plane after the A-pose conversion.
    return z < 0.015 ? 'biceps' : 'triceps';
  }
  if (bone.startsWith('forearm_')) return front ? 'forearm_flexors' : 'forearm_extensors';
  if (bone === 'spine_03') {
    if (front) return Math.abs(x) < 0.13 ? 'pectoralis' : 'deltoid_anterior';
    return y > 1.34 ? 'trapezius_upper' : 'erector_upper';
  }
  if (bone === 'spine_02') {
    if (front) return Math.abs(x) < 0.075 ? 'rectus_abdominis' : 'obliques';
    return Math.abs(x) > 0.075 ? 'latissimus' : 'erector_mid';
  }
  if (bone === 'spine_01') {
    if (front) return Math.abs(x) < 0.07 ? 'rectus_abdominis' : 'obliques';
    return 'erector_lower';
  }
  if (bone === 'pelvis') return front ? 'rectus_abdominis' : 'gluteus';
  if (bone.startsWith('thigh_')) {
    if (!front) return 'hamstrings';
    const outside = bone.endsWith('_l') ? x < -0.11 : x > 0.11;
    const inside = bone.endsWith('_l') ? x > -0.055 : x < 0.055;
    return outside ? 'hip_abductors' : inside ? 'hip_adductors' : 'quadriceps';
  }
  if (bone.startsWith('shin_')) return 'calves';
  return null;
}

/**
 * Human-topology body generated from MakeHuman's CC0 base mesh and default
 * weights, reshaped to an athletic male and remapped onto the canonical rig.
 */
export function buildAnatomicalBodyGeometry(
  rig: Skeleton = canonicalSkeleton,
): BodyGeometry {
  if (rig.bones.length < 53) {
    throw new Error('The anatomical body requires the complete canonical humanoid rig');
  }

  const geometry = new BufferGeometry();
  const positions = float32(ANATOMICAL_POSITIONS);
  const skinIndices = uint16(ANATOMICAL_SKIN_INDICES);
  const skinWeights = float32(ANATOMICAL_SKIN_WEIGHTS);
  geometry.setAttribute('position', new BufferAttribute(positions, 3));
  geometry.setAttribute('skinIndex', new BufferAttribute(skinIndices, 4));
  geometry.setAttribute('skinWeight', new BufferAttribute(skinWeights, 4));
  geometry.setAttribute('color', new BufferAttribute(decode(ANATOMICAL_COLOURS), 3, true));
  const muscleGroups = new Uint8Array(ANATOMICAL_VERTEX_COUNT);
  for (let vertex = 0; vertex < ANATOMICAL_VERTEX_COUNT; vertex += 1) {
    let ownerSlot = 0;
    for (let slot = 1; slot < 4; slot += 1) {
      if (skinWeights[vertex * 4 + slot] > skinWeights[vertex * 4 + ownerSlot]) ownerSlot = slot;
    }
    const bone = rig.bones[skinIndices[vertex * 4 + ownerSlot]]?.name ?? 'root';
    muscleGroups[vertex] = muscleIndex(surfaceMuscle(
      bone,
      positions[vertex * 3],
      positions[vertex * 3 + 1],
      positions[vertex * 3 + 2],
    ));
  }
  geometry.setAttribute('muscleGroup', new BufferAttribute(muscleGroups, 1));
  geometry.setIndex(new BufferAttribute(uint16(ANATOMICAL_INDICES), 1));
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  geometry.userData.source = 'MakeHuman CC0 human topology';

  return {
    geometry,
    vertices: ANATOMICAL_VERTEX_COUNT,
    triangles: ANATOMICAL_TRIANGLE_COUNT,
  };
}
