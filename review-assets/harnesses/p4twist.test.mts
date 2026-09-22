import { readFileSync } from 'node:fs';
import { describe, it } from 'vitest';
import { Matrix4, Quaternion, Vector3 } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { pushUp } from '../../src/exercises/definitions/pushUp';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';

/**
 * Where does the forearm's pronation actually live?
 *
 * A Rigify deform forearm is two bones: DEF-forearm.L at the elbow and
 * DEF-forearm.L.001 toward the wrist, and the twist is meant to be shared so
 * the surface winds gradually. If all of it lands on one bone the skin creases
 * and flattens at that joint instead, which is what a collapsed strap looks
 * like. This measures each bone's twist about its own long axis, in the bind
 * pose and posed, so the difference is the twist that bone actually took.
 */
const DEG = 180 / Math.PI;

describe('phase 4 twist distribution', () => {
  it('reports twist per forearm bone', async () => {
    const rig = canonicalSkeleton;
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const source = retargetedCharacterSource({ id: 'tw', label: 'TW', data });
    const character = await source.build(rig);

    // Bind orientations, before any pose is applied.
    // GLTFLoader strips the dots from node names, so DEF-forearm.L.001 arrives
    // as DEF-forearmL001. Discovered by listing them rather than assumed.
    const found = character.meshes[0].skeleton.bones
      .map((b) => b.name)
      .filter((name) => /^DEF-(upper_arm|forearm|hand)/i.test(name) && /l(\.?001)?$/i.test(name));
    console.log(`TWIST nodes: ${found.join(', ')}`);
    const names = found;
    // The bones come off the skinned mesh's skeleton, which is the list every
    // other harness in this directory reads; character.root.traverse does not
    // reach them.
    const skeletonBones = character.meshes[0].skeleton.bones;
    const find = (name: string) => skeletonBones.find((b) => b.name === name) ?? null;
    character.meshes[0].skeleton.update();
    character.meshes[0].updateWorldMatrix(true, false);
    const bind = new Map<string, Quaternion>();
    for (const name of names) {
      const node = find(name);
      if (node) bind.set(name, new Quaternion().setFromRotationMatrix(new Matrix4().extractRotation(node.matrixWorld)));
    }

    const clip = generateClip(rig, pushUp);
    const evaluation = new PoseEvaluation(rig);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
    const bottom = clip.keyframes.find((k) => k.marker === 'peak')?.time ?? clip.duration / 2;
    for (const [label, time] of [['Top', 0], ['Bottom', bottom]] as [string, number][]) {
      const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
      evaluation.apply(frame.pose);
      applyCharacterPose(character, rig, frame.pose, evaluation, {
        contacts: frame.contacts,
        grip: { kind: pushUp.hands.grip, closure: pushUp.hands.closure },
      });
      character.meshes[0].skeleton.update();
      character.meshes[0].updateWorldMatrix(true, false);
      const parts: string[] = [];
      for (const name of names) {
        const node = find(name);
        const rest = bind.get(name);
        if (!node || !rest) continue;
        const now = new Quaternion().setFromRotationMatrix(new Matrix4().extractRotation(node.matrixWorld));
        const change = now.clone().multiply(rest.clone().invert());
        // Twist about the bone's own long axis, in its posed frame.
        const axis = new Vector3(0, 1, 0).applyQuaternion(now).normalize();
        const v = new Vector3(change.x, change.y, change.z);
        const projected = axis.clone().multiplyScalar(v.dot(axis));
        const twist = new Quaternion(projected.x, projected.y, projected.z, change.w);
        if (twist.lengthSq() < 1e-12) twist.identity(); else twist.normalize();
        let angle = 2 * Math.atan2(new Vector3(twist.x, twist.y, twist.z).dot(axis), twist.w) * DEG;
        while (angle > 180) angle -= 360;
        while (angle <= -180) angle += 360;
        parts.push(`${name.replace('DEF-', '').padEnd(18)} ${angle.toFixed(1).padStart(7)}°`);
      }
      console.log(`TWIST ${label}\n    ${parts.join('\n    ')}`);
    }
  }, 300000);
});
