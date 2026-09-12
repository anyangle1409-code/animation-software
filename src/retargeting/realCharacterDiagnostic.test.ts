import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { airSquat } from '../exercises/definitions/airSquat';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { pullUp } from '../exercises/definitions/pullUp';
import { pushUp } from '../exercises/definitions/pushUp';
import { shoulderPress } from '../exercises/definitions/shoulderPress';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { applyCharacterPose } from '../character/pose';
import { retargetedCharacterSource } from '../character/retargetSource';

/**
 * Optional production-path diagnostic for a real imported character.
 *
 * It is intentionally skipped in ordinary CI because the real asset is not
 * committed to the repository.  To run it locally:
 *
 *   REAL_CHARACTER_GLB=/absolute/path/model.glb npx vitest run \
 *     src/retargeting/realCharacterDiagnostic.test.ts --reporter=verbose
 *
 * The test goes through the same preserved-import, resolveFrame and
 * applyCharacterPose path the Studio uses, samples the five representative
 * exercise families, and prints mesh strain plus hand-frame continuity.  It is
 * a measurement harness, not a substitute for visual approval.
 */

const path = process.env.REAL_CHARACTER_GLB;
const rig = canonicalSkeleton;
const definitions = [airSquat, bicepCurl, shoulderPress, pushUp, pullUp];
const fractions = [0, 0.2, 0.45, 0.7, 0.95];

interface EdgeSet {
  edges: [number, number][];
  rest: number[];
}

function meshEdges(mesh: SkinnedMesh): EdgeSet {
  const position = mesh.geometry.getAttribute('position');
  const index = mesh.geometry.getIndex();
  if (!index) throw new Error(`${mesh.name || 'mesh'} is not indexed`);

  const edges: [number, number][] = [];
  const rest: number[] = [];
  const seen = new Set<number>();
  const one = new Vector3();
  const two = new Vector3();

  for (let triangle = 0; triangle < index.count; triangle += 3) {
    const corners = [index.getX(triangle), index.getX(triangle + 1), index.getX(triangle + 2)];
    for (let slot = 0; slot < 3; slot += 1) {
      const a = corners[slot];
      const b = corners[(slot + 1) % 3];
      const lo = Math.min(a, b);
      const hi = Math.max(a, b);
      const key = lo * position.count + hi;
      if (seen.has(key)) continue;
      seen.add(key);
      one.fromBufferAttribute(position, lo);
      two.fromBufferAttribute(position, hi);
      const length = one.distanceTo(two);
      if (length < 1e-8) continue;
      edges.push([lo, hi]);
      rest.push(length);
    }
  }

  return { edges, rest };
}

function percentile(values: number[], fraction: number): number {
  if (values.length === 0) return 1;
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.min(sorted.length - 1, Math.floor((sorted.length - 1) * fraction))];
}

function strain(mesh: SkinnedMesh, set: EdgeSet) {
  const position = mesh.geometry.getAttribute('position');
  const one = new Vector3();
  const two = new Vector3();
  const ratios: number[] = [];

  mesh.skeleton.update();
  set.edges.forEach(([a, b], slot) => {
    one.fromBufferAttribute(position, a);
    two.fromBufferAttribute(position, b);
    mesh.applyBoneTransform(a, one);
    mesh.applyBoneTransform(b, two);
    ratios.push(one.distanceTo(two) / set.rest[slot]);
  });

  const maximum = Math.max(...ratios);
  const minimum = Math.min(...ratios);
  return {
    max: maximum,
    p99: percentile(ratios, 0.99),
    p95: percentile(ratios, 0.95),
    min: minimum,
    over2x: ratios.filter((value) => value > 2).length,
    over3x: ratios.filter((value) => value > 3).length,
    underHalf: ratios.filter((value) => value < 0.5).length,
  };
}

const real = path ? describe : describe.skip;

real('real imported-character production diagnostic', () => {
  it('measures representative whole-body exercises through the production importer', async () => {
    const bytes = readFileSync(path!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const source = retargetedCharacterSource({
      id: 'real-diagnostic',
      label: 'Real diagnostic character',
      data,
    });
    const character = await source.build(rig);
    const report = source.lastReport!;

    expect(report.mapping.missingRequired).toEqual([]);
    expect(character.meshes.length).toBeGreaterThan(0);

    const edgeSets = new Map(character.meshes.map((mesh) => [mesh, meshEdges(mesh)]));
    const results: Record<string, unknown[]> = {};

    for (const definition of definitions) {
      const clip = generateClip(rig, definition);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const samples: unknown[] = [];

      for (const fraction of fractions) {
        const frame = resolveFrame(rig, evaluation, clip, clip.duration * fraction, { anchors });
        applyCharacterPose(character, rig, frame.pose, evaluation);
        character.object.updateMatrixWorld(true);

        const meshStats = character.meshes.map((mesh) => ({
          mesh: mesh.name,
          ...strain(mesh, edgeSets.get(mesh)!),
        }));

        const hands: Record<string, number[] | null> = {};
        for (const side of ['l', 'r'] as const) {
          const matrix = character.handMatrix?.(side, new Matrix4()) ?? null;
          hands[side] = matrix
            ? new Vector3().setFromMatrixPosition(matrix).toArray().map((value) => Number(value.toFixed(5)))
            : null;
        }

        samples.push({ fraction, meshStats, hands });

        for (const stat of meshStats) {
          expect(Number.isFinite(stat.max)).toBe(true);
          expect(Number.isFinite(stat.min)).toBe(true);
          // Catastrophic guard only.  The detailed numbers are printed for
          // review; moderate deformation is judged per anatomical region.
          expect(stat.max, `${definition.id} ${stat.mesh} ${fraction}`).toBeLessThan(10);
        }
      }
      results[definition.id] = samples;
    }

    console.log('\nREAL_CHARACTER_DIAGNOSTIC');
    console.log(JSON.stringify({ import: report, exercises: results }, null, 2));
    character.dispose();
  }, 60_000);
});
