import { BufferAttribute, Bone, SkinnedMesh, Vector3 } from 'three';
import type { Skeleton } from '../rig/skeleton';
import type { BoneName, Side } from '../rig/boneNames';
import { elbowFlexion } from '../body/elbow';
import type {
  DeformationControl,
  DeformationSampler,
  DeformationStack,
} from './types';
import { correctiveSampler } from './importedDeformation';
import type { CorrectiveTarget } from './importedDeformation';

/**
 * Pose-dependent arm muscle shape for an imported character.
 *
 * The skinned mesh alone can only follow bones, so a curl reads as a tube
 * rotating rather than a muscle working. This adds corrective morph targets on
 * the biceps belly, the brachialis/elbow junction and the proximal forearm, all
 * driven by the elbow's own flexion, so the arm fills and shortens toward Peak
 * and returns to the authored shape at Bottom.
 *
 * Why morph targets rather than writing vertices each frame: `elbowFlexion` is
 * exactly 0 in the rest pose, so an influence driven by it guarantees the
 * accepted static shape at Bottom, and the same targets bake into animation
 * tracks, which keeps the viewport and the exported file identical. Writing
 * positions on the CPU would be invisible to the exporter.
 *
 * Each target carries a normal delta as well as a position delta. Without that
 * the silhouette would swell while the shading stayed flat, and a muscle whose
 * shading does not change barely reads as fuller at all.
 */
export interface MuscleDeformationOptions {
  enabled?: boolean;
  /** Anterior swell of the biceps belly at full flexion, metres. */
  biceps?: number;
  /** How far the belly draws toward its own middle as it shortens, metres. */
  shorten?: number;
  /** Fill at the brachialis / elbow junction, metres. */
  brachialis?: number;
  /** Fill on the proximal forearm flexor mass, metres. */
  forearm?: number;
}

export interface MuscleRuntimeTuning {
  /** 0 = the accepted static arm at every pose; 1 = the authored amplitudes. */
  amount: number;
  defaultAmount: number;
}

type Target = CorrectiveTarget;

const clamp01 = (value: number): number => Math.min(1, Math.max(0, value));

/** cos², so a region reaches zero value *and* zero slope at its edge. */
const falloff = (t: number, from: number, to: number): number => {
  if (t <= from || t >= to) return 0;
  const centre = (from + to) / 2;
  const half = (to - from) / 2;
  return Math.cos(((t - centre) / half) * (Math.PI / 2)) ** 2;
};

/**
 * A plateau: 1 across the interior, easing to 0 in the outermost `edge` of the
 * span. The axial draw-in needs this rather than `falloff`, because it is
 * strongest near the belly's ends — multiplying it by a profile that is zero
 * there would cancel the effect exactly where it should be largest.
 */
const plateau = (t: number, from: number, to: number, edge = 0.18): number => {
  if (t <= from || t >= to) return 0;
  const u = (t - from) / (to - from);
  const ramp = Math.min(u, 1 - u) / edge;
  if (ramp >= 1) return 1;
  return ramp * ramp * (3 - 2 * ramp);
};

const point = new Vector3();
const along = new Vector3();
const radial = new Vector3();

export function importedMuscleDeformation(
  meshes: SkinnedMesh[],
  boneByName: Map<BoneName, Bone>,
  rig: Skeleton,
  options?: MuscleDeformationOptions,
  tuning?: MuscleRuntimeTuning,
): DeformationStack | null {
  if (options?.enabled === false) return null;
  const targets: Target[] = [];
  for (const mesh of meshes) {
    for (const side of ['l', 'r'] as const) {
      targets.push(...appendArm(mesh, boneByName, side, options, tuning));
    }
  }
  if (!targets.length) return null;

  const controls: DeformationControl[] | undefined = tuning
    ? [{
        id: 'muscleAmount',
        label: 'Arm muscle contraction',
        min: 0,
        max: 1,
        step: 0.05,
        defaultValue: clamp01(tuning.defaultAmount),
        get value() {
          return clamp01(tuning.amount);
        },
        set(value: number) {
          tuning.amount = clamp01(value);
        },
        note: '0% is the accepted static arm at every pose; 100% is the authored contraction. The morphs themselves stay capped at their authored amplitudes.',
      }]
    : undefined;

  return {
    controls,
    update({ evaluation }) {
      for (const target of targets) {
        if (!target.mesh.morphTargetInfluences) continue;
        target.mesh.morphTargetInfluences[target.influence] =
          elbowFlexion(evaluation, target.side) * target.scale();
      }
    },
    sampler: (): DeformationSampler | null => correctiveSampler(targets, rig),
  };
}

function appendArm(
  mesh: SkinnedMesh,
  boneByName: Map<BoneName, Bone>,
  side: Side,
  options: MuscleDeformationOptions | undefined,
  tuning: MuscleRuntimeTuning | undefined,
): Target[] {
  const upper = boneByName.get(`upperarm_${side}` as BoneName);
  const lower = boneByName.get(`forearm_${side}` as BoneName);
  const hand = boneByName.get(`hand_${side}` as BoneName);
  if (!upper || !lower || !hand) return [];
  const position = mesh.geometry.getAttribute('position');
  const skinIndex = mesh.geometry.getAttribute('skinIndex');
  const skinWeight = mesh.geometry.getAttribute('skinWeight');
  if (!position || !skinIndex || !skinWeight) return [];

  mesh.updateWorldMatrix(true, false);
  const shoulder = mesh.worldToLocal(upper.getWorldPosition(new Vector3()));
  const elbow = mesh.worldToLocal(lower.getWorldPosition(new Vector3()));
  const wrist = mesh.worldToLocal(hand.getWorldPosition(new Vector3()));
  const upperAxis = elbow.clone().sub(shoulder);
  const foreAxis = wrist.clone().sub(elbow);
  const upperLength = upperAxis.length();
  const foreLength = foreAxis.length();
  if (upperLength < 1e-4 || foreLength < 1e-4) return [];
  upperAxis.divideScalar(upperLength);
  foreAxis.divideScalar(foreLength);
  // The character stands in a T-pose with +z to the front, so anterior is +z
  // and the biceps is the front of the upper arm.
  const anterior = new Vector3(0, 0, 1);

  const upperOwned = ownership(mesh, upper.name);
  const lowerOwned = ownership(mesh, lower.name);
  if (!upperOwned.size || !lowerOwned.size) return [];

  const bicepsAmp = options?.biceps ?? 0.007;
  const shortenAmp = options?.shorten ?? 0.004;
  const brachialisAmp = options?.brachialis ?? 0.0045;
  const forearmAmp = options?.forearm ?? 0.003;

  const biceps = new Float32Array(position.count * 3);
  const brachialis = new Float32Array(position.count * 3);
  const forearm = new Float32Array(position.count * 3);

  for (let vertex = 0; vertex < position.count; vertex += 1) {
    point.fromBufferAttribute(position, vertex);
    const upperShare = share(skinIndex, skinWeight, vertex, upperOwned);
    const lowerShare = share(skinIndex, skinWeight, vertex, lowerOwned);

    if (upperShare > 0.25) {
      along.copy(point).sub(shoulder);
      const t = along.dot(upperAxis) / upperLength;
      // Fades out before the deltoid above and before the elbow below, so the
      // shoulder cap and the elbow corrective are not fought over.
      const belly = falloff(t, 0.12, 0.84);
      if (belly > 0) {
        radial.copy(along).addScaledVector(upperAxis, -along.dot(upperAxis));
        if (radial.lengthSq() > 1e-10) {
          radial.normalize();
          const front = Math.max(0, radial.dot(anterior)) ** 1.5;
          const swell = bicepsAmp * belly * front * upperShare;
          // Shortening: the belly draws toward its own middle from both ends,
          // which is what makes a contracting muscle read as shorter and not
          // merely thicker. Signed by which side of the mid-belly the vertex
          // is on, over a plateau so both ends actually travel.
          // Inset from the swell window at both ends, and further at the
          // proximal end: full axial pull at t = 0.12 would drag armpit and
          // chest skin down the humerus, which is the accepted armpit repair's
          // territory. Zero there, and the deltoid frontier stays put.
          const u = (t - 0.26) / (0.78 - 0.26);
          const pull = -shortenAmp * plateau(t, 0.26, 0.78, 0.3)
            * Math.max(-1, Math.min(1, (u - 0.5) * 2)) * upperShare;
          biceps[vertex * 3] = radial.x * swell + upperAxis.x * pull;
          biceps[vertex * 3 + 1] = radial.y * swell + upperAxis.y * pull;
          biceps[vertex * 3 + 2] = radial.z * swell + upperAxis.z * pull;
        }
      }
    }

    // Brachialis sits across the junction: the distal upper arm and the very
    // top of the forearm, on the front and the outside rather than the front
    // alone.
    const junction = Math.max(
      upperShare > 0.2 ? falloff(distanceAlong(point, shoulder, upperAxis) / upperLength, 0.72, 1.06) * upperShare : 0,
      lowerShare > 0.2 ? falloff(distanceAlong(point, elbow, foreAxis) / foreLength, -0.06, 0.24) * lowerShare : 0,
    );
    if (junction > 0) {
      const base = upperShare >= lowerShare ? shoulder : elbow;
      const axis = upperShare >= lowerShare ? upperAxis : foreAxis;
      along.copy(point).sub(base);
      radial.copy(along).addScaledVector(axis, -along.dot(axis));
      if (radial.lengthSq() > 1e-10) {
        radial.normalize();
        const facing = Math.max(0, radial.dot(anterior) * 0.7 + Math.abs(radial.x) * 0.5);
        const push = brachialisAmp * junction * facing;
        brachialis[vertex * 3] = radial.x * push;
        brachialis[vertex * 3 + 1] = radial.y * push;
        brachialis[vertex * 3 + 2] = radial.z * push;
      }
    }

    if (lowerShare > 0.25) {
      along.copy(point).sub(elbow);
      const s = along.dot(foreAxis) / foreLength;
      const mass = falloff(s, 0.04, 0.62);
      if (mass > 0) {
        radial.copy(along).addScaledVector(foreAxis, -along.dot(foreAxis));
        if (radial.lengthSq() > 1e-10) {
          radial.normalize();
          const push = forearmAmp * mass * lowerShare;
          forearm[vertex * 3] = radial.x * push;
          forearm[vertex * 3 + 1] = radial.y * push;
          forearm[vertex * 3 + 2] = radial.z * push;
        }
      }
    }
  }

  const scale = tuning ? () => clamp01(tuning.amount) : () => 1;
  const built: Target[] = [];
  for (const [delta, name] of [
    [biceps, `homeGymPT_biceps_${side}`],
    [brachialis, `homeGymPT_brachialis_${side}`],
    [forearm, `homeGymPT_forearm_${side}`],
  ] as const) {
    const target = appendTarget(mesh, side, delta, name, scale);
    if (target) built.push(target);
  }
  return built;
}

const distanceAlong = (p: Vector3, base: Vector3, axis: Vector3): number =>
  p.clone().sub(base).dot(axis);

/** Which skin indices belong to a bone, including its deform twist helpers. */
function ownership(mesh: SkinnedMesh, boneName: string): Set<number> {
  const found = new Set<number>();
  const bones = mesh.skeleton?.bones ?? [];
  // GLTFLoader strips dots from node names, so `DEF-forearm.L.001` arrives as
  // `DEF-forearmL001`. Match on a punctuation-free form or the helpers are
  // silently missed and the corrective loses the twist bones' vertices.
  const plain = (value: string) => value.replace(/[^a-z0-9]/gi, '').toLowerCase();
  const wanted = plain(boneName);
  bones.forEach((bone, index) => {
    if (plain(bone.name).startsWith(wanted)) found.add(index);
  });
  return found;
}

function share(
  skinIndex: { getComponent(index: number, component: number): number },
  skinWeight: { getComponent(index: number, component: number): number },
  vertex: number,
  owned: Set<number>,
): number {
  let total = 0;
  for (let lane = 0; lane < 4; lane += 1) {
    const weight = skinWeight.getComponent(vertex, lane);
    if (weight <= 0) continue;
    if (owned.has(skinIndex.getComponent(vertex, lane))) total += weight;
  }
  return total;
}

/**
 * Append one corrective as a morph target, with the normal delta it implies.
 *
 * three.js indexes `morphAttributes.normal` by the same slot as
 * `morphAttributes.position`, so a normal array has to cover every target the
 * geometry already carries. Earlier targets are padded with zero normals, which
 * leaves their behaviour exactly as it was.
 */
function appendTarget(
  mesh: SkinnedMesh,
  side: Side,
  delta: Float32Array,
  name: string,
  scale: () => number,
): Target | null {
  const position = mesh.geometry.getAttribute('position');
  let affected = 0;
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    const start = vertex * 3;
    if (
      Math.abs(delta[start]) > 1e-7 ||
      Math.abs(delta[start + 1]) > 1e-7 ||
      Math.abs(delta[start + 2]) > 1e-7
    ) {
      affected += 1;
    }
  }
  if (!affected) return null;

  const relative = mesh.geometry.morphTargetsRelative === true;
  const positions = mesh.geometry.morphAttributes.position ?? [];
  const morph = relative
    ? new BufferAttribute(delta, 3)
    : absolute(position, delta);
  morph.name = name;
  mesh.geometry.morphAttributes.position = [...positions, morph];

  const normalDelta = normalsFor(mesh, delta, relative);
  if (normalDelta) {
    const normals = mesh.geometry.morphAttributes.normal ?? [];
    const baseNormal = mesh.geometry.getAttribute('normal');
    while (normals.length < positions.length) {
      const zeros = new Float32Array(position.count * 3);
      normals.push(relative || !baseNormal
        ? new BufferAttribute(zeros, 3)
        : new BufferAttribute(Float32Array.from((baseNormal.array as ArrayLike<number>)), 3));
    }
    normals.push(normalDelta);
    mesh.geometry.morphAttributes.normal = normals;
  }

  mesh.updateMorphTargets();
  const influence = mesh.morphTargetDictionary?.[morph.name] ?? positions.length;
  if (mesh.morphTargetInfluences) mesh.morphTargetInfluences[influence] = 0;
  return { mesh, side, influence, name: morph.name, scale };
}

function absolute(
  position: { count: number; getX(i: number): number; getY(i: number): number; getZ(i: number): number },
  delta: Float32Array,
): BufferAttribute {
  const values = new Float32Array(position.count * 3);
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    values[vertex * 3] = position.getX(vertex) + delta[vertex * 3];
    values[vertex * 3 + 1] = position.getY(vertex) + delta[vertex * 3 + 1];
    values[vertex * 3 + 2] = position.getZ(vertex) + delta[vertex * 3 + 2];
  }
  return new BufferAttribute(values, 3);
}

/**
 * Smooth vertex normals for an arbitrary set of positions, welded across
 * co-located duplicates so the two sides of a UV seam agree.
 */
function smoothNormals(
  points: Float32Array,
  index: { count: number; getX(i: number): number },
  groupOf: Map<number, number[]>,
  count: number,
): Float64Array {
  const accumulated = new Float64Array(count * 3);
  for (let triangle = 0; triangle < index.count; triangle += 3) {
    const a = index.getX(triangle);
    const b = index.getX(triangle + 1);
    const c = index.getX(triangle + 2);
    const ux = points[b * 3] - points[a * 3];
    const uy = points[b * 3 + 1] - points[a * 3 + 1];
    const uz = points[b * 3 + 2] - points[a * 3 + 2];
    const vx = points[c * 3] - points[a * 3];
    const vy = points[c * 3 + 1] - points[a * 3 + 1];
    const vz = points[c * 3 + 2] - points[a * 3 + 2];
    const nx = uy * vz - uz * vy;
    const ny = uz * vx - ux * vz;
    const nz = ux * vy - uy * vx;
    for (const vertex of [a, b, c]) {
      for (const other of groupOf.get(vertex) ?? [vertex]) {
        accumulated[other * 3] += nx;
        accumulated[other * 3 + 1] += ny;
        accumulated[other * 3 + 2] += nz;
      }
    }
  }
  for (let vertex = 0; vertex < count; vertex += 1) {
    const length = Math.hypot(
      accumulated[vertex * 3],
      accumulated[vertex * 3 + 1],
      accumulated[vertex * 3 + 2],
    );
    if (length > 0) {
      accumulated[vertex * 3] /= length;
      accumulated[vertex * 3 + 1] /= length;
      accumulated[vertex * 3 + 2] /= length;
    }
  }
  return accumulated;
}

/**
 * The shading change the displacement implies.
 *
 * The reference is the smooth field recomputed from the *undisplaced*
 * positions, not the normals stored in the asset. That matters: this asset's
 * convention is unwelded per-vertex normals with deliberate hard edges at the
 * scalp and neck, so differencing against the stored normals would emit a
 * non-zero delta over the whole body — rewriting the face, neck and chest to
 * welded smooth normals and undoing the surface repair the moment the muscle
 * fills. Differencing two fields computed the same way cancels the convention
 * out, and leaves a delta that is exactly zero wherever the surface does not
 * move.
 */
function normalsFor(
  mesh: SkinnedMesh,
  delta: Float32Array,
  relative: boolean,
): BufferAttribute | null {
  const position = mesh.geometry.getAttribute('position');
  const baseNormal = mesh.geometry.getAttribute('normal');
  const index = mesh.geometry.getIndex();
  if (!baseNormal || !index) return null;
  const count = position.count;

  const key = new Map<string, number[]>();
  for (let vertex = 0; vertex < count; vertex += 1) {
    const id = `${position.getX(vertex)},${position.getY(vertex)},${position.getZ(vertex)}`;
    const group = key.get(id);
    if (group) group.push(vertex); else key.set(id, [vertex]);
  }
  const groupOf = new Map<number, number[]>();
  for (const group of key.values()) for (const vertex of group) groupOf.set(vertex, group);

  const base = new Float32Array(count * 3);
  const moved = new Float32Array(count * 3);
  for (let vertex = 0; vertex < count; vertex += 1) {
    base[vertex * 3] = position.getX(vertex);
    base[vertex * 3 + 1] = position.getY(vertex);
    base[vertex * 3 + 2] = position.getZ(vertex);
    moved[vertex * 3] = base[vertex * 3] + delta[vertex * 3];
    moved[vertex * 3 + 1] = base[vertex * 3 + 1] + delta[vertex * 3 + 1];
    moved[vertex * 3 + 2] = base[vertex * 3 + 2] + delta[vertex * 3 + 2];
  }
  const before = smoothNormals(base, index, groupOf, count);
  const after = smoothNormals(moved, index, groupOf, count);

  const values = new Float32Array(count * 3);
  let touched = 0;
  for (let vertex = 0; vertex < count; vertex += 1) {
    const dx = after[vertex * 3] - before[vertex * 3];
    const dy = after[vertex * 3 + 1] - before[vertex * 3 + 1];
    const dz = after[vertex * 3 + 2] - before[vertex * 3 + 2];
    if (Math.abs(dx) < 1e-6 && Math.abs(dy) < 1e-6 && Math.abs(dz) < 1e-6) {
      // Untouched by the displacement. Under the absolute convention the slot
      // still has to name the normal the vertex already has.
      if (!relative) {
        values[vertex * 3] = baseNormal.getX(vertex);
        values[vertex * 3 + 1] = baseNormal.getY(vertex);
        values[vertex * 3 + 2] = baseNormal.getZ(vertex);
      }
      continue;
    }
    touched += 1;
    if (relative) {
      values[vertex * 3] = dx;
      values[vertex * 3 + 1] = dy;
      values[vertex * 3 + 2] = dz;
    } else {
      values[vertex * 3] = baseNormal.getX(vertex) + dx;
      values[vertex * 3 + 1] = baseNormal.getY(vertex) + dy;
      values[vertex * 3 + 2] = baseNormal.getZ(vertex) + dz;
    }
  }
  return touched ? new BufferAttribute(values, 3) : null;
}
