import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Matrix4, Quaternion, Vector3 } from 'three';
import type { Bone } from 'three';
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

/**
 * The wrist, in the order the body does it.
 *
 * A forearm pronates first and the wrist then bends relative to the pronated
 * forearm, so the relative rotation is split the same way: a twist about the
 * forearm's long axis, then a swing. The twist is pronation/supination — a
 * radioulnar motion, not wrist motion. The swing is the wrist angulation, and
 * because its axis is perpendicular to the forearm it resolves cleanly onto the
 * two anatomical wrist axes *after* the twist has been applied to them, which is
 * what stops a pronation from being reported as a 95° sideways deviation.
 */

const rig = canonicalSkeleton;
const DEG = 180 / Math.PI;
const clamp = (value: number) => Math.min(1, Math.max(-1, value));

/** Q = swing ∘ twist, with twist about `axis`. */
function twistFirst(rotation: Quaternion, axis: Vector3) {
  const vector = new Vector3(rotation.x, rotation.y, rotation.z);
  const projected = axis.clone().multiplyScalar(vector.dot(axis));
  const twist = new Quaternion(projected.x, projected.y, projected.z, rotation.w);
  if (twist.lengthSq() < 1e-12) twist.identity();
  else twist.normalize();
  const swing = rotation.clone().multiply(twist.clone().invert());
  let twistAngle = 2 * Math.atan2(new Vector3(twist.x, twist.y, twist.z).dot(axis), twist.w) * DEG;
  // 2·atan2 runs to ±360; fold it back so a mirrored pair reads as ±the same
  // number rather than θ and 360−θ.
  while (twistAngle > 180) twistAngle -= 360;
  while (twistAngle <= -180) twistAngle += 360;
  return { swing, twist, twistAngle };
}

describe('wrist, twist then swing', () => {
  it('reports pronation, extension and deviation separately', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const source = retargetedCharacterSource({ id: 'wrist4', label: 'Wrist', data });
    const character = await source.build(rig);
    const mesh = character.meshes[0];
    const bone = (name: string): Bone => {
      const found = mesh.skeleton.bones.find((each) => each.name === name);
      if (!found) throw new Error(`no bone ${name}`);
      return found;
    };
    const head = (name: string) => new Vector3().setFromMatrixPosition(bone(name).matrixWorld);

    character.object.updateMatrixWorld(true);

    interface Setup {
      long: Vector3;
      palmar: Vector3;
      radioulnar: Vector3;
      bind: Quaternion;
      bindAngulation: number;
      /** +1 if a positive turn about `radioulnar` lifts the back of the hand. */
      extensionSign: number;
    }
    const setup: Record<string, Setup> = {};

    for (const side of ['L', 'R'] as const) {
      const parent = bone(`DEF-forearm${side}`);
      const intoParent = new Quaternion().setFromRotationMatrix(parent.matrixWorld).invert();
      const toLocal = (world: Vector3) => world.clone().applyQuaternion(intoParent).normalize();

      const long = toLocal(new Vector3().subVectors(head(`DEF-hand${side}`), head(`DEF-forearm${side}`)));
      const handLong = toLocal(
        new Vector3().subVectors(head(`DEF-f_middle01${side}`), head(`DEF-hand${side}`)),
      );
      const ulnar = toLocal(
        new Vector3().subVectors(head(`DEF-f_pinky01${side}`), head(`DEF-f_index01${side}`)),
      );
      // Forearm frame: palm normal squared up to the forearm's own long axis.
      const rawPalmar = new Vector3().crossVectors(ulnar, handLong).normalize();
      const palmar = rawPalmar.clone().addScaledVector(long, -rawPalmar.dot(long)).normalize();
      const radioulnar = new Vector3().crossVectors(long, palmar).normalize();

      const relative = new Matrix4().multiplyMatrices(
        new Matrix4().copy(parent.matrixWorld).invert(),
        bone(`DEF-hand${side}`).matrixWorld,
      );

      // Extension lifts the back of the hand, so a turn about `radioulnar` is
      // extension when it moves the hand axis *away* from the palm normal.
      const probe = handLong
        .clone()
        .applyQuaternion(new Quaternion().setFromAxisAngle(radioulnar, 0.05));
      const extensionSign = probe.dot(palmar) < handLong.dot(palmar) ? 1 : -1;

      setup[side] = {
        long,
        palmar,
        radioulnar,
        bind: new Quaternion().setFromRotationMatrix(relative),
        bindAngulation: Math.acos(clamp(handLong.dot(long))) * DEG,
        extensionSign,
      };
    }

    console.log('\nBIND OFFSET — hand axis versus forearm axis');
    for (const side of ['L', 'R'] as const) {
      console.log(`  ${side}: ${setup[side].bindAngulation.toFixed(2)}°`);
    }

    const measure = (side: 'L' | 'R') => {
      const s = setup[side];
      const relative = new Matrix4().multiplyMatrices(
        new Matrix4().copy(bone(`DEF-forearm${side}`).matrixWorld).invert(),
        bone(`DEF-hand${side}`).matrixWorld,
      );
      const now = new Quaternion().setFromRotationMatrix(relative);
      const change = now.clone().multiply(s.bind.clone().invert());

      const { swing, twist, twistAngle } = twistFirst(change, s.long);

      // The wrist axes as the pronated forearm presents them. This has to be
      // the twist itself — a rotation about the forearm axis, which keeps the
      // axes square to it — and not `change · swing⁻¹`, which is not.
      const palmar = s.palmar.clone().applyQuaternion(twist).normalize();
      const radioulnar = s.radioulnar.clone().applyQuaternion(twist).normalize();

      const swingAxis = new Vector3(swing.x, swing.y, swing.z);
      const swingAngle = 2 * Math.acos(clamp(Math.abs(swing.w))) * DEG;
      const unit = swingAxis.lengthSq() < 1e-14 ? new Vector3() : swingAxis.clone().normalize();
      const orientation = swing.w < 0 ? -1 : 1;

      const extension = s.extensionSign * orientation * swingAngle * unit.dot(radioulnar);
      const deviation = orientation * swingAngle * unit.dot(palmar);

      // Independent sanity check, free of any frame or decomposition: the plain
      // world-space angle between the forearm's direction and the hand's. This
      // is the angle an eye sees at the wrist.
      const forearmWorld = new Vector3()
        .subVectors(head(`DEF-hand${side}`), head(`DEF-forearm${side}`))
        .normalize();
      const handWorld = new Vector3()
        .subVectors(head(`DEF-f_middle01${side}`), head(`DEF-hand${side}`))
        .normalize();
      const visible = Math.acos(clamp(forearmWorld.dot(handWorld))) * DEG;

      return {
        visible,
        pronation: twistAngle,
        angulation: swingAngle,
        extension,
        deviation,
        // Should equal the angulation; if it does not, the frame is wrong.
        residual: Math.abs(Math.hypot(extension, deviation) - swingAngle),
      };
    };

    const series = new Set(['push_up', 'pull_up']);

    // HANDZ / HANDX sweep the push-up's floor contact so a placement candidate
    // is measured by this exact decomposition rather than a reimplementation.
    const handZ = process.env.HANDZ ? Number(process.env.HANDZ) : null;
    const handX = process.env.HANDX ? Number(process.env.HANDX) : null;
    const placed = handZ === null && handX === null
      ? pushUp
      : {
          ...pushUp,
          locks: pushUp.locks.map((lock) =>
            lock.mode === 'world' && /^hand_/.test(lock.id)
              ? {
                  ...lock,
                  position: {
                    x: handX === null ? lock.position.x : Math.sign(lock.position.x) * handX,
                    y: lock.position.y,
                    z: handZ === null ? lock.position.z : handZ,
                  },
                }
              : lock,
          ),
        };
    const only = process.env.ONLY_PUSHUP ? [placed] : [placed, pullUp, bicepCurl, shoulderPress];
    for (const definition of only) {
      const clip = generateClip(rig, definition);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const steps = 176;
      console.log(`\n=== ${definition.id} (${clip.duration.toFixed(2)}s)`);

      const peak: Record<string, { angulation: number; time: number; row: ReturnType<typeof measure> }> = {};
      let worstMirror = 0;
      let worstResidual = 0;
      const rows: string[] = [];

      for (let step = 0; step <= steps; step += 1) {
        const time = (clip.duration * step) / steps;
        const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
        character.object.updateMatrixWorld(true);
        const left = measure('L');
        const right = measure('R');
        worstMirror = Math.max(
          worstMirror,
          Math.abs(left.angulation - right.angulation),
          Math.abs(left.extension + right.extension),
          Math.abs(left.deviation - right.deviation),
          Math.abs(left.pronation + right.pronation),
        );
        worstResidual = Math.max(worstResidual, left.residual, right.residual);
        for (const [side, row] of [['L', left], ['R', right]] as const) {
          if (!peak[side] || row.angulation > peak[side].angulation) {
            peak[side] = { angulation: row.angulation, time, row };
          }
        }
        if (series.has(definition.id) && step % 22 === 0) {
          rows.push(
            `    t=${time.toFixed(2)}s  angulation ${left.angulation.toFixed(1).padStart(6)}°` +
              `  ext ${left.extension.toFixed(1).padStart(6)}°` +
              `  dev ${left.deviation.toFixed(1).padStart(6)}°` +
              `  pronation ${left.pronation.toFixed(1).padStart(6)}°` +
              `  visible ${left.visible.toFixed(1).padStart(6)}°`,
          );
        }
      }

      for (const side of ['L', 'R'] as const) {
        const { angulation, time, row } = peak[side];
        console.log(
          `  ${side}  peak wrist angulation ${angulation.toFixed(2)}° at ${time.toFixed(3)}s` +
            `  —  extension ${row.extension.toFixed(2)}°, deviation ${row.deviation.toFixed(2)}°,` +
            ` pronation ${row.pronation.toFixed(2)}°` +
            `\n      plain forearm-to-hand angle on screen: ${row.visible.toFixed(2)}°`,
        );
      }
      console.log(`  worst left/right mismatch: ${worstMirror.toFixed(4)}°`);
      console.log(`  worst decomposition residual: ${worstResidual.toFixed(4)}° (0 means ext/dev fully account for the angulation)`);
      if (rows.length) console.log(rows.join('\n'));
    }

    expect(true).toBe(true);
    character.dispose();
  });
});
