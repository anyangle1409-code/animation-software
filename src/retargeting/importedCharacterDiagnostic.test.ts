import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  HgBone,
} from '../core/sceneGraph';
import {
  HgBufferAttribute,
  HgBufferGeometry,
  HgSkeleton,
  HgSkinnedMesh,
  HgStandardMaterial,
} from '../core/sceneSkin';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import type { StudioClip } from '../animation/clip';
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
import type { CharacterBuild, Side } from '../character/types';
import { equipmentSocket } from '../equipment/library';
import { handAttachmentLocalMatrix } from '../equipment/attach';
import { HgMat4, HgVec3 } from '../core/linearMath';

/**
 * Optional diagnostic for a supplied imported character.
 *
 * It is intentionally skipped in ordinary CI because the real asset is not
 * committed to the repository.  To run it locally:
 *
 *   CHARACTER_DIAGNOSTIC_GLB=/absolute/path/model.glb npx vitest run \
 *     src/retargeting/importedCharacterDiagnostic.test.ts --reporter=verbose
 *
 * The test goes through the same preserved-import, resolveFrame and
 * applyCharacterPose path the Studio uses, samples the five representative
 * exercise families, and prints mesh strain, hand-frame continuity and
 * dumbbell-handle/skin clearance.  It is
 * a measurement harness, not a substitute for visual approval.
 */

const path = process.env.CHARACTER_DIAGNOSTIC_GLB;
const rig = canonicalSkeleton;
const definitions = [airSquat, bicepCurl, shoulderPress, pushUp, pullUp];
const fractions = [0, 0.2, 0.45, 0.7, 0.95];

interface EdgeSet {
  edges: [number, number][];
  rest: number[];
}

function meshEdges(mesh: HgSkinnedMesh): EdgeSet {
  const position = mesh.geometry.getAttribute('position');
  const index = mesh.geometry.getIndex();
  if (!index) throw new Error(`${mesh.name || 'mesh'} is not indexed`);

  const edges: [number, number][] = [];
  const rest: number[] = [];
  const seen = new Set<number>();
  const one = new HgVec3();
  const two = new HgVec3();

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

function strain(mesh: HgSkinnedMesh, set: EdgeSet) {
  const one = new HgVec3();
  const two = new HgVec3();
  const ratios: number[] = [];

  mesh.skeleton.update();
  set.edges.forEach(([a, b], slot) => {
    // Three's vertex evaluator applies both morph targets and skinning in the
    // rendered order. applyBoneTransform alone silently ignores correctives.
    mesh.getVertexPosition(a, one);
    mesh.getVertexPosition(b, two);
    ratios.push(one.distanceTo(two) / set.rest[slot]);
  });

  // A loop, not Math.max(...ratios): one ratio per edge, and a denser mesh
  // can have more edges than a call can safely take as arguments.
  let maximum = -Infinity;
  let minimum = Infinity;
  for (const ratio of ratios) {
    if (ratio > maximum) maximum = ratio;
    if (ratio < minimum) minimum = ratio;
  }
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

const DUMBBELL_HANDLE_RADIUS = 0.015;
const DUMBBELL_HANDLE_HALF_LENGTH = 0.06;

/**
 * Measure the visible imported skin against the exact handle transform used by
 * the viewport. This is diagnostic only: a sparse mesh can miss a triangle-level
 * intersection even when no vertex enters the cylinder, so the number is useful
 * for A/B calibration but is not a pass/fail threshold. Negative clearance means
 * at least one posed skin vertex is inside the 15 mm-radius handle volume.
 */
function dumbbellHandleSkinClearance(character: CharacterBuild, clip: StudioClip) {
  const result: Record<Side, { penetratingVertices: number; minClearanceMm: number | null; sampledVertices: number } | null> = {
    l: null,
    r: null,
  };
  if (!character.handMatrix) return result;

  const vertex = new HgVec3();
  const handleLocal = new HgVec3();

  for (const side of ['l', 'r'] as const) {
    const instance = clip.equipment.find(
      (entry) =>
        entry.kind === 'dumbbell' &&
        entry.attachment.mode === 'hand' &&
        entry.attachment.side === side,
    );
    if (!instance || instance.attachment.mode !== 'hand') continue;

    const hand = character.handMatrix(side, new HgMat4());
    if (!hand) continue;
    const socket = equipmentSocket(instance.kind, instance.attachment.socket);
    const grip = instance.attachment.gripOffset ?? { x: 0, y: 0.045, z: 0 };
    const equipment = hand.clone().multiply(
      handAttachmentLocalMatrix(
        grip,
        socket?.position ?? { x: 0, y: 0, z: 0 },
      ),
    );
    const toHandle = equipment.clone().invert();

    let penetratingVertices = 0;
    let sampledVertices = 0;
    let minClearance = Number.POSITIVE_INFINITY;

    for (const mesh of character.meshes) {
      mesh.skeleton.update();
      mesh.updateWorldMatrix(true, false);
      const count = mesh.geometry.getAttribute('position').count;
      for (let index = 0; index < count; index += 1) {
        mesh.getVertexPosition(index, vertex);
        handleLocal.copy(vertex).applyMatrix4(mesh.matrixWorld).applyMatrix4(toHandle);
        if (Math.abs(handleLocal.z) > DUMBBELL_HANDLE_HALF_LENGTH) continue;
        sampledVertices += 1;
        const clearance = Math.hypot(handleLocal.x, handleLocal.y) - DUMBBELL_HANDLE_RADIUS;
        minClearance = Math.min(minClearance, clearance);
        if (clearance < 0) penetratingVertices += 1;
      }
    }

    result[side] = {
      penetratingVertices,
      minClearanceMm: Number.isFinite(minClearance) ? Number((minClearance * 1000).toFixed(3)) : null,
      sampledVertices,
    };
  }

  return result;
}

const supplied = path ? describe : describe.skip;

describe('strain measurement includes pose shapes', () => {
  for (const relative of [true, false]) {
    it(`measures ${relative ? 'relative' : 'absolute'} morphs before skinning`, () => {
      const geometry = new HgBufferGeometry();
      geometry.setAttribute('position', new HgBufferAttribute(new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0]), 3));
      geometry.setIndex([0, 1, 2]);
      geometry.setAttribute('skinIndex', new HgBufferAttribute(new Float32Array(12), 4));
      geometry.setAttribute('skinWeight', new HgBufferAttribute(new Float32Array([1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]), 4));
      geometry.morphTargetsRelative = relative;
      geometry.morphAttributes.position = [new HgBufferAttribute(
        new Float32Array(
          relative
            ? [0, 0, 0, 1, 0, 0, 0, 0, 0]
            : [0, 0, 0, 2, 0, 0, 0, 1, 0],
        ),
        3,
      )];
      const mesh = new HgSkinnedMesh(geometry, new HgStandardMaterial());
      const bone = new HgBone();
      mesh.add(bone);
      mesh.bind(new HgSkeleton([bone]));
      mesh.updateMorphTargets();
      const edges = meshEdges(mesh);
      expect(strain(mesh, edges).max).toBeCloseTo(1);
      mesh.morphTargetInfluences![0] = 1;
      expect(strain(mesh, edges).max).toBeCloseTo(2);
      mesh.morphTargetInfluences![0] = 0;
      expect(strain(mesh, edges).max).toBeCloseTo(1);
      geometry.dispose();
      (mesh.material as HgStandardMaterial).dispose();
    });
  }
});

supplied('imported-character diagnostic', () => {
  it('measures representative whole-body exercises through the current importer', async () => {
    const bytes = readFileSync(path!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const source = retargetedCharacterSource({
      id: 'imported-diagnostic',
      label: 'Imported diagnostic character',
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
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
        character.object.updateMatrixWorld(true);

        const meshStats = character.meshes.map((mesh) => ({
          mesh: mesh.name,
          ...strain(mesh, edgeSets.get(mesh)!),
        }));

        const hands: Record<string, number[] | null> = {};
        for (const side of ['l', 'r'] as const) {
          const matrix = character.handMatrix?.(side, new HgMat4()) ?? null;
          hands[side] = matrix
            ? [matrix.elements[12], matrix.elements[13], matrix.elements[14]]
                .map((value) => Number(value.toFixed(5)))
            : null;
        }

        const handleSkin = dumbbellHandleSkinClearance(character, clip);
        samples.push({ fraction, meshStats, hands, handleSkin });

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

    console.log('\nIMPORTED_CHARACTER_DIAGNOSTIC');
    console.log(JSON.stringify({ import: report, exercises: results }, null, 2));
    character.dispose();
  }, 60_000);
});
