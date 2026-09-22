import { readFileSync } from 'node:fs';
import { describe, it } from 'vitest';
import { Vector3 } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { pushUp } from '../../src/exercises/definitions/pushUp';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';
import type { BoneName } from '../../src/rig/boneNames';
// @ts-expect-error - plain js helper
import { writePng } from './png.mjs';

/**
 * Phase 4 silhouette evidence.
 *
 * The previous attempt filtered vertices by skin weight and drew only triangles
 * whose three corners survived, which tore the mesh into shards and made the
 * surface impossible to judge. This filters NOTHING: every triangle of every
 * mesh is rasterised and the camera is simply zoomed onto the forearm. What the
 * image shows is therefore the actual skinned surface.
 */
const rig = canonicalSkeleton;
const SIZE = 820;

class Canvas {
  rgb = new Uint8Array(SIZE * SIZE * 3);
  depth = new Float32Array(SIZE * SIZE).fill(Infinity);
  constructor(bg: [number, number, number]) {
    for (let i = 0; i < SIZE * SIZE; i += 1) {
      this.rgb[i * 3] = bg[0]; this.rgb[i * 3 + 1] = bg[1]; this.rgb[i * 3 + 2] = bg[2];
    }
  }
  triangle(a: number[], b: number[], c: number[], base: [number, number, number]) {
    const minX = Math.max(0, Math.floor(Math.min(a[0], b[0], c[0])));
    const maxX = Math.min(SIZE - 1, Math.ceil(Math.max(a[0], b[0], c[0])));
    const minY = Math.max(0, Math.floor(Math.min(a[1], b[1], c[1])));
    const maxY = Math.min(SIZE - 1, Math.ceil(Math.max(a[1], b[1], c[1])));
    const area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]);
    if (Math.abs(area) < 1e-9) return;
    for (let y = minY; y <= maxY; y += 1) for (let x = minX; x <= maxX; x += 1) {
      const w0 = ((b[0] - a[0]) * (y + 0.5 - a[1]) - (x + 0.5 - a[0]) * (b[1] - a[1])) / area;
      const w1 = ((x + 0.5 - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (y + 0.5 - a[1])) / area;
      if (w0 < 0 || w1 < 0 || w0 + w1 > 1) continue;
      const z = a[2] + w1 * (b[2] - a[2]) + w0 * (c[2] - a[2]);
      const i = y * SIZE + x;
      if (z >= this.depth[i]) continue;
      this.depth[i] = z;
      this.rgb[i * 3] = base[0]; this.rgb[i * 3 + 1] = base[1]; this.rgb[i * 3 + 2] = base[2];
    }
  }
  disc(x: number, y: number, r: number, c: [number, number, number]) {
    for (let dy = -r; dy <= r; dy += 1) for (let dx = -r; dx <= r; dx += 1) {
      if (dx * dx + dy * dy > r * r) continue;
      const px = Math.round(x + dx), py = Math.round(y + dy);
      if (px < 0 || py < 0 || px >= SIZE || py >= SIZE) continue;
      const i = (py * SIZE + px) * 3;
      this.rgb[i] = c[0]; this.rgb[i + 1] = c[1]; this.rgb[i + 2] = c[2];
    }
  }
  line(a: number[], b: number[], c: [number, number, number]) {
    const steps = Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]));
    for (let s = 0; s <= steps; s += 1) {
      const t = steps ? s / steps : 0;
      this.disc(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, 1, c);
    }
  }
}

describe('phase 4 silhouette', () => {
  it('renders the push-up forearm chain with nothing filtered out', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({ id: 'p4v', label: 'P4V', data }).build(rig);
    const clip = generateClip(rig, pushUp);
    const evaluation = new PoseEvaluation(rig);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
    const peak = clip.keyframes.find((k) => k.marker === 'peak')?.time ?? clip.duration / 2;
    const tag = process.env.TAG ?? 'base';

    for (const [label, time] of [['Top', 0], ['Bottom', peak]] as [string, number][]) {
      const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
      evaluation.apply(frame.pose);
      applyCharacterPose(character, rig, frame.pose, evaluation, {
        contacts: frame.contacts,
        grip: { kind: pushUp.hands.grip, closure: pushUp.hands.closure },
      });

      const boneAt = (name: string) => {
        const bone = character.boneByName.get(name as BoneName);
        if (!bone) return null;
        bone.updateWorldMatrix(true, false);
        return new Vector3().setFromMatrixPosition(bone.matrixWorld);
      };
      const shoulder = boneAt('upperarm_l')!;
      const elbow = boneAt('forearm_l')!;
      const wrist = boneAt('hand_l')!;
      const knuckle = boneAt('middle_01_l') ?? wrist;

      // Every triangle of every mesh, posed into world space. No filtering.
      const verts: Vector3[] = [];
      const tris: [number, number, number][] = [];
      const scratch = new Vector3();
      for (const mesh of character.meshes) {
        mesh.skeleton.update();
        mesh.updateWorldMatrix(true, false);
        const base = verts.length;
        const count = mesh.geometry.getAttribute('position').count;
        for (let v = 0; v < count; v += 1) {
          mesh.getVertexPosition(v, scratch);
          verts.push(scratch.clone().applyMatrix4(mesh.matrixWorld));
        }
        const idx = mesh.geometry.index;
        if (idx) for (let t = 0; t < idx.count; t += 3)
          tris.push([base + idx.getX(t), base + idx.getX(t + 1), base + idx.getX(t + 2)]);
      }

      const axis = new Vector3().subVectors(wrist, elbow).normalize();
      const reference = Math.abs(axis.y) > 0.9 ? new Vector3(0, 0, 1) : new Vector3(0, 1, 0);
      const sideDir = new Vector3().crossVectors(axis, reference).normalize();
      const centre = elbow.clone().add(knuckle).multiplyScalar(0.5);
      const span = elbow.distanceTo(knuckle) * 2.3;
      const light = new Vector3(0.3, 0.7, 0.65).normalize();

      const views: [string, Vector3][] = [
        ['side', sideDir.clone()],
        ['threequarter', sideDir.clone().multiplyScalar(0.72)
          .add(new Vector3().crossVectors(sideDir, axis).normalize().multiplyScalar(0.7)).normalize()],
      ];
      for (const [view, forward] of views) {
        for (const overlay of view === 'side' ? [false, true] : [false]) {
          const up = axis.clone();
          const right = new Vector3().crossVectors(up, forward).normalize();
          const trueUp = new Vector3().crossVectors(forward, right).normalize();
          const project = (v: Vector3) => {
            const d = v.clone().sub(centre);
            return [
              SIZE / 2 + (d.dot(right) / span) * SIZE,
              SIZE / 2 - (d.dot(trueUp) / span) * SIZE,
              -d.dot(forward),
            ];
          };
          const canvas = new Canvas([15, 16, 20]);
          for (const [a, b, c] of tris) {
            const va = verts[a], vb = verts[b], vc = verts[c];
            const n = new Vector3().crossVectors(
              new Vector3().subVectors(vb, va), new Vector3().subVectors(vc, va),
            ).normalize();
            const lam = 0.26 + 0.74 * Math.abs(n.dot(light));
            canvas.triangle(project(va), project(vb), project(vc),
              [Math.min(255, 216 * lam), Math.min(255, 174 * lam), Math.min(255, 143 * lam)]);
          }
          // Floor line, so palm/floor contact is visible rather than inferred.
          const onFloor = (p: Vector3) => { const q = p.clone(); q.y = 0; return q; };
          canvas.line(project(onFloor(centre.clone().add(right.clone().multiplyScalar(-span)))),
                      project(onFloor(centre.clone().add(right.clone().multiplyScalar(span)))), [70, 90, 120]);
          if (overlay) {
            const chain: [string, Vector3 | null][] = [
              ['shoulder', shoulder], ['elbow', elbow], ['wrist', wrist], ['knuckle', knuckle],
            ];
            for (let i = 0; i < chain.length - 1; i += 1) {
              const one = chain[i][1], two = chain[i + 1][1];
              if (one && two) canvas.line(project(one), project(two), [90, 200, 255]);
            }
            for (const [, p] of chain) if (p) {
              const [x, y] = project(p);
              canvas.disc(x, y, 6, [255, 80, 60]);
            }
          }
          const name = `P4_${tag}_${label}_${view}${overlay ? '_skeleton' : ''}`;
          writePng(`scratchpad/repair/shots/${name}.png`, SIZE, SIZE, canvas.rgb);
        }
      }
      console.log(`P4VIEW ${tag} ${label}: ${verts.length} vertices, ${tris.length} triangles, span ${(span * 1000).toFixed(0)} mm`);
    }
  }, 600000);
});
