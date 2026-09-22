import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { pullUp } from '../../src/exercises/definitions/pullUp';
import { pushUp } from '../../src/exercises/definitions/pushUp';
import { shoulderPress } from '../../src/exercises/definitions/shoulderPress';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';
import type { CharacterBuild, Side } from '../../src/character/types';
import { equipmentSocket } from '../../src/equipment/library';
import { handAttachmentMatrix } from '../../src/export/clipBuilder';
import { measureGripFit } from '../../src/equipment/gripDiagnostics';

/**
 * Measurement harness for the hand/wrist weight repair.
 *
 * Everything here goes through the same preserved-import, resolveFrame and
 * applyCharacterPose path the Studio uses, so a number measured here is a
 * number about the production surface — not about a re-exported copy of it.
 */

const glbPath = process.env.GLB!;
const rig = canonicalSkeleton;

/** Equilateral is 1; a collapsing triangle grows without bound. */
function aspect(a: Vector3, b: Vector3, c: Vector3): number {
  const ab = a.distanceTo(b);
  const bc = b.distanceTo(c);
  const ca = c.distanceTo(a);
  const area = triangleArea(a, b, c);
  if (area < 1e-14) return Infinity;
  // Normalised so an equilateral triangle scores 1 and a collapsing one grows.
  const longest = Math.max(ab, bc, ca);
  return (3 * longest * longest) / (4 * Math.sqrt(3) * area);
}

function triangleArea(a: Vector3, b: Vector3, c: Vector3): number {
  const u = new Vector3().subVectors(b, a);
  const v = new Vector3().subVectors(c, a);
  return u.cross(v).length() / 2;
}

function percentile(values: number[], fraction: number): number {
  if (values.length === 0) return 1;
  const sorted = [...values].sort((x, y) => x - y);
  return sorted[Math.min(sorted.length - 1, Math.floor((sorted.length - 1) * fraction))];
}

/** Which source bones a vertex is actually weighted to, by name. */
function vertexBones(mesh: SkinnedMesh): string[][] {
  const skinIndex = mesh.geometry.getAttribute('skinIndex');
  const skinWeight = mesh.geometry.getAttribute('skinWeight');
  const names = mesh.skeleton.bones.map((bone) => bone.name);
  const out: string[][] = [];
  for (let vertex = 0; vertex < skinIndex.count; vertex += 1) {
    const carried: string[] = [];
    for (let lane = 0; lane < 4; lane += 1) {
      const weight = skinWeight.getComponent(vertex, lane);
      if (weight > 1e-5) carried.push(names[skinIndex.getComponent(vertex, lane)]);
    }
    out.push(carried);
  }
  return out;
}

// three's GLTFLoader sanitises node names, so `DEF-hand.L` arrives as
// `DEF-handL`. Everything here matches the sanitised form.
const RING_PAIRS: [string, string, string][] = ['L', 'R'].flatMap((side) => [
  ...['index', 'middle', 'ring', 'pinky'].map(
    (digit) => [`DEF-hand${side}`, `DEF-f_${digit}01${side}`, `mcp-${digit}.${side}`] as [string, string, string],
  ),
  [`DEF-forearm${side}001`, `DEF-hand${side}`, `wrist.${side}`] as [string, string, string],
]);

const HAND_AREA = /^DEF-(hand|f_index|f_middle|f_ring|f_pinky|thumb|palm)/;

interface Triangles {
  corners: [number, number, number][];
  bindArea: number[];
  bindAspect: number[];
  ring: (string | null)[];
  handArea: boolean[];
}

/**
 * Bind-pose triangle inventory, classified by which handover it spans.
 *
 * Widening a handover necessarily recruits a few more triangles into the
 * "spans this ring" set, so before/after counts taken from each file's own
 * classification would compare different populations. RING_SET pins the set to
 * the baseline's, which is the only way the counts mean the same thing.
 */
function inventory(mesh: SkinnedMesh, fixedRing: Map<string, string> | null): Triangles {
  const position = mesh.geometry.getAttribute('position');
  const index = mesh.geometry.getIndex()!;
  const bones = vertexBones(mesh);
  const corners: [number, number, number][] = [];
  const bindArea: number[] = [];
  const bindAspect: number[] = [];
  const ring: (string | null)[] = [];
  const handArea: boolean[] = [];
  const a = new Vector3();
  const b = new Vector3();
  const c = new Vector3();

  for (let triangle = 0; triangle < index.count; triangle += 3) {
    const set: [number, number, number] = [
      index.getX(triangle),
      index.getX(triangle + 1),
      index.getX(triangle + 2),
    ];
    const carried = new Set(set.flatMap((vertex) => bones[vertex]));
    const inHand = set.every((vertex) => bones[vertex].some((name) => HAND_AREA.test(name)));

    let spans: string | null = null;
    for (const [proximal, distal, label] of RING_PAIRS) {
      if (carried.has(proximal) && carried.has(distal)) spans = spans ? `${spans}+${label}` : label;
    }

    if (fixedRing) {
      const key = set.join(',');
      if (!fixedRing.has(key)) continue;
      spans = fixedRing.get(key) || null;
    } else if (!inHand && !spans) continue;
    a.fromBufferAttribute(position, set[0]);
    b.fromBufferAttribute(position, set[1]);
    c.fromBufferAttribute(position, set[2]);
    corners.push(set);
    bindArea.push(triangleArea(a, b, c));
    bindAspect.push(aspect(a, b, c));
    ring.push(spans);
    handArea.push(inHand);
  }
  return { corners, bindArea, bindAspect, ring, handArea };
}

/** Posed triangle metrics against the bind inventory. */
function posedMetrics(mesh: SkinnedMesh, triangles: Triangles) {
  mesh.skeleton.update();
  const a = new Vector3();
  const b = new Vector3();
  const c = new Vector3();
  const retention: number[] = [];
  const aspects: number[] = [];
  const worst: { triangle: number; retention: number; aspect: number; ring: string | null }[] = [];

  for (let slot = 0; slot < triangles.corners.length; slot += 1) {
    const [x, y, z] = triangles.corners[slot];
    mesh.getVertexPosition(x, a);
    mesh.getVertexPosition(y, b);
    mesh.getVertexPosition(z, c);
    const area = triangleArea(a, b, c);
    const keep = triangles.bindArea[slot] > 1e-12 ? area / triangles.bindArea[slot] : 1;
    const shape = aspect(a, b, c);
    retention.push(keep);
    aspects.push(shape);
    worst.push({ triangle: slot, retention: keep, aspect: shape, ring: triangles.ring[slot] });
  }

  worst.sort((one, two) => one.retention - two.retention);
  return {
    minRetention: retention.length ? Math.min(...retention) : 1,
    p01Retention: percentile(retention, 0.01),
    p05Retention: percentile(retention, 0.05),
    below25: retention.filter((value) => value < 0.25).length,
    below40: retention.filter((value) => value < 0.4).length,
    maxAspect: aspects.length ? Math.max(...aspects) : 0,
    p99Aspect: percentile(aspects, 0.99),
    worst: worst.slice(0, 8).map((entry) => ({
      triangle: entry.triangle,
      corners: triangles.corners[entry.triangle],
      ring: entry.ring,
      retention: Number(entry.retention.toFixed(4)),
      aspect: Number(entry.aspect.toFixed(3)),
      bindAspect: Number(triangles.bindAspect[entry.triangle].toFixed(3)),
    })),
  };
}

/** Whole-mesh edge strain, the same measure the retained diagnostic prints. */
function edgeSet(mesh: SkinnedMesh) {
  const position = mesh.geometry.getAttribute('position');
  const index = mesh.geometry.getIndex()!;
  const edges: [number, number][] = [];
  const rest: number[] = [];
  const seen = new Set<number>();
  const one = new Vector3();
  const two = new Vector3();
  for (let triangle = 0; triangle < index.count; triangle += 3) {
    const set = [index.getX(triangle), index.getX(triangle + 1), index.getX(triangle + 2)];
    for (let slot = 0; slot < 3; slot += 1) {
      const lo = Math.min(set[slot], set[(slot + 1) % 3]);
      const hi = Math.max(set[slot], set[(slot + 1) % 3]);
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

function strain(mesh: SkinnedMesh, set: ReturnType<typeof edgeSet>) {
  mesh.skeleton.update();
  const one = new Vector3();
  const two = new Vector3();
  const ratios: number[] = [];
  set.edges.forEach(([a, b], slot) => {
    mesh.getVertexPosition(a, one);
    mesh.getVertexPosition(b, two);
    ratios.push(one.distanceTo(two) / set.rest[slot]);
  });
  return {
    max: Math.max(...ratios),
    p99: percentile(ratios, 0.99),
    p95: percentile(ratios, 0.95),
    min: Math.min(...ratios),
  };
}

const HANDLE_RADIUS = 0.015;
const HANDLE_HALF_LENGTH = 0.06;

function handleClearance(character: CharacterBuild, clip: ReturnType<typeof generateClip>) {
  const out: Record<string, { penetrating: number; minMm: number | null }> = {};
  if (!character.handMatrix) return out;
  const vertex = new Vector3();
  const local = new Vector3();

  for (const side of ['l', 'r'] as Side[]) {
    const instance = clip.equipment.find(
      (entry) =>
        entry.kind === 'dumbbell' && entry.attachment.mode === 'hand' && entry.attachment.side === side,
    );
    if (!instance || instance.attachment.mode !== 'hand') continue;
    const hand = character.handMatrix(side, new Matrix4());
    if (!hand) continue;
    const socket = equipmentSocket(instance.kind, instance.attachment.socket);
    const grip = instance.attachment.gripOffset ?? { x: 0, y: 0.045, z: 0 };
    const equipment = new Matrix4().multiplyMatrices(
      hand,
      handAttachmentMatrix(grip, socket?.position ?? { x: 0, y: 0, z: 0 }),
    );
    const toHandle = equipment.clone().invert();
    let penetrating = 0;
    let minimum = Number.POSITIVE_INFINITY;
    for (const mesh of character.meshes) {
      mesh.skeleton.update();
      mesh.updateWorldMatrix(true, false);
      const count = mesh.geometry.getAttribute('position').count;
      for (let index = 0; index < count; index += 1) {
        mesh.getVertexPosition(index, vertex);
        local.copy(vertex).applyMatrix4(mesh.matrixWorld).applyMatrix4(toHandle);
        if (Math.abs(local.z) > HANDLE_HALF_LENGTH) continue;
        const clearance = Math.hypot(local.x, local.y) - HANDLE_RADIUS;
        minimum = Math.min(minimum, clearance);
        if (clearance < 0) penetrating += 1;
      }
    }
    out[side] = {
      penetrating,
      minMm: Number.isFinite(minimum) ? Number((minimum * 1000).toFixed(3)) : null,
    };
  }
  return out;
}

const CURL_FRAMES: [string, number][] = [
  ['Bottom', 0],
  ['Mid lift', 1],
  ['Peak', 2],
  ['Mid lower', 4],
  ['Return', 5],
];

describe('hand/wrist ring measurement', () => {
  it('measures the repaired rings through the production path', async () => {
    const bytes = readFileSync(glbPath);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const source = retargetedCharacterSource({ id: 'measure', label: 'Measure', data });
    const character = await source.build(rig);
    const mesh = character.meshes[0];
    const ringSetPath = process.env.RING_SET;
    const fixedRing =
      ringSetPath && existsSync(ringSetPath)
        ? new Map<string, string>(JSON.parse(readFileSync(ringSetPath, 'utf8')))
        : null;
    const triangles = inventory(mesh, fixedRing);
    if (ringSetPath && !fixedRing) {
      const entries = triangles.corners.map(
        (corners, slot) => [corners.join(','), triangles.ring[slot] ?? ''] as [string, string],
      );
      writeFileSync(ringSetPath, JSON.stringify(entries));
      console.log(`wrote ring set: ${entries.length} triangles`);
    }
    const edges = edgeSet(mesh);

    const report: Record<string, unknown> = {
      glb: glbPath,
      vertices: mesh.geometry.getAttribute('position').count,
      inventoryTriangles: triangles.corners.length,
      ringTriangles: triangles.ring.filter(Boolean).length,
    };

    // Rest pose, so a repair that disturbed bind geometry shows up at once.
    mesh.skeleton.bones.forEach((bone) => bone.updateMatrixWorld(true));
    const restPositions: number[] = [];
    const point = new Vector3();
    for (let vertex = 0; vertex < mesh.geometry.getAttribute('position').count; vertex += 1) {
      point.fromBufferAttribute(mesh.geometry.getAttribute('position'), vertex);
      restPositions.push(point.x, point.y, point.z);
    }
    let checksum = 0;
    for (const value of restPositions) checksum = (checksum * 31 + Math.round(value * 1e6)) % 2147483647;
    report.bindChecksum = checksum;

    const exercises = [bicepCurl, shoulderPress, pushUp, pullUp];
    const perExercise: Record<string, unknown> = {};

    for (const definition of exercises) {
      const clip = generateClip(rig, definition);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const frames: [string, number][] =
        definition === bicepCurl
          ? CURL_FRAMES
          : [0, 0.2, 0.45, 0.7, 0.95].map((fraction) => [
              `${Math.round(fraction * 100)}%`,
              clip.duration * fraction,
            ]);

      const samples: unknown[] = [];
      const wholeRep = { p95: 0, p99: 0, max: 0 };
      const steps = 40;
      for (let step = 0; step <= steps; step += 1) {
        const frame = resolveFrame(rig, evaluation, clip, (clip.duration * step) / steps, { anchors });
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
        character.object.updateMatrixWorld(true);
        const measured = strain(mesh, edges);
        wholeRep.p95 = Math.max(wholeRep.p95, measured.p95);
        wholeRep.p99 = Math.max(wholeRep.p99, measured.p99);
        wholeRep.max = Math.max(wholeRep.max, measured.max);
      }

      for (const [label, time] of frames) {
        const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
        character.object.updateMatrixWorld(true);

        const ringOnly: Triangles = {
          corners: [],
          bindArea: [],
          bindAspect: [],
          ring: [],
          handArea: [],
        };
        triangles.ring.forEach((value, slot) => {
          if (!value) return;
          ringOnly.corners.push(triangles.corners[slot]);
          ringOnly.bindArea.push(triangles.bindArea[slot]);
          ringOnly.bindAspect.push(triangles.bindAspect[slot]);
          ringOnly.ring.push(value);
          ringOnly.handArea.push(triangles.handArea[slot]);
        });

        const sample: Record<string, unknown> = {
          label,
          time: Number(time.toFixed(3)),
          hand: posedMetrics(mesh, triangles),
          rings: posedMetrics(mesh, ringOnly),
        };

        if (definition === bicepCurl) {
          sample.handle = handleClearance(character, clip);
          const transforms = frame.equipment;
          const grips: Record<string, unknown> = {};
          for (const side of ['l', 'r'] as Side[]) {
            const instance = clip.equipment.find(
              (entry) =>
                entry.attachment.mode === 'hand' && entry.attachment.side === side,
            );
            const transform = instance ? transforms.get(instance.id) : undefined;
            if (!transform) continue;
            const fit = measureGripFit(evaluation, transform, side);
            grips[side] = {
              reachUse: Number(fit.reachUse.toFixed(4)),
              wrapCoverageDeg: Number(fit.wrapCoverageDeg.toFixed(2)),
              withinEnvelope: fit.withinEnvelope,
            };
          }
          sample.grip = grips;
        }

        samples.push(sample);
      }

      perExercise[definition.id] = { wholeRepStrain: wholeRep, samples };
    }

    report.exercises = perExercise;
    console.log('\nRING_MEASUREMENT\n' + JSON.stringify(report, null, 1));
    expect(triangles.corners.length).toBeGreaterThan(0);
    character.dispose();
  });
});
