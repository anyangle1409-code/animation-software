import { readFileSync } from 'node:fs';
import { describe, it, expect } from 'vitest';
import { Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';

/**
 * Stage 1 of the curl realism layer: does the arm actually change shape with
 * flexion, and does it come back to the accepted body at Bottom?
 */
const rig = canonicalSkeleton;
const FRAMES: [string, number][] = [
  ['Bottom', 0],
  ['Mid lift', 1],
  ['Peak', 2.5],
  ['Mid lower', 4],
  ['Return', 5.5],
];

const load = async (id: string) => {
  const bytes = readFileSync(process.env.GLB!);
  const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  return retargetedCharacterSource({ id, label: id, data }).build(rig);
};

/** Local position with the active morph influences folded in, then skinned. */
function posed(mesh: SkinnedMesh, index: number, out: Vector3): Vector3 {
  const position = mesh.geometry.getAttribute('position');
  out.fromBufferAttribute(position, index);
  const morphs = mesh.geometry.morphAttributes.position ?? [];
  const influences = mesh.morphTargetInfluences ?? [];
  const relative = mesh.geometry.morphTargetsRelative === true;
  for (let slot = 0; slot < morphs.length; slot += 1) {
    const weight = influences[slot] ?? 0;
    if (!weight) continue;
    const morph = morphs[slot];
    if (relative) {
      out.x += morph.getX(index) * weight;
      out.y += morph.getY(index) * weight;
      out.z += morph.getZ(index) * weight;
    } else {
      out.x += (morph.getX(index) - position.getX(index)) * weight;
      out.y += (morph.getY(index) - position.getY(index)) * weight;
      out.z += (morph.getZ(index) - position.getZ(index)) * weight;
    }
  }
  mesh.applyBoneTransform(index, out);
  return mesh.localToWorld(out);
}

/** The bone carrying the most weight on a vertex, for region reporting. */
function dominant(mesh: SkinnedMesh, index: number): string {
  const skinIndex = mesh.geometry.getAttribute('skinIndex');
  const skinWeight = mesh.geometry.getAttribute('skinWeight');
  let best = -1;
  let bone = '?';
  for (let lane = 0; lane < 4; lane += 1) {
    const weight = skinWeight.getComponent(index, lane);
    if (weight > best) {
      best = weight;
      bone = mesh.skeleton.bones[skinIndex.getComponent(index, lane)]?.name ?? '?';
    }
  }
  return bone.replace(/^DEF-?/, '');
}

const setAmount = (character: Awaited<ReturnType<typeof load>>, amount: number) => {
  const control = character.deformation?.controls?.find((c) => c.id === 'muscleAmount');
  expect(control, 'muscleAmount control is present').toBeTruthy();
  control!.set(amount);
};

async function frames(amount: number) {
  const character = await load(`muscle-${amount}`);
  setAmount(character, amount);
  const clip = generateClip(rig, bicepCurl);
  const evaluation = new PoseEvaluation(rig);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  const out = new Map<string, Float64Array[]>();
  for (const [label, time] of FRAMES) {
    const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
    applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
    const perMesh: Float64Array[] = [];
    const point = new Vector3();
    for (const mesh of character.meshes as SkinnedMesh[]) {
      mesh.skeleton.update();
      mesh.updateWorldMatrix(true, false);
      const count = mesh.geometry.getAttribute('position').count;
      const values = new Float64Array(count * 3);
      for (let index = 0; index < count; index += 1) {
        posed(mesh, index, point);
        values[index * 3] = point.x;
        values[index * 3 + 1] = point.y;
        values[index * 3 + 2] = point.z;
      }
      perMesh.push(values);
    }
    out.set(label, perMesh);
  }
  return { character, out };
}

describe('arm muscle deformation', () => {
  it('fills toward Peak, returns at Bottom, and moves nothing outside the arm', async () => {
    const off = await frames(0);
    const on = await frames(1);
    const meshes = on.character.meshes as SkinnedMesh[];

    console.log('\nMORPH INVENTORY');
    for (const mesh of meshes) {
      const names = (mesh.geometry.morphAttributes.position ?? []).map((m) => m.name);
      const normals = (mesh.geometry.morphAttributes.normal ?? []).length;
      console.log(`  ${mesh.name}: ${names.length} position morphs [${names.join(', ')}], ${normals} normal morphs`);
      expect(normals === 0 || normals === names.length, 'normal slots cover every position slot').toBe(true);
    }

    // A normal morph that reaches past the displacement rewrites shading on
    // parts of the body the layer has no business touching — and because the
    // asset stores unwelded normals with deliberate hard edges at the scalp and
    // neck, that shows up as crumpled faceting on the face, not as a subtle
    // difference. Guarded per slot, by region.
    console.log('\nNORMAL MORPH REACH (non-zero normal delta, by dominant bone)');
    for (const mesh of meshes) {
      const positions = mesh.geometry.morphAttributes.position ?? [];
      const normals = mesh.geometry.morphAttributes.normal ?? [];
      const relative = mesh.geometry.morphTargetsRelative === true;
      const baseNormal = mesh.geometry.getAttribute('normal');
      console.log(`  (${mesh.name}: morphTargetsRelative=${relative})`);
      for (let slot = 0; slot < normals.length; slot += 1) {
        const normal = normals[slot];
        const regions = new Map<string, number>();
        for (let index = 0; index < normal.count; index += 1) {
          // Under the absolute convention three.js applies
          // `(morphNormal - normal) * influence`, so a slot that equals the
          // base normal is the no-change case, not a zero vector.
          const length = relative
            ? Math.hypot(normal.getX(index), normal.getY(index), normal.getZ(index))
            : Math.hypot(
                normal.getX(index) - baseNormal.getX(index),
                normal.getY(index) - baseNormal.getY(index),
                normal.getZ(index) - baseNormal.getZ(index),
              );
          if (length < 1e-6) continue;
          const region = dominant(mesh, index);
          regions.set(region, (regions.get(region) ?? 0) + 1);
        }
        const name = positions[slot]?.name ?? `slot ${slot}`;
        const listed = [...regions].sort((x, y) => y[1] - x[1]).map(([r, n]) => `${r}:${n}`);
        console.log(`  ${name.padEnd(28)} ${listed.length ? listed.join(' ') : '(none)'}`);
        const stray = [...regions.keys()].filter((region) => !/^(upper_?arm|forearm|shoulder|hand|breast)/i.test(region));
        expect(stray, `${name} does not reshade outside the arm`).toEqual([]);
      }
    }

    console.log('\nPER-FRAME SHAPE CHANGE (layer on vs layer off, same pose)');
    console.log('frame | vertices moved | worst mm | region of worst | mean mm over moved');
    const movedRegions = new Map<string, number>();
    for (const [label] of FRAMES) {
      const a = off.out.get(label)!;
      const b = on.out.get(label)!;
      let moved = 0;
      let worst = 0;
      let worstRegion = '—';
      let total = 0;
      for (let m = 0; m < a.length; m += 1) {
        const count = a[m].length / 3;
        for (let index = 0; index < count; index += 1) {
          const d = Math.hypot(
            b[m][index * 3] - a[m][index * 3],
            b[m][index * 3 + 1] - a[m][index * 3 + 1],
            b[m][index * 3 + 2] - a[m][index * 3 + 2],
          ) * 1000;
          if (d <= 1e-6) continue;
          moved += 1;
          total += d;
          if (d > worst) {
            worst = d;
            worstRegion = dominant(meshes[m], index);
          }
          if (label === 'Peak') {
            const region = dominant(meshes[m], index);
            movedRegions.set(region, Math.max(movedRegions.get(region) ?? 0, d));
          }
        }
      }
      console.log(
        `${label.padEnd(9)} | ${String(moved).padStart(14)} | ${worst.toFixed(3).padStart(8)} | ${worstRegion.padEnd(15)} | ${(moved ? total / moved : 0).toFixed(3)}`,
      );
      if (label === 'Bottom' || label === 'Return') {
        expect(worst, `${label} is the accepted static body`).toBeLessThan(1e-6);
      }
    }

    console.log('\nREGIONS TOUCHED AT PEAK (worst mm per dominant bone)');
    for (const [region, worst] of [...movedRegions].sort((a, b) => b[1] - a[1])) {
      console.log(`  ${region.padEnd(18)} ${worst.toFixed(3)} mm`);
    }
    // The layer is *meant* to reach a little past the arm chain: the doc asks
    // it to blend into the deltoid and armpit rather than stop at a skin-weight
    // boundary, and a hard zero there is exactly how a crease gets made. So the
    // guard is on size, not on membership — a neighbouring region may feather,
    // it may not bulge. The hand is held tighter still, because the grip is
    // measured off finger vertices.
    const allowed = /^(upper_?arm|forearm|shoulder)/i;
    const leaked = [...movedRegions].filter(([region]) => !allowed.test(region));
    console.log(`  outside upper arm / forearm / shoulder: ${leaked.length ? leaked.map(([r, d]) => `${r} ${d.toFixed(3)} mm`).join(', ') : 'none'}`);
    for (const [region, worst] of leaked) {
      const limit = /hand|finger|thumb|f_/i.test(region) ? 0.15 : 0.5;
      expect(worst, `${region} feathers rather than bulges`).toBeLessThan(limit);
    }

    // Girth: the circumference of the biceps belly ring, as a muscle would be
    // measured with a tape. Radial distance from the humerus axis, summed.
    // Three rings, not one: a fill that reads the same near the deltoid and the
    // elbow as at the belly is a fatter arm, not a contracting muscle.
    const RINGS: [string, number, number][] = [
      ['proximal', 0.16, 0.26],
      ['belly', 0.4, 0.56],
      ['distal', 0.7, 0.8],
    ];
    console.log('\nANTERIOR RADIUS FROM THE HUMERUS AXIS, THREE RINGS');
    console.log('frame | side | ring     | off mm | on mm | Δ mm | Δ %');
    for (const [label] of FRAMES) {
      for (const side of ['l', 'r'] as const) {
      for (const [ring, lo, hi] of RINGS) {
        const upper = on.character.boneByName.get(`upperarm_${side}` as never) as
          | { matrixWorld: { elements: number[] } }
          | undefined;
        const lower = on.character.boneByName.get(`forearm_${side}` as never) as
          | { matrixWorld: { elements: number[] } }
          | undefined;
        if (!upper || !lower) continue;
        const shoulder = new Vector3().setFromMatrixPosition(upper.matrixWorld as never);
        const elbow = new Vector3().setFromMatrixPosition(lower.matrixWorld as never);
        const axis = elbow.clone().sub(shoulder);
        const length = axis.length();
        axis.divideScalar(length);
        const measure = (values: Float64Array[]) => {
          let sum = 0;
          let count = 0;
          const point = new Vector3();
          for (let m = 0; m < values.length; m += 1) {
            const total = values[m].length / 3;
            for (let index = 0; index < total; index += 1) {
              if (!/^upper_?arm/i.test(dominant(meshes[m], index))) continue;
              point.set(values[m][index * 3], values[m][index * 3 + 1], values[m][index * 3 + 2]);
              const along = point.clone().sub(shoulder);
              const t = along.dot(axis) / length;
              if (t < lo || t > hi) continue;
              const radial = along.clone().addScaledVector(axis, -along.dot(axis));
              // Anterior half only: that is where the biceps is.
              if (radial.clone().normalize().dot(new Vector3(0, 0, 1)) < 0.3) continue;
              sum += radial.length();
              count += 1;
            }
          }
          return count ? (sum / count) * 1000 : 0;
        };
        const before = measure(off.out.get(label)!);
        const after = measure(on.out.get(label)!);
        console.log(
          `${label.padEnd(9)} | ${side}    | ${ring.padEnd(8)} | ${before.toFixed(2).padStart(6)} | ${after.toFixed(2).padStart(6)} | ${(after - before).toFixed(2).padStart(6)} | ${before ? (((after - before) / before) * 100).toFixed(1) : '—'}`,
        );
      }
      }
    }

    // Shortening: the length of the belly *bump*, as full width at half
    // maximum of the anterior radius profile along the humerus. Percentile
    // spread of the moved vertex set cannot show this — its edges are exactly
    // where the axial pull is deliberately zero, so they are pinned whatever
    // the interior does. FWHM measures the bump and ignores the tails.
    console.log('\nBICEPS BELLY WORKING LENGTH (axial gap between two fixed bands near the belly ends)');
    console.log('frame | side | off mm | on mm | Δ mm | Δ %');
    for (const [label] of FRAMES) {
      for (const side of ['l', 'r'] as const) {
        const upper = on.character.boneByName.get(`upperarm_${side}` as never) as never;
        const lower = on.character.boneByName.get(`forearm_${side}` as never) as never;
        if (!upper || !lower) continue;
        const shoulder = new Vector3().setFromMatrixPosition((upper as { matrixWorld: never }).matrixWorld);
        const elbow = new Vector3().setFromMatrixPosition((lower as { matrixWorld: never }).matrixWorld);
        const axis = elbow.clone().sub(shoulder).normalize();
        const length = elbow.distanceTo(shoulder);
        /** Mean anterior radius in 40 bins along the humerus, then its FWHM. */
        const profile = (values: Float64Array[]) => {
          const BINS = 40;
          const sum = new Float64Array(BINS);
          const hits = new Int32Array(BINS);
          const point = new Vector3();
          for (let m = 0; m < values.length; m += 1) {
            const total = values[m].length / 3;
            for (let index = 0; index < total; index += 1) {
              if (!/^upper_?arm/i.test(dominant(meshes[m], index))) continue;
              point.set(values[m][index * 3], values[m][index * 3 + 1], values[m][index * 3 + 2]);
              const along = point.sub(shoulder);
              const t = along.dot(axis) / length;
              if (t < 0 || t >= 1) continue;
              const radial = along.clone().addScaledVector(axis, -along.dot(axis));
              if (radial.clone().normalize().dot(new Vector3(0, 0, 1)) < 0.5) continue;
              const bin = Math.min(BINS - 1, Math.floor(t * BINS));
              sum[bin] += radial.length();
              hits[bin] += 1;
            }
          }
          return Array.from({ length: BINS }, (_, bin) =>
            hits[bin] ? (sum[bin] / hits[bin]) * 1000 : NaN);
        };
        // Two fixed bands near the ends of the shortening window, and the axial
        // gap between their means. No threshold is involved, so unlike a
        // half-maximum width this cannot confuse a taller bump for a longer
        // one — it reports only how much closer the belly's ends became.
        const bandMean = (values: Float64Array[], lo: number, hi: number) => {
          let sum = 0;
          let count = 0;
          const point = new Vector3();
          for (let m = 0; m < values.length; m += 1) {
            const total = values[m].length / 3;
            for (let index = 0; index < total; index += 1) {
              if (!/^upper_?arm/i.test(dominant(meshes[m], index))) continue;
              point.set(values[m][index * 3], values[m][index * 3 + 1], values[m][index * 3 + 2]);
              const along = point.sub(shoulder);
              const t = along.dot(axis) / length;
              if (t < lo || t > hi) continue;
              const radial = along.clone().addScaledVector(axis, -along.dot(axis));
              if (radial.clone().normalize().dot(new Vector3(0, 0, 1)) < 0.4) continue;
              sum += along.dot(axis);
              count += 1;
            }
          }
          return count ? sum / count : NaN;
        };
        const gap = (values: Float64Array[]) =>
          (bandMean(values, 0.68, 0.76) - bandMean(values, 0.3, 0.38)) * 1000;
        const before = gap(off.out.get(label)!);
        const after = gap(on.out.get(label)!);
        console.log(
          `${label.padEnd(9)} | ${side}    | ${before.toFixed(2).padStart(6)} | ${after.toFixed(2).padStart(6)} | ${(after - before).toFixed(2).padStart(6)} | ${before ? (((after - before) / before) * 100).toFixed(2) : '—'}`,
        );
      }
    }
  }, 240_000);
});
