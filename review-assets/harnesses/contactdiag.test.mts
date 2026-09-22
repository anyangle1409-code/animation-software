import { readFileSync, writeFileSync } from 'node:fs';
import { describe, it } from 'vitest';
import { Matrix4, Quaternion, Vector3 } from 'three';
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

/**
 * Root-cause diagnostic for the curl Bottom/Return dumbbell penetration.
 * Instrumentation only: nothing here changes an asset, a pose or a rule.
 */
const rig = canonicalSkeleton;
const HANDLE_RADIUS = 0.015, HANDLE_HALF = 0.06;
const PLATE_RADIUS = 0.048, PLATE_HALF = 0.0175, PLATE_CENTRE = 0.075;
const ARM = /^(shoulder|upper_?arm|forearm|hand|palm|f_|thumb|clavicle)/i;

/** Which anatomical region a vertex belongs to, by dominant deform bone. */
function regionOf(name: string): string {
  const bare = name.replace(/^DEF-/, '');
  if (/^thigh/i.test(bare)) return /\.001|001/.test(bare) ? 'mid/lower thigh' : 'upper thigh';
  if (/^pelvis/i.test(bare)) return 'hip / pelvis';
  if (/^spine(\.|$|00)/i.test(bare)) return 'lower torso / abdomen';
  if (/^shin/i.test(bare)) return 'shin';
  return bare;
}
/** Distance to the dumbbell envelope, and which part owns it. */
const distanceToDumbbell = (p: Vector3): { d: number; part: string } => {
  const radial = Math.hypot(p.x, p.y), z = Math.abs(p.z);
  const handle = Math.max(radial - HANDLE_RADIUS, z - HANDLE_HALF);
  const plate = Math.max(radial - PLATE_RADIUS, PLATE_CENTRE - PLATE_HALF - z, z - PLATE_CENTRE - PLATE_HALF);
  return handle <= plate
    ? { d: handle, part: 'handle' }
    : { d: plate, part: p.z < 0 ? 'plate(-z)' : 'plate(+z)' };
};

describe('curl bottom contact diagnostic', () => {
  it('locates and attributes the penetration', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({ id: 'diag', label: 'Diag', data }).build(rig);

    const rows: string[] = [];
    const reference: Record<string, { grip: Vector3; plate: Vector3; axis: Vector3; shoulder: Vector3; elbow: Vector3; hand: Vector3 }> = {};

    for (const [label, time] of [['Bottom', 0], ['Return', 5]] as [string, number][]) {
      for (const value of label === 'Bottom' ? [3, 5, 6, 7, 8, 9, 11] : [3]) {
        const tuned = {
          ...bicepCurl,
          startPose: {
            ...bicepCurl.startPose,
            joints: {
              ...bicepCurl.startPose.joints,
              upperarm_l: { ...bicepCurl.startPose.joints.upperarm_l, z: -value },
              upperarm_r: { ...bicepCurl.startPose.joints.upperarm_r, z: value },
            },
          },
        };
        const clip = generateClip(rig, tuned);
        const evaluation = new PoseEvaluation(rig);
        const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
        const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });

        for (const side of ['l', 'r'] as const) {
          const instance = clip.equipment.find(
            (e) => e.kind === 'dumbbell' && e.attachment.mode === 'hand' && e.attachment.side === side,
          );
          if (!instance || instance.attachment.mode !== 'hand') continue;
          const handFrame = character.handMatrix?.(side, new Matrix4());
          if (!handFrame) continue;
          const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
          const offset = instance.attachment.gripOffset ?? character.gripOffset?.(side) ?? anatomicalGripOffset(side);
          const dumbbell = new Matrix4().multiplyMatrices(
            handFrame,
            handAttachmentMatrix(offset, socket?.position ?? { x: 0, y: 0, z: 0 }),
          );
          const toDumbbell = dumbbell.clone().invert();

          const bone = (n: string) => {
            const b = character.boneByName.get(n as never);
            return b ? new Vector3().setFromMatrixPosition(b.matrixWorld) : new Vector3();
          };
          const shoulder = bone(side === 'l' ? 'upperarm_l' : 'upperarm_r');
          const elbow = bone(side === 'l' ? 'forearm_l' : 'forearm_r');
          const wrist = bone(side === 'l' ? 'hand_l' : 'hand_r');
          const frameOrigin = new Vector3().setFromMatrixPosition(handFrame);
          const gripCentre = new Vector3().setFromMatrixPosition(dumbbell);
          const axis = new Vector3(0, 0, 1).transformDirection(dumbbell).normalize();
          // Inboard plate: the one on the side of the body midline.
          const inboardSign = gripCentre.x > 0 ? (axis.x > 0 ? -1 : 1) : (axis.x > 0 ? 1 : -1);
          const plateCentre = gripCentre.clone().addScaledVector(axis, inboardSign * PLATE_CENTRE);

          let best = Number.POSITIVE_INFINITY;
          let bestPoint = new Vector3();
          let bestRegion = '—';
          let bestPart = '—';
          let gripToBody = Number.POSITIVE_INFINITY;
          const vertex = new Vector3(), local = new Vector3();
          for (const mesh of character.meshes) {
            mesh.skeleton.update();
            mesh.updateWorldMatrix(true, false);
            const joints = mesh.geometry.getAttribute('skinIndex');
            const weights = mesh.geometry.getAttribute('skinWeight');
            for (let index = 0; index < mesh.geometry.getAttribute('position').count; index += 1) {
              let arm = 0, top = 0, topName = '';
              for (let lane = 0; lane < 4; lane += 1) {
                const weight = weights.getComponent(index, lane);
                if (weight <= 0) continue;
                const name = mesh.skeleton.bones[joints.getComponent(index, lane)]?.name ?? '';
                if (ARM.test(name.replace(/^DEF-/, ''))) arm += weight;
                if (weight > top) { top = weight; topName = name; }
              }
              if (arm > 0.05) continue;
              mesh.getVertexPosition(index, vertex);
              vertex.applyMatrix4(mesh.matrixWorld);
              gripToBody = Math.min(gripToBody, vertex.distanceTo(gripCentre));
              local.copy(vertex).applyMatrix4(toDumbbell);
              const hit = distanceToDumbbell(local);
              if (hit.d < best) { best = hit.d; bestPoint = vertex.clone(); bestRegion = regionOf(topName); bestPart = hit.part; }
            }
          }

          const key = `${label}-${side}`;
          const base = reference[`Bottom-${side}`];
          const shift = (v: Vector3, b?: Vector3) => (b ? `${((v.x - b.x) * 1000).toFixed(1)}` : '—');
          const twist = base
            ? ((Math.acos(Math.min(1, Math.abs(axis.dot(base.axis)))) * 180) / Math.PI).toFixed(1)
            : '—';
          rows.push(
            [
              `${label} ${value}°`, side,
              `${(shoulder.x * 1000).toFixed(0)}/${(shoulder.z * 1000).toFixed(0)}`,
              `${(elbow.x * 1000).toFixed(0)}/${(elbow.z * 1000).toFixed(0)}`,
              `${(gripCentre.x * 1000).toFixed(0)}/${(gripCentre.z * 1000).toFixed(0)}`,
              `${(plateCentre.x * 1000).toFixed(0)}/${(plateCentre.z * 1000).toFixed(0)}`,
              bestRegion,
              bestPart,
              `${(bestPoint.x * 1000).toFixed(0)}/${(bestPoint.y * 1000).toFixed(0)}/${(bestPoint.z * 1000).toFixed(0)}`,
              `${(gripToBody * 1000).toFixed(1)}`,
              `${(best * 1000).toFixed(2)}`,
              `${shift(shoulder, base?.shoulder)}/${shift(elbow, base?.elbow)}/${shift(gripCentre, base?.grip)}/${shift(plateCentre, base?.plate)}`,
              twist,
            ].join(' | '),
          );
          if (value === 3 && label === 'Bottom') {
            reference[key] = { grip: gripCentre.clone(), plate: plateCentre.clone(), axis: axis.clone(), shoulder: shoulder.clone(), elbow: elbow.clone(), hand: frameOrigin.clone() };
            if (side === 'l' && process.env.DUMP) {
              const points: number[] = [];
              for (const mesh of character.meshes) {
                for (let index = 0; index < mesh.geometry.getAttribute('position').count; index += 1) {
                  mesh.getVertexPosition(index, vertex);
                  vertex.applyMatrix4(mesh.matrixWorld);
                  points.push(Number(vertex.x.toFixed(4)), Number(vertex.y.toFixed(4)), Number(vertex.z.toFixed(4)));
                }
              }
              writeFileSync(process.env.DUMP, JSON.stringify({
                points,
                shoulder: shoulder.toArray(), elbow: elbow.toArray(), wrist: wrist.toArray(),
                frameOrigin: frameOrigin.toArray(), gripCentre: gripCentre.toArray(),
                plateCentre: plateCentre.toArray(), axis: axis.toArray(),
                closest: bestPoint.toArray(), region: bestRegion, distance: best,
                plateRadius: PLATE_RADIUS,
              }));
            }
          }
        }
      }
    }
    console.log('\nCONTACT_DIAG');
    console.log('pose | side | shoulder x/z | elbow x/z | grip x/z | inboard plate x/z | region | part | closest body pt x/y/z | grip-to-body | clearance | Δx sh/el/grip/plate | axis Δ°');
    for (const row of rows) console.log(row);
  });
});
