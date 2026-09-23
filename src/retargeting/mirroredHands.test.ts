import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Quaternion, Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { sampleClip } from '../animation/clip';
import { applyCharacterPose } from '../character/pose';
import {
  CORRECTED_HAND_FRAME,
  handFrameTurn,
  inHandFrame,
  retargetedCharacterSource,
} from '../character/retargetSource';
import { guessMapping, createMapping } from './boneMap';
import { bindRetarget, readCharacter } from './retarget';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { EXERCISES } from '../exercises/library';

/**
 * The production character is mirrored, and its hands used to roll 5.5-6.2°
 * about the forearm away from the rig's — a palm-roll correction applied
 * without the reflection every other canonical frame gets. Held here on the
 * real asset: through every exercise whose hands the character's own contact
 * solver does not re-place (the push-up's floor and the pull-up's bar are
 * solved on the character, so its hands there follow its own contacts), the
 * knuckle fan's roll about the forearm matches the rig's within 1°, and the
 * two hands match each other.
 */
const ASSET =
  process.env.REAL_CHARACTER_GLB ?? 'review-assets/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb';
const R = Math.PI / 180;

describe('grip metadata measured before the correction', () => {
  const legacy = { l: new Quaternion().setFromAxisAngle(new Vector3(0, 1, 0), 0.1), r: new Quaternion() };

  it('is turned into the corrected hand frame, unless it says it was measured there', () => {
    const offsets = { l: { x: 0.015, y: 0.055, z: 0.012 }, r: { x: -0.015, y: 0.055, z: 0.012 } };
    const turned = inHandFrame(offsets, handFrameTurn(undefined, legacy))!;
    const expected = new Vector3(0.015, 0.055, 0.012).applyQuaternion(legacy.l);
    expect(new Vector3(turned.l!.x, turned.l!.y, turned.l!.z).distanceTo(expected)).toBeLessThan(1e-15);
    expect(turned.r).toEqual(offsets.r);
    expect(inHandFrame(offsets, handFrameTurn(CORRECTED_HAND_FRAME, legacy))).toEqual(offsets);
    expect(inHandFrame(undefined, legacy)).toBeUndefined();
  });
});

describe.skipIf(!existsSync(ASSET))('the production character\'s hands', () => {
  it('were rolled by twice the palm-roll angle, and only that', async () => {
    const bytes = readFileSync(ASSET);
    const scene = (await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '')).scene;
    scene.updateMatrixWorld(true);
    const character = readCharacter(scene);
    const mapping = createMapping('production', 'production');
    mapping.bones = guessMapping(character.boneNames);
    const binding = bindRetarget(character, mapping, canonicalSkeleton);
    expect(binding.mirrorSides).toBe(true);
    for (const side of ['l', 'r'] as const) {
      // 2 × 2.770°: the turn embedded grip offsets are carried through.
      const turn = binding.legacyHandFrame[side];
      expect(2 * Math.acos(Math.min(1, Math.abs(turn.w))) / R, side).toBeCloseTo(5.54, 1);
      // About the hand's own axis, so the wrist and the hand's direction stay put.
      const axis = new Vector3(turn.x, turn.y, turn.z).normalize();
      expect(Math.abs(axis.y), side).toBeGreaterThan(0.999);
    }
  });

  it('roll with the rig\'s, about the forearm, in every exercise it does not re-solve', async () => {
    const bytes = readFileSync(ASSET);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({ id: ASSET, label: ASSET, data }).build(canonicalSkeleton);
    const body = (character.meshes as SkinnedMesh[]).find((mesh) => /freeman/i.test(mesh.name))!;
    const at = (name: string) => {
      const position = body.skeleton.bones.find((bone) => bone.name === name)!.getWorldPosition(new Vector3());
      return position.setX(-position.x); // its left lies on the rig's right
    };
    /** Roll of the index-to-little knuckle fan about the forearm axis, from a fixed reference. */
    const roll = (fan: Vector3, axis: Vector3) => {
      const reference = new Vector3(0, 1, 0).addScaledVector(axis, -axis.y).normalize();
      const flat = fan.clone().addScaledVector(axis, -fan.dot(axis)).normalize();
      return Math.atan2(reference.clone().cross(flat).dot(axis), reference.dot(flat)) / R;
    };

    for (const exercise of EXERCISES.filter((entry) => !['push_up', 'pull_up'].includes(entry.id))) {
      const evaluation = new PoseEvaluation(canonicalSkeleton);
      const clip = generateClip(canonicalSkeleton, exercise);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      let worst = 0;
      for (let step = 0; step <= 20; step += 1) {
        const frame = resolveFrame(canonicalSkeleton, evaluation, clip, (step / 20) * clip.duration, { anchors });
        evaluation.apply(frame.pose);
        applyCharacterPose(character, canonicalSkeleton, frame.pose, evaluation, { contacts: frame.contacts });
        body.skeleton.update();
        const errors = (['l', 'r'] as const).map((side) => {
          const S = side === 'l' ? 'L' : 'R';
          const forearm = at(`DEF-hand${S}`).sub(at(`DEF-forearm${S}`)).normalize();
          const fan = at(`DEF-f_index01${S}`).sub(at(`DEF-f_pinky01${S}`));
          const rigForearm = evaluation.head(`hand_${side}`, new Vector3()).sub(evaluation.head(`forearm_${side}`, new Vector3())).normalize();
          const rigFan = evaluation.head(`index_01_${side}`, new Vector3()).sub(evaluation.head(`pinky_01_${side}`, new Vector3()));
          return Math.abs(roll(fan, forearm) - roll(rigFan, rigForearm));
        });
        worst = Math.max(worst, ...errors);
        expect(Math.abs(errors[0] - errors[1]), `${exercise.id} hands differ`).toBeLessThan(1e-6);
      }
      expect(worst, exercise.id).toBeLessThan(1);
    }
    character.dispose?.();
  }, 60_000);
});
