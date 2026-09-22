import { readFileSync } from 'node:fs';
import { describe, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';
import { anatomicalGripOffset } from '../../src/equipment/attach';
import { equipmentSocketForInstance } from '../../src/equipment/library';
import { handAttachmentMatrix } from '../../src/export/clipBuilder';
import { GRIP_PROFILES } from '../../src/exercises/gripProfiles';
// @ts-expect-error - plain js helper
import { writePng } from './png.mjs';

/**
 * Rendered evidence for the corrected metric.
 *
 * Two images per profile, both in the handle's own frame so the bar is exactly
 * where the metric says it is:
 *
 *  - SOLID: a z-buffered lambert render of the hand and the bar, looking down
 *    the bar axis, with the metric's penetrating vertices overlaid in red and
 *    its contact vertices (0 to +2 mm) in amber, drawn without depth test so
 *    the set the number came from is visible even where it is buried.
 *  - SLICE: a cross-section. Every hand vertex within 4 mm of the bar's mid
 *    plane, plotted against the bar's true circle. A finger dot inside that
 *    circle is a finger inside the bar, which needs no interpretation.
 *
 * Drawn from the same posed vertices the metric grades, through the same
 * transform, so the picture cannot agree with a number the geometry does not.
 */
const rig = canonicalSkeleton;
const BAR_RADIUS = 0.015;
const BAR_HALF = 0.06;
const SIZE = 720;

type Group = 'proximal' | 'middle' | 'distal' | 'thumb' | 'palm';
const GROUPS: [Group, RegExp][] = [
  ['proximal', /^(f_index|f_middle|f_ring|f_pinky)\.?01/i],
  ['middle', /^(f_index|f_middle|f_ring|f_pinky)\.?02/i],
  ['distal', /^(f_index|f_middle|f_ring|f_pinky)\.?03/i],
  ['thumb', /^thumb\.?0[123]/i],
  ['palm', /^(palm\.?0[1-4]|hand)/i],
];
const COLOUR: Record<Group, [number, number, number]> = {
  proximal: [90, 160, 230],
  middle: [70, 200, 140],
  distal: [190, 150, 240],
  thumb: [240, 170, 70],
  palm: [170, 170, 170],
};

function cylinderDistance(p: Vector3): number {
  const dr = Math.hypot(p.x, p.y) - BAR_RADIUS;
  const dz = Math.abs(p.z) - BAR_HALF;
  if (dr <= 0 && dz <= 0) return Math.max(dr, dz);
  return Math.hypot(Math.max(dr, 0), Math.max(dz, 0));
}

class Canvas {
  rgb = new Uint8Array(SIZE * SIZE * 3);
  depth = new Float32Array(SIZE * SIZE).fill(Infinity);
  constructor(bg: [number, number, number]) {
    for (let i = 0; i < SIZE * SIZE; i += 1) {
      this.rgb[i * 3] = bg[0];
      this.rgb[i * 3 + 1] = bg[1];
      this.rgb[i * 3 + 2] = bg[2];
    }
  }
  pixel(x: number, y: number, c: [number, number, number]) {
    if (x < 0 || y < 0 || x >= SIZE || y >= SIZE) return;
    const i = (y * SIZE + x) * 3;
    this.rgb[i] = c[0];
    this.rgb[i + 1] = c[1];
    this.rgb[i + 2] = c[2];
  }
  disc(x: number, y: number, r: number, c: [number, number, number]) {
    for (let dy = -r; dy <= r; dy += 1)
      for (let dx = -r; dx <= r; dx += 1)
        if (dx * dx + dy * dy <= r * r) this.pixel(Math.round(x + dx), Math.round(y + dy), c);
  }
  ring(cx: number, cy: number, r: number, c: [number, number, number]) {
    for (let a = 0; a < 2600; a += 1) {
      const t = (a / 2600) * Math.PI * 2;
      this.pixel(Math.round(cx + Math.cos(t) * r), Math.round(cy + Math.sin(t) * r), c);
    }
  }
  /** Depth-tested flat-shaded triangle. */
  triangle(
    a: [number, number, number],
    b: [number, number, number],
    c: [number, number, number],
    base: [number, number, number],
  ) {
    const minX = Math.max(0, Math.floor(Math.min(a[0], b[0], c[0])));
    const maxX = Math.min(SIZE - 1, Math.ceil(Math.max(a[0], b[0], c[0])));
    const minY = Math.max(0, Math.floor(Math.min(a[1], b[1], c[1])));
    const maxY = Math.min(SIZE - 1, Math.ceil(Math.max(a[1], b[1], c[1])));
    const area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]);
    if (Math.abs(area) < 1e-9) return;
    // Facing, from the winding in screen space: the shade stands in for a
    // normal-dot-view, which is all this needs to read as a surface.
    const shade = 0.45 + 0.55 * Math.min(1, Math.abs(area) / 60);
    for (let y = minY; y <= maxY; y += 1) {
      for (let x = minX; x <= maxX; x += 1) {
        const w0 = ((b[0] - a[0]) * (y + 0.5 - a[1]) - (x + 0.5 - a[0]) * (b[1] - a[1])) / area;
        const w1 = ((x + 0.5 - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (y + 0.5 - a[1])) / area;
        if (w0 < 0 || w1 < 0 || w0 + w1 > 1) continue;
        const z = a[2] + w1 * (b[2] - a[2]) + w0 * (c[2] - a[2]);
        const i = y * SIZE + x;
        if (z >= this.depth[i]) continue;
        this.depth[i] = z;
        const j = i * 3;
        this.rgb[j] = Math.min(255, base[0] * shade);
        this.rgb[j + 1] = Math.min(255, base[1] * shade);
        this.rgb[j + 2] = Math.min(255, base[2] * shade);
      }
    }
  }
}

describe('grip render', () => {
  it('renders the fist against the bar with the metric’s own vertices marked', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({ id: 'view', label: 'View', data }).build(rig);
    const baseline = GRIP_PROFILES.dumbbell;
    const dir = process.env.OUT ?? 'scratchpad/repair/shots';
    const side = 'l' as const;

    const profiles: [string, [number, number, number], [number, number, number]][] = JSON.parse(
      process.env.PROFILES ??
        '[["shipped",[78,95,60],[-22,60,60]],["open",[45,55,35],[-14,40,40]]]',
    );

    for (const [label, fingers, thumb] of profiles) {
      GRIP_PROFILES.dumbbell = { ...baseline, fingers, thumb };
      const clip = generateClip(rig, bicepCurl);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const frame = resolveFrame(rig, evaluation, clip, 2, { anchors });
      // A solved per-digit table from gripsolver, applied to the resolved pose
      // exactly as the solver applied it, so the picture shows the solved grip
      // rather than the static profile.
      if (process.env.SOLVED) {
        const solved = JSON.parse(readFileSync(process.env.SOLVED, 'utf8'));
        const rotations = frame.pose.rotations as Record<string, { x: number; y: number; z: number }>;
        const sign = side === 'l' ? 1 : -1;
        const rad = (deg: number) => (deg * Math.PI) / 180;
        for (const finger of ['index', 'middle', 'ring', 'pinky'] as const)
          for (let seg = 0; seg < 3; seg += 1)
            rotations[`${finger}_0${seg + 1}_${side}`] = { x: 0, y: 0, z: sign * rad(solved.digits[finger][seg]) };
        for (let seg = 0; seg < 3; seg += 1)
          rotations[`thumb_0${seg + 1}_${side}`] = {
            x: seg === 0 ? rad(solved.opposition) : 0,
            y: 0,
            z: sign * rad(solved.thumbAngles[seg]),
          };
      }
      // PROD renders through the shipped grip context, so the picture is the
      // solved grip as applyCharacterPose actually delivers it.
      applyCharacterPose(character, rig, frame.pose, evaluation, {
        contacts: frame.contacts,
        ...(process.env.SHIPPED
          ? { grip: { kind: bicepCurl.hands.grip, closure: bicepCurl.hands.closure } }
          : {}),
      });

      const hand = character.handMatrix?.(side, new Matrix4());
      const instance = clip.equipment.find(
        (entry) => entry.attachment.mode === 'hand' && entry.attachment.side === side,
      );
      if (!hand || !instance || instance.attachment.mode !== 'hand') continue;
      const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
      const baseOffset =
        instance.attachment.gripOffset ?? character.gripOffset?.(side) ?? anatomicalGripOffset(side);
      const shift = JSON.parse(process.env.OFFSET ?? '[0,0,0]') as [number, number, number];
      const offset = {
        x: baseOffset.x + (side === 'l' ? shift[0] : -shift[0]) / 1000,
        y: baseOffset.y + shift[1] / 1000,
        z: baseOffset.z + shift[2] / 1000,
      };
      const handle = new Matrix4().multiplyMatrices(
        hand,
        handAttachmentMatrix(offset, socket?.position ?? { x: 0, y: 0, z: 0 }),
      );
      const toHandle = handle.clone().invert();

      // Everything in the handle's frame, in millimetres.
      const points: { p: Vector3; group: Group; d: number }[] = [];
      const tris: [number, number, number][] = [];
      const verts: Vector3[] = [];
      const scratch = new Vector3();
      for (const mesh of character.meshes) {
        mesh.skeleton.update();
        mesh.updateWorldMatrix(true, false);
        const joints = mesh.geometry.getAttribute('skinIndex');
        const weights = mesh.geometry.getAttribute('skinWeight');
        const count = mesh.geometry.getAttribute('position').count;
        const base = verts.length;
        const keep = new Int32Array(count).fill(-1);
        for (let index = 0; index < count; index += 1) {
          const totals = { proximal: 0, middle: 0, distal: 0, thumb: 0, palm: 0 } as Record<Group, number>;
          let held = 0;
          for (let lane = 0; lane < 4; lane += 1) {
            const w = weights.getComponent(index, lane);
            if (w <= 0) continue;
            const raw = mesh.skeleton.bones[joints.getComponent(index, lane)]?.name ?? '';
            if (!raw.toLowerCase().endsWith(side)) continue;
            const group = GROUPS.find(([, pattern]) => pattern.test(raw.replace(/^DEF-/, '')));
            if (!group) continue;
            totals[group[0]] += w;
            held += w;
          }
          if (held < 0.5) continue;
          let group: Group = 'palm';
          let best = -1;
          for (const [name] of GROUPS)
            if (totals[name] > best) {
              best = totals[name];
              group = name;
            }
          mesh.getVertexPosition(index, scratch);
          const local = scratch.clone().applyMatrix4(mesh.matrixWorld).applyMatrix4(toHandle);
          keep[index] = verts.length;
          verts.push(local);
          points.push({ p: local, group, d: cylinderDistance(local) });
        }
        const indexAttribute = mesh.geometry.index;
        if (indexAttribute) {
          for (let t = 0; t < indexAttribute.count; t += 3) {
            const a = keep[indexAttribute.getX(t)];
            const b = keep[indexAttribute.getX(t + 1)];
            const c = keep[indexAttribute.getX(t + 2)];
            if (a >= 0 && b >= 0 && c >= 0) tris.push([a, b, c]);
          }
        }
        void base;
      }

      // --- SOLID, looking down the bar axis (+z) -------------------------
      const mm = (v: number) => v * 1000;
      const solid = new Canvas([18, 20, 24]);
      const span = 110; // mm across the frame
      const px = (x: number, y: number): [number, number] => [
        SIZE / 2 + (mm(x) / span) * SIZE,
        SIZE / 2 - (mm(y) / span) * SIZE,
      ];
      // Looking down the bar axis at the BACK half of the hand only. Drawing
      // the bar's near end cap, as an earlier pass did, just occludes the wrap
      // that the view exists to show; the bar is the white outline instead.
      for (const [a, b, c] of tris) {
        const va = verts[a];
        const vb = verts[b];
        const vc = verts[c];
        if ((va.z + vb.z + vc.z) / 3 > 0) continue;
        const pa = px(va.x, va.y);
        const pb = px(vb.x, vb.y);
        const pc = px(vc.x, vc.y);
        solid.triangle([pa[0], pa[1], -va.z], [pb[0], pb[1], -vb.z], [pc[0], pc[1], -vc.z], [206, 168, 140]);
      }
      let inside = 0;
      let contact = 0;
      for (const { p, d } of points) {
        const [x, y] = px(p.x, p.y);
        if (d < 0) {
          solid.disc(x, y, 3, [255, 40, 40]);
          inside += 1;
        } else if (d < 0.002) {
          solid.disc(x, y, 2, [255, 190, 40]);
          contact += 1;
        }
      }
      solid.ring(SIZE / 2, SIZE / 2, (mm(BAR_RADIUS) / span) * SIZE, [255, 255, 255]);
      writePng(`${dir}/GRIP_${label}_solid.png`, SIZE, SIZE, solid.rgb);

      // --- SLICE through the bar's mid plane -----------------------------
      const slice = new Canvas([14, 15, 18]);
      const sliceSpan = 90;
      const spx = (x: number, y: number): [number, number] => [
        SIZE / 2 + (mm(x) / sliceSpan) * SIZE,
        SIZE / 2 - (mm(y) / sliceSpan) * SIZE,
      ];
      for (const { p, group, d } of points) {
        if (Math.abs(p.z) > 0.004) continue;
        const [x, y] = spx(p.x, p.y);
        slice.disc(x, y, d < 0 ? 4 : 3, d < 0 ? [255, 40, 40] : COLOUR[group]);
      }
      slice.ring(SIZE / 2, SIZE / 2, (mm(BAR_RADIUS) / sliceSpan) * SIZE, [255, 255, 255]);
      slice.ring(SIZE / 2, SIZE / 2, (mm(BAR_RADIUS) / sliceSpan) * SIZE + 1, [255, 255, 255]);
      writePng(`${dir}/GRIP_${label}_slice.png`, SIZE, SIZE, slice.rgb);

      // --- THREE-QUARTER, the arbiter view ------------------------------
      // Down the barrel cannot show a fingertip closing under the handle: it
      // is at the far end and gets clipped or occluded. This looks across the
      // bar instead, with the bar as a real cylinder and true lambert shading
      // from the triangle normals, so the shape reads as a hand.
      const q = new Canvas([16, 17, 21]);
      const f = new Vector3(0.62, 0.38, 0.69).normalize();
      const rt = new Vector3().crossVectors(new Vector3(0, 0, 1), f).normalize();
      const up = new Vector3().crossVectors(f, rt).normalize();
      const light = new Vector3(0.4, 0.75, 0.53).normalize();
      const qSpan = 150;
      const centre = new Vector3();
      for (const v of verts) centre.add(v);
      centre.multiplyScalar(1 / Math.max(1, verts.length));
      const qpx = (v: Vector3): [number, number, number] => {
        const d = scratch.copy(v).sub(centre);
        return [
          SIZE / 2 + (mm(d.dot(rt)) / qSpan) * SIZE,
          SIZE / 2 - (mm(d.dot(up)) / qSpan) * SIZE,
          -d.dot(f),
        ];
      };
      const shadeOf = (a: Vector3, b: Vector3, c: Vector3, base: [number, number, number]) => {
        const n = new Vector3()
          .crossVectors(new Vector3().subVectors(b, a), new Vector3().subVectors(c, a))
          .normalize();
        const lambert = 0.28 + 0.72 * Math.abs(n.dot(light));
        return [base[0] * lambert, base[1] * lambert, base[2] * lambert] as [number, number, number];
      };
      // The bar, as a real cylinder.
      const SEG = 48;
      for (let i = 0; i < SEG; i += 1) {
        const t0 = (i / SEG) * Math.PI * 2;
        const t1 = ((i + 1) / SEG) * Math.PI * 2;
        const ring = (t: number, z: number) =>
          new Vector3(Math.cos(t) * BAR_RADIUS, Math.sin(t) * BAR_RADIUS, z);
        const a = ring(t0, -BAR_HALF);
        const b = ring(t1, -BAR_HALF);
        const c = ring(t0, BAR_HALF);
        const d = ring(t1, BAR_HALF);
        for (const [p0, p1, p2] of [[a, b, c] as const, [b, d, c] as const]) {
          q.triangle(qpx(p0), qpx(p1), qpx(p2), shadeOf(p0, p1, p2, [118, 140, 176]));
        }
      }
      for (const [a, b, c] of tris) {
        const va = verts[a];
        const vb = verts[b];
        const vc = verts[c];
        q.triangle(qpx(va), qpx(vb), qpx(vc), shadeOf(va, vb, vc, [214, 172, 141]));
      }
      writePng(`${dir}/GRIP_${label}_3q.png`, SIZE, SIZE, q.rgb);

      console.log(
        `RENDER ${label}: ${points.length} hand vertices, ${tris.length} triangles, ` +
          `${inside} inside (red), ${contact} in contact band (amber)`,
      );
    }
    GRIP_PROFILES.dumbbell = baseline;
  }, 240000);
});
