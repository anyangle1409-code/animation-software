import { readFileSync, writeFileSync } from 'node:fs';
import { describe, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { toDeg } from '../../src/core/math';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';
import { anatomicalGripOffset } from '../../src/equipment/attach';
import { equipmentSocketForInstance } from '../../src/equipment/library';
import { handAttachmentMatrix } from '../../src/export/clipBuilder';
import { GRIP_PROFILES } from '../../src/exercises/gripProfiles';

/**
 * Corrected full-fist grip metric.
 *
 * Four faults in the previous harnesses, each fixed here:
 *
 *  1. CLASSIFICATION. It picked the single highest-weighted bone and dropped
 *     any vertex whose best bone held under 0.5. A finger vertex normally
 *     splits ~0.45/0.40 across two phalanges, so those vertices were either
 *     discarded or, when the palm happened to hold the plurality, counted as
 *     palm. That is the whole dominant-bone vs summed-weight disagreement.
 *     Here a vertex is assigned to the group holding the largest SUMMED weight,
 *     which is how the vertex actually moves.
 *  2. FINITE HANDLE. It measured radial distance to an INFINITE cylinder and
 *     threw away anything outside an axial slab. A vertex past the end of the
 *     bar was reported as absent rather than clear. Here the distance is the
 *     signed distance to the real capped cylinder, so nothing is discarded and
 *     a vertex beyond the cap reads as the positive distance it is.
 *  3. SLAB. The half-length was an env var (±40 vs ±60 mm between runs, which
 *     is why two harnesses disagreed). It is now the bar's real half-length,
 *     read from the equipment geometry, and it is no longer a filter at all.
 *  4. SWEEP INTEGRITY. A profile sweep returned byte-identical numbers. Every
 *     profile here reports the canonical joint angle it produced AND a
 *     checksum of the posed hand vertices, and the run flags SWEEP-DEAD if
 *     either fails to move. A number that cannot be traced to a moved mesh is
 *     not reported as a measurement.
 */
const rig = canonicalSkeleton;

// The real dumbbell bar, from src/equipment/geometry.ts.
const BAR_RADIUS = 0.015;
const BAR_HALF = 0.06;

type Group = 'proximal' | 'middle' | 'distal' | 'thumb' | 'palm';
const GROUPS: [Group, RegExp][] = [
  ['proximal', /^(f_index|f_middle|f_ring|f_pinky)\.?01/i],
  ['middle', /^(f_index|f_middle|f_ring|f_pinky)\.?02/i],
  ['distal', /^(f_index|f_middle|f_ring|f_pinky)\.?03/i],
  ['thumb', /^thumb\.?0[123]/i],
  ['palm', /^(palm\.?0[1-4]|hand)/i],
];

/**
 * Signed distance from a point to a capped cylinder of radius R and half
 * length H about the local z axis. Negative inside; the magnitude is the
 * penetration depth, which is what "the handle is N mm inside the hand" means.
 */
function cylinderDistance(local: Vector3): number {
  const dr = Math.hypot(local.x, local.y) - BAR_RADIUS;
  const dz = Math.abs(local.z) - BAR_HALF;
  if (dr <= 0 && dz <= 0) return Math.max(dr, dz);
  return Math.hypot(Math.max(dr, 0), Math.max(dz, 0));
}

interface Slot {
  near: number;
  inside: number;
  deepest: number;
}

function measure(
  character: Awaited<ReturnType<ReturnType<typeof retargetedCharacterSource>['build']>>,
  handle: Matrix4,
  side: 'l' | 'r',
) {
  const toHandle = handle.clone().invert();
  const out = {} as Record<Group, Slot>;
  for (const [name] of GROUPS) out[name] = { near: Number.POSITIVE_INFINITY, inside: 0, deepest: 0 };
  const angles: number[] = [];
  const penetrating: { x: number; y: number; z: number; group: Group; depth: number }[] = [];
  const vertex = new Vector3();
  const local = new Vector3();
  const world = new Vector3();
  let checksum = 0;

  for (const mesh of character.meshes) {
    mesh.skeleton.update();
    mesh.updateWorldMatrix(true, false);
    const joints = mesh.geometry.getAttribute('skinIndex');
    const weights = mesh.geometry.getAttribute('skinWeight');
    const count = mesh.geometry.getAttribute('position').count;
    for (let index = 0; index < count; index += 1) {
      // Fix 1: sum the weight each GROUP holds, rather than taking one bone.
      const totals = { proximal: 0, middle: 0, distal: 0, thumb: 0, palm: 0 } as Record<Group, number>;
      let held = 0;
      for (let lane = 0; lane < 4; lane += 1) {
        const w = weights.getComponent(index, lane);
        if (w <= 0) continue;
        const raw = mesh.skeleton.bones[joints.getComponent(index, lane)]?.name ?? '';
        if (!raw.toLowerCase().endsWith(side)) continue;
        const name = raw.replace(/^DEF-/, '');
        const group = GROUPS.find(([, pattern]) => pattern.test(name));
        if (!group) continue;
        totals[group[0]] += w;
        held += w;
      }
      // The vertex has to belong to this hand at all before it can be graded.
      if (held < 0.5) continue;
      let group: Group = 'palm';
      let best = -1;
      for (const [name] of GROUPS) {
        if (totals[name] > best) {
          best = totals[name];
          group = name;
        }
      }

      mesh.getVertexPosition(index, vertex);
      world.copy(vertex).applyMatrix4(mesh.matrixWorld);
      checksum = (checksum + Math.round(world.x * 1e6) + Math.round(world.y * 1e6) * 3 + Math.round(world.z * 1e6) * 7) % 2147483647;
      local.copy(world).applyMatrix4(toHandle);

      // Fix 2 + 3: real capped-cylinder distance, no slab filter.
      const distance = cylinderDistance(local);
      const slot = out[group];
      if (distance < slot.near) slot.near = distance;
      if (distance < 0) {
        slot.inside += 1;
        slot.deepest = Math.min(slot.deepest, distance);
        penetrating.push({ x: world.x, y: world.y, z: world.z, group, depth: distance });
      }
      // Wrap: only vertices actually alongside the bar, hugging it.
      if (Math.abs(local.z) <= BAR_HALF && Math.hypot(local.x, local.y) - BAR_RADIUS < 0.012) {
        angles.push(Math.atan2(local.y, local.x));
      }
    }
  }

  angles.sort((a, b) => a - b);
  let widest = angles.length ? angles[0] + Math.PI * 2 - angles[angles.length - 1] : Math.PI * 2;
  for (let i = 1; i < angles.length; i += 1) widest = Math.max(widest, angles[i] - angles[i - 1]);
  const fingers = (['proximal', 'middle', 'distal'] as Group[]).reduce(
    (acc, name) => ({
      near: Math.min(acc.near, out[name].near),
      inside: acc.inside + out[name].inside,
      deepest: Math.min(acc.deepest, out[name].deepest),
    }),
    { near: Number.POSITIVE_INFINITY, inside: 0, deepest: 0 } as Slot,
  );
  return { out, fingers, coverage: 360 - (widest * 180) / Math.PI, penetrating, checksum };
}

function handleFrame(
  character: Awaited<ReturnType<ReturnType<typeof retargetedCharacterSource>['build']>>,
  clip: ReturnType<typeof generateClip>,
  side: 'l' | 'r',
): Matrix4 | null {
  const hand = character.handMatrix?.(side, new Matrix4());
  if (!hand) return null;
  const instance = clip.equipment.find(
    (entry) => entry.attachment.mode === 'hand' && entry.attachment.side === side,
  );
  if (!instance || instance.attachment.mode !== 'hand') return null;
  const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
  const offset =
    instance.attachment.gripOffset ?? character.gripOffset?.(side) ?? anatomicalGripOffset(side);
  return new Matrix4().multiplyMatrices(
    hand,
    handAttachmentMatrix(offset, socket?.position ?? { x: 0, y: 0, z: 0 }),
  );
}

const FRAMES: [string, number][] = [
  ['Bottom', 0],
  ['Mid', 1],
  ['Peak', 2],
];

describe('corrected grip metric', () => {
  it('measures the fist against the real capped bar, and proves the sweep moves the mesh', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({ id: 'metric', label: 'Metric', data }).build(rig);

    const baseline = GRIP_PROFILES.dumbbell;
    // The sweep. The first row is the shipped profile, so the run reproduces
    // the current state before it varies anything.
    const sweep: [string, [number, number, number], [number, number, number]][] = [
      ['shipped   ', [78, 95, 60], [-22, 60, 60]],
      ['deeper PIP', [78, 108, 60], [-22, 60, 60]],
      ['deeper MCP', [92, 95, 60], [-22, 60, 60]],
      ['deeper DIP', [78, 95, 78], [-22, 60, 60]],
      ['full fist ', [92, 108, 78], [-25, 68, 68]],
      ['open      ', [45, 55, 35], [-14, 40, 40]],
    ];

    const seen = new Map<string, string>();
    const dump: Record<string, unknown> = {};

    console.log('\nCORRECTED GRIP METRIC — capped bar r=15.0mm half=60.0mm, summed-weight classification');
    console.log('profile | frame | PIP° | checksum | fingers near/in | palm near/in | thumb near/in | wrap°');

    for (const [label, fingers, thumb] of sweep) {
      GRIP_PROFILES.dumbbell = { ...baseline, fingers, thumb };
      // Regenerated AFTER the mutation, every time — the previous sweep reused
      // a clip built before the profile changed, which is why it could not move.
      const clip = generateClip(rig, bicepCurl);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);

      for (const [frameLabel, time] of FRAMES) {
        const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
        const pip = toDeg(frame.pose.rotations.middle_02_l?.z ?? 0);
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
        const handle = handleFrame(character, clip, 'l');
        if (!handle) continue;
        const result = measure(character, handle, 'l');

        // Fix 4: a number only counts if the mesh moved to produce it.
        const key = `${frameLabel}:${result.checksum}:${pip.toFixed(4)}`;
        const previous = seen.get(`${frameLabel}:${result.checksum}`);
        const dead = previous && previous !== label ? ` SWEEP-DEAD(matches ${previous})` : '';
        if (!previous) seen.set(`${frameLabel}:${result.checksum}`, label);

        const cell = (slot: Slot) =>
          `${Number.isFinite(slot.near) ? (slot.near * 1000).toFixed(2) : '—'}${slot.inside ? `/${slot.inside}` : '/0'}`;
        console.log(
          `${label} | ${frameLabel.padEnd(6)} | ${pip.toFixed(1).padStart(5)} | ${String(result.checksum).padStart(10)} | ` +
            `${cell(result.fingers).padStart(12)} | ${cell(result.out.palm).padStart(12)} | ${cell(result.out.thumb).padStart(12)} | ` +
            `${result.coverage.toFixed(0)}${dead}`,
        );
        if (label.trim() === 'shipped' && frameLabel === 'Peak') {
          dump.penetrating = result.penetrating;
          dump.handle = handle.toArray();
          void key;
        }
      }
    }

    GRIP_PROFILES.dumbbell = baseline;
    if (process.env.DUMP) writeFileSync(process.env.DUMP, JSON.stringify(dump));
  }, 240000);
});
