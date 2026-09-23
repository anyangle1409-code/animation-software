import { Vector3 } from 'three';
import type { SkinnedMesh } from 'three';

/**
 * Where a vertex of a posed skinned mesh actually is, in world space.
 *
 * Reading `position` alone gives the bind pose, which is rarely what a
 * measurement wants: anything checking clearance, penetration or strain needs
 * the vertex where the character currently holds it. That means the morph
 * targets at their current influence, then the skin transform, then the mesh's
 * own world matrix, in that order — and getting the order wrong produces
 * plausible numbers that are quietly measuring a different body.
 *
 * `morphTargetsRelative` decides whether a morph stores an offset or an absolute
 * position, and both conventions appear in the assets this project imports, so
 * it is honoured rather than assumed.
 *
 * The caller passes `out` and gets it back, because these run over tens of
 * thousands of vertices per frame and allocating there dominates the cost.
 */
export function posedVertex(mesh: SkinnedMesh, index: number, out: Vector3): Vector3 {
  const position = mesh.geometry.getAttribute('position');
  out.fromBufferAttribute(position, index);

  const morphs = mesh.geometry.morphAttributes.position ?? [];
  const influences = mesh.morphTargetInfluences ?? [];
  const relative = mesh.geometry.morphTargetsRelative === true;
  for (let slot = 0; slot < morphs.length; slot += 1) {
    const weight = influences[slot] ?? 0;
    if (!weight) continue;
    const morph = morphs[slot];
    out.x += (relative ? morph.getX(index) : morph.getX(index) - position.getX(index)) * weight;
    out.y += (relative ? morph.getY(index) : morph.getY(index) - position.getY(index)) * weight;
    out.z += (relative ? morph.getZ(index) : morph.getZ(index) - position.getZ(index)) * weight;
  }

  mesh.applyBoneTransform(index, out);
  return mesh.localToWorld(out);
}

/**
 * The bone with the largest share of a vertex, as a plain name.
 *
 * Imported rigs prefix their deform bones (`DEF-upper_arm.L`), so the prefix is
 * stripped and callers can match one pattern against both the canonical rig and
 * an import. This is a label for grouping and reporting — "which part of the
 * body is this" — not a claim that the vertex belongs to one bone; at a joint it
 * is blended across several by design.
 */
export function dominantBone(mesh: SkinnedMesh, index: number): string {
  const skinIndex = mesh.geometry.getAttribute('skinIndex');
  const skinWeight = mesh.geometry.getAttribute('skinWeight');
  let best = -1;
  let name = '';
  for (let lane = 0; lane < 4; lane += 1) {
    const weight = skinWeight.getComponent(index, lane);
    if (weight > best) {
      best = weight;
      name = mesh.skeleton.bones[skinIndex.getComponent(index, lane)]?.name ?? '';
    }
  }
  return name.replace(/^DEF-?/, '');
}
