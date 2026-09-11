import { Box3, Matrix4, Vector3 } from 'three';
import type { BufferGeometry, Object3D, SkinnedMesh } from 'three';
import type { BoneName } from '../rig/boneNames';
import { canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { RIG_HEIGHT } from '../rig/humanoid';
import type { BoneMapping } from '../retargeting/boneMap';
import { buildCanonicalBones } from './bones';

/**
 * Rebinding an imported surface onto the canonical rig.
 *
 * A GLB arrives bound to its own skeleton, in its own bind pose, with its own
 * bone names and bone *order*. Our skin attributes index the canonical rig by
 * position, so an imported mesh cannot simply be handed to it — the indices
 * would point at unrelated bones.
 *
 * So the surface is rebound by name. For each vertex, its bind-space position
 * is read into the frame of each bone that influences it, and re-placed by the
 * canonical bone that bone maps to:
 *
 *     q = Σ wᵢ · (Cⱼ · S · Bᵢ⁻¹) · p
 *
 * with `Bᵢ` the source bone's world matrix at bind time, `Cⱼ` the canonical
 * bone's rest world matrix, and `S` a uniform scale that matches the model's
 * height to the rig's. The result is a surface in *our* rest pose, weighted to
 * *our* bone indices — after which it is an ordinary skinned mesh and every
 * system downstream treats it exactly like the built-in one.
 *
 * Two honest limits. Proportions follow the rig, not the model: a longer
 * forearm is re-placed onto ours, so the mesh stretches to fit rather than the
 * rig adapting to it. And custom normals, tangents and morph targets are
 * authored against the source bind pose, so they are dropped and the normals
 * recomputed.
 */

export interface RebindReport {
  vertices: number;
  /** Source bones that carried weight and found a canonical bone. */
  mappedBones: string[];
  /** Source bones that carried weight and did not; their weight moved to an ancestor. */
  unmappedBones: string[];
  /** Vertices with at least one influence moved to an ancestor bone. */
  reassigned: number;
  /**
   * Vertices whose influences the rig could not use at all — an unweighted
   * vertex, or one on a bone with no canonical counterpart anywhere above it.
   * Each is bound rigidly to the bone nearest it instead. A large count means
   * the file has a hole in its weighting, not that the import failed.
   */
  orphaned: number;
  /** Uniform scale applied to match the rig's height. */
  scale: number;
  /** The model's own height, metres. */
  height: number;
}

const INFLUENCES = 4;

/**
 * Rebind one imported skinned mesh onto the canonical rig, in place.
 *
 * The mesh keeps its geometry, its UVs and its material — only the positions,
 * the skin indices and the skin weights are rewritten.
 */
export function rebindToCanonical(
  mesh: SkinnedMesh,
  mapping: BoneMapping,
  rig: Skeleton = canonicalSkeleton,
): RebindReport {
  const geometry = mesh.geometry as BufferGeometry;
  const position = geometry.getAttribute('position');
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  if (!position || !skinIndex || !skinWeight) {
    throw new Error(`"${mesh.name || 'mesh'}" is not skinned: it has no skin indices or weights.`);
  }

  const sourceBones = mesh.skeleton.bones;
  const canonicalIndex = new Map<BoneName, number>();
  rig.bones.forEach((bone, index) => canonicalIndex.set(bone.name, index));

  // Which canonical bone each source bone belongs to. A bone the mapping does
  // not name — a twist bone, a helper, a finger the rig does not carry — hands
  // its weight to the nearest mapped ancestor, which is where that surface
  // would have ridden anyway.
  const byTargetName = new Map<string, BoneName>();
  for (const [canonical, target] of Object.entries(mapping.bones)) {
    if (target) byTargetName.set(target, canonical as BoneName);
  }

  // Where each source bone sits at bind time, used both for the placement
  // below and for the proximity fallback.
  const bindHead = sourceBones.map((_, index) =>
    new Vector3().setFromMatrixPosition(mesh.skeleton.boneInverses[index].clone().invert()),
  );

  const owner: (BoneName | null)[] = [];
  const inherited: boolean[] = [];
  for (const bone of sourceBones) {
    let search: Object3D | null = bone;
    let steps = 0;
    let found: BoneName | null = null;
    while (search && steps < 64) {
      const name = byTargetName.get(search.name);
      if (name) {
        found = name;
        break;
      }
      search = search.parent;
      steps += 1;
    }
    owner.push(found);
    inherited.push(found !== null && steps > 0);
  }

  /** The source bones that did find a canonical bone, for the fallback below. */
  const anchors = sourceBones
    .map((_, index) => index)
    .filter((index) => owner[index] !== null);

  // The model's height, measured in the bind space the weights are expressed
  // in, so a centimetre-scaled export is handled like any other.
  const bindMatrix = mesh.bindMatrix.clone();
  const bounds = new Box3();
  const point = new Vector3();
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    bounds.expandByPoint(
      point.set(position.getX(vertex), position.getY(vertex), position.getZ(vertex)).applyMatrix4(bindMatrix),
    );
  }
  const height = Math.max(0.2, bounds.max.y - bounds.min.y);
  const scale = mapping.characterHeight ? RIG_HEIGHT / mapping.characterHeight : RIG_HEIGHT / height;

  // Cⱼ · S · Bᵢ⁻¹, one per source bone.
  const rest = buildCanonicalBones(rig);
  const scaleMatrix = new Matrix4().makeScale(scale, scale, scale);
  const placement: (Matrix4 | null)[] = sourceBones.map((_, index) => {
    const canonical = owner[index];
    if (!canonical) return null;
    const bone = rest.boneByName.get(canonical);
    if (!bone) return null;
    const bind = mesh.skeleton.boneInverses[index].clone(); // Bᵢ⁻¹
    return bone.matrixWorld.clone().multiply(scaleMatrix).multiply(bind);
  });

  const pelvis = canonicalIndex.get('pelvis') ?? 0;

  const mapped = new Set<string>();
  const unmapped = new Set<string>();
  let reassigned = 0;
  let orphaned = 0;

  const source = new Vector3();
  const moved = new Vector3();
  const blended = new Vector3();

  for (let vertex = 0; vertex < position.count; vertex += 1) {
    source
      .set(position.getX(vertex), position.getY(vertex), position.getZ(vertex))
      .applyMatrix4(bindMatrix);

    const slots: { bone: number; weight: number }[] = [];
    let total = 0;
    let borrowed = false;
    for (let slot = 0; slot < INFLUENCES; slot += 1) {
      const weight = weightAt(skinWeight, vertex, slot);
      if (weight <= 0) continue;
      const index = indexAt(skinIndex, vertex, slot);
      const bone = sourceBones[index];
      if (!bone) continue;
      if (owner[index]) {
        mapped.add(bone.name);
        if (inherited[index]) borrowed = true;
      } else {
        unmapped.add(bone.name);
        continue;
      }
      slots.push({ bone: index, weight });
      total += weight;
    }

    blended.set(0, 0, 0);
    if (total <= 0) {
      // No influence this rig can use. Two rigs in three do this somewhere: a
      // face rig parented to the armature rather than to the head, or the
      // placeholder bone Blender's exporter gives vertices that were left out
      // of every vertex group. Rather than pin them to the root — which drags
      // whole limbs across the body — each such vertex takes the bone nearest
      // to it at bind time, so it rides the part of the body it sits on.
      // It is a repair, not a rescue: the vertex becomes rigid with one bone
      // and is counted in the report so the gap is visible rather than silent.
      let nearest = Infinity;
      let chosen = anchors[0] ?? 0;
      for (const anchor of anchors) {
        const distance = source.distanceToSquared(bindHead[anchor]);
        if (distance < nearest) {
          nearest = distance;
          chosen = anchor;
        }
      }
      const matrix = placement[chosen];
      blended.copy(source).applyMatrix4(matrix ?? scaleMatrix);
      writeSkin(skinIndex, skinWeight, vertex, [
        { bone: canonicalIndex.get(owner[chosen]!) ?? pelvis, weight: 1 },
      ]);
      orphaned += 1;
    } else {
      for (const slot of slots) {
        const matrix = placement[slot.bone]!;
        blended.addScaledVector(moved.copy(source).applyMatrix4(matrix), slot.weight / total);
      }
      writeSkin(
        skinIndex,
        skinWeight,
        vertex,
        slots
          .map((slot) => ({
            bone: canonicalIndex.get(owner[slot.bone]!) ?? pelvis,
            weight: slot.weight / total,
          }))
          .sort((one, two) => two.weight - one.weight),
      );
      if (borrowed) reassigned += 1;
    }

    position.setXYZ(vertex, blended.x, blended.y, blended.z);
  }

  position.needsUpdate = true;
  skinIndex.needsUpdate = true;
  skinWeight.needsUpdate = true;

  // Authored against the old bind pose, so no longer meaningful.
  geometry.deleteAttribute('tangent');
  geometry.morphAttributes = {};
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();

  return {
    vertices: position.count,
    mappedBones: [...mapped].sort(),
    unmappedBones: [...unmapped].sort(),
    reassigned,
    orphaned,
    scale,
    height,
  };
}

/** Several influences can land on the same canonical bone; add them together. */
function writeSkin(
  skinIndex: { setXYZW(i: number, x: number, y: number, z: number, w: number): void },
  skinWeight: { setXYZW(i: number, x: number, y: number, z: number, w: number): void },
  vertex: number,
  slots: { bone: number; weight: number }[],
): void {
  const merged = new Map<number, number>();
  for (const slot of slots) merged.set(slot.bone, (merged.get(slot.bone) ?? 0) + slot.weight);
  const ordered = [...merged]
    .sort((one, two) => two[1] - one[1])
    .slice(0, INFLUENCES);
  const sum = ordered.reduce((running, entry) => running + entry[1], 0) || 1;

  const bones = [0, 0, 0, 0];
  const weights = [0, 0, 0, 0];
  ordered.forEach(([bone, weight], slot) => {
    bones[slot] = bone;
    weights[slot] = weight / sum;
  });
  skinIndex.setXYZW(vertex, bones[0], bones[1], bones[2], bones[3]);
  skinWeight.setXYZW(vertex, weights[0], weights[1], weights[2], weights[3]);
}

interface Slotted {
  getX(index: number): number;
  getY(index: number): number;
  getZ(index: number): number;
  getW(index: number): number;
}

const weightAt = (attribute: Slotted, vertex: number, slot: number): number => {
  if (slot === 0) return attribute.getX(vertex);
  if (slot === 1) return attribute.getY(vertex);
  if (slot === 2) return attribute.getZ(vertex);
  return attribute.getW(vertex);
};

const indexAt = (attribute: Slotted, vertex: number, slot: number): number =>
  Math.round(weightAt(attribute, vertex, slot));
