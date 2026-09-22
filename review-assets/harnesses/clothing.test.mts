import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { airSquat } from '../../src/exercises/definitions/airSquat';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { pullUp } from '../../src/exercises/definitions/pullUp';
import { pushUp } from '../../src/exercises/definitions/pushUp';
import { shoulderPress } from '../../src/exercises/definitions/shoulderPress';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';

/**
 * Does any skin come through the shorts, in any pose?
 *
 * For every piece of skin the garment covers, this finds the closest point on
 * the garment's own surface — point to triangle, not point to vertex, because
 * the garment's vertices are 15-25 mm apart and a thigh can push between two of
 * them — and asks which side of the cloth that skin is on. Positive means the
 * skin is behind the cloth, which is the only acceptable answer.
 *
 * Skin near the waistband and the hems is excluded: it is outside the garment
 * by design, and counting it would report the leg openings as failures.
 */

const rig = canonicalSkeleton;

function posedPositions(mesh: SkinnedMesh): Float32Array {
  mesh.skeleton.update();
  const count = mesh.geometry.getAttribute('position').count;
  const out = new Float32Array(count * 3);
  const point = new Vector3();
  for (let vertex = 0; vertex < count; vertex += 1) {
    mesh.getVertexPosition(vertex, point);
    out[vertex * 3] = point.x;
    out[vertex * 3 + 1] = point.y;
    out[vertex * 3 + 2] = point.z;
  }
  return out;
}

const a = new Vector3();
const b = new Vector3();
const c = new Vector3();
const point = new Vector3();
const ab = new Vector3();
const ac = new Vector3();
const ap = new Vector3();
const bp = new Vector3();
const cp = new Vector3();
const closest = new Vector3();

/** Closest point on a triangle to a point, in the triangle's own plane logic. */
function closestOnTriangle(target: Vector3): Vector3 {
  ab.subVectors(b, a);
  ac.subVectors(c, a);
  ap.subVectors(target, a);
  const d1 = ab.dot(ap);
  const d2 = ac.dot(ap);
  if (d1 <= 0 && d2 <= 0) return closest.copy(a);

  bp.subVectors(target, b);
  const d3 = ab.dot(bp);
  const d4 = ac.dot(bp);
  if (d3 >= 0 && d4 <= d3) return closest.copy(b);

  const vc = d1 * d4 - d3 * d2;
  if (vc <= 0 && d1 >= 0 && d3 <= 0) {
    return closest.copy(a).addScaledVector(ab, d1 / (d1 - d3));
  }

  cp.subVectors(target, c);
  const d5 = ab.dot(cp);
  const d6 = ac.dot(cp);
  if (d6 >= 0 && d5 <= d6) return closest.copy(c);

  const vb = d5 * d2 - d1 * d6;
  if (vb <= 0 && d2 >= 0 && d6 <= 0) {
    return closest.copy(a).addScaledVector(ac, d2 / (d2 - d6));
  }

  const va = d3 * d6 - d5 * d4;
  if (va <= 0 && d4 - d3 >= 0 && d5 - d6 >= 0) {
    return closest
      .copy(b)
      .addScaledVector(new Vector3().subVectors(c, b), (d4 - d3) / (d4 - d3 + (d5 - d6)));
  }

  const denominator = 1 / (va + vb + vc);
  return closest
    .copy(a)
    .addScaledVector(ab, vb * denominator)
    .addScaledVector(ac, vc * denominator);
}

describe('shorts against the body', () => {
  it('keeps the skin behind the cloth in every tested pose', async () => {
    const glbPath = process.env.GLB!;
    const bytes = readFileSync(glbPath);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const source = retargetedCharacterSource({ id: 'cloth', label: 'Clothing', data });
    const character = await source.build(rig);

    const shorts = character.meshes.find((mesh) => /shorts/i.test(mesh.name))!;
    const body = character.meshes.find((mesh) => !/shorts/i.test(mesh.name))!;
    expect(shorts).toBeTruthy();
    expect(body).toBeTruthy();

    const correspondence: [number, number][][] = JSON.parse(
      readFileSync(`${glbPath}.correspondence.json`, 'utf8'),
    );
    const outerCount = correspondence.length / 2;
    const shortsIndex = shorts.geometry.getIndex()!;
    // Only the outer shell; the lining sits inside it on purpose.
    const outerTriangles: [number, number, number][] = [];
    for (let corner = 0; corner < shortsIndex.count; corner += 3) {
      const set: [number, number, number] = [
        shortsIndex.getX(corner),
        shortsIndex.getX(corner + 1),
        shortsIndex.getX(corner + 2),
      ];
      if (set.every((vertex) => vertex < outerCount)) outerTriangles.push(set);
    }

    // Skin the garment is meant to cover, minus a margin at the cut edges.
    const bodyPosition = body.geometry.getAttribute('position');
    const sources = new Set<number>();
    for (const entry of correspondence) for (const [vertex] of entry) sources.add(vertex);
    const covered = [...sources].filter((vertex) => {
      const y = bodyPosition.getY(vertex);
      return y > 0.845 && y < 1.15;
    });

    console.log(
      `\ngarment ${shorts.geometry.getAttribute('position').count} vertices, ` +
        `${shortsIndex.count / 3} triangles (${outerTriangles.length} on the outer shell)`,
    );
    console.log(`skin sampled under the garment: ${covered.length} vertices`);

    const scale = source.lastReport!.scale;
    const mm = (value: number) => value * scale * 1000;

    const summary: Record<string, unknown> = {};
    const frames = 13;

    for (const definition of [airSquat, bicepCurl, shoulderPress, pushUp, pullUp]) {
      const clip = generateClip(rig, definition);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);

      let worst = Infinity;
      let worstAt = 0;
      let worstVertex = -1;
      let breaches = 0;
      let samples = 0;
      let tightest = Infinity;

      for (let step = 0; step <= frames; step += 1) {
        const time = (clip.duration * step) / frames;
        const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
        character.object.updateMatrixWorld(true);

        const bodyPosed = posedPositions(body);
        const shortsPosed = posedPositions(shorts);

        for (const vertex of covered) {
          point.set(bodyPosed[vertex * 3], bodyPosed[vertex * 3 + 1], bodyPosed[vertex * 3 + 2]);
          let bestDistance = Infinity;
          let bestDepth = 0;
          for (const [one, two, three] of outerTriangles) {
            a.set(shortsPosed[one * 3], shortsPosed[one * 3 + 1], shortsPosed[one * 3 + 2]);
            b.set(shortsPosed[two * 3], shortsPosed[two * 3 + 1], shortsPosed[two * 3 + 2]);
            c.set(shortsPosed[three * 3], shortsPosed[three * 3 + 1], shortsPosed[three * 3 + 2]);
            // Cheap reject before the exact test.
            const rough = point.distanceToSquared(a);
            if (rough > bestDistance + 0.02) continue;
            const found = closestOnTriangle(point);
            const distance = point.distanceToSquared(found);
            if (distance >= bestDistance) continue;
            bestDistance = distance;
            const normal = new Vector3()
              .subVectors(b, a)
              .cross(new Vector3().subVectors(c, a))
              .normalize();
            bestDepth = -new Vector3().subVectors(point, found).dot(normal);
          }
          if (bestDistance === Infinity) continue;
          samples += 1;
          tightest = Math.min(tightest, Math.sqrt(bestDistance));
          if (bestDepth < worst) {
            worst = bestDepth;
            worstAt = time;
            worstVertex = vertex;
          }
          if (bestDepth < 0) breaches += 1;
        }
      }

      summary[definition.id] = {
        worstDepthMm: Number(mm(worst).toFixed(2)),
        worstAt: Number(worstAt.toFixed(2)),
        worstVertex,
        tightestGapMm: Number(mm(tightest).toFixed(2)),
        breaches,
        samples,
      };
      console.log(
        `  ${definition.id.padEnd(24)} worst ${mm(worst).toFixed(2).padStart(7)} mm @${worstAt.toFixed(2)}s (v${worstVertex})` +
          `   tightest gap ${mm(tightest).toFixed(2).padStart(6)} mm   breaches ${breaches}/${samples}`,
      );
    }

    console.log('\nCLOTHING_CONTAINMENT\n' + JSON.stringify(summary, null, 1));
    character.dispose();
  }, 1_800_000);
});
