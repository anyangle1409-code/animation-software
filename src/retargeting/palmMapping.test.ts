import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Bone, Euler, Group, Quaternion, Vector3 } from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { restPose } from '../rig/pose';
import { EULER_ORDER } from '../rig/types';
import { METACARPAL_BONES } from '../rig/boneNames';
import type { BoneName } from '../rig/boneNames';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { EXERCISES } from '../exercises/library';
import { createMapping, guessMapping, reportMapping } from './boneMap';
import type { BoneMapping } from './boneMap';
import { applyRetarget, bindRetarget, plausiblePalms, readCharacter } from './retarget';

/**
 * Retargeting onto characters with and without palm bones.
 *
 * A metacarpal is retargeted relative to its hand, not absolutely like a limb,
 * so a mapped palm bone rides its hand exactly until a metacarpal moves — and
 * the hand, fingers and grip of every character, palm bones or not, come out
 * as they did before the metacarpals existed. What a palm mapping adds is only
 * the palm's own motion, which no exercise authors yet.
 */
const rig = canonicalSkeleton;
const R = Math.PI / 180;
const ASSET =
  process.env.REAL_CHARACTER_GLB ?? 'review-assets/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb';

/**
 * A character with every canonical bone, rest poses deliberately off the rig's
 * — hands, palms and fingers rolled — optionally built as its mirror image,
 * with each side's geometry on the other side of the body, as the production
 * character is.
 */
function palmCharacter(mirrored: boolean, biased = true) {
  const root = new Group();
  const bones = new Map<string, Bone>();
  const swap = (name: string) => (mirrored ? name.replace(/_([lr])$/, (_, s) => (s === 'l' ? '_r' : '_l')) : name);
  for (const definition of rig.bones) {
    // A mirrored character's bone named `_l` has the geometry of the rig's `_r`.
    const source = rig.bone(swap(definition.name) as BoneName);
    const bone = new Bone();
    bone.name = definition.name;
    bone.position.copy(source.offset);
    bone.quaternion.copy(source.restLocalQuaternion);
    const side = definition.name.endsWith('_l') ? 1 : definition.name.endsWith('_r') ? -1 : 0;
    const rotate = (axis: Vector3, degrees: number) =>
      bone.quaternion.multiply(new Quaternion().setFromAxisAngle(axis, (degrees * Math.PI) / 180));
    if (biased && /^hand_/.test(definition.name)) rotate(new Vector3(0, 0, 1), side * 14);
    if (biased && /^metacarpal_/.test(definition.name)) rotate(new Vector3(0.3, 1, 0.2).normalize(), side * 23);
    if (biased && /^(index|middle|ring|pinky)_01_/.test(definition.name)) rotate(new Vector3(1, 0, 0), 12);
    bones.set(definition.name, bone);
    if (definition.parent) bones.get(definition.parent)!.add(bone);
    else root.add(bone);
  }
  root.updateMatrixWorld(true);
  return readCharacter(root);
}

const withoutPalms = (mapping: BoneMapping): BoneMapping => {
  const copy = { ...mapping, bones: { ...mapping.bones } };
  for (const name of METACARPAL_BONES) delete copy.bones[name];
  return copy;
};

describe('a character with palm bones', () => {
  it.each([
    ['same-side', false],
    ['mirrored', true],
  ] as const)('%s: maps them, and at rest moves exactly as with no palm mapping at all', (_label, mirrored) => {
    const withPalm = palmCharacter(mirrored);
    const without = palmCharacter(mirrored);
    const mapping = createMapping('palm', 'palm');
    mapping.bones = guessMapping(withPalm.boneNames);
    const a = bindRetarget(withPalm, mapping);
    const b = bindRetarget(without, withoutPalms(mapping));
    expect(a.mirrorSides).toBe(mirrored);
    expect(METACARPAL_BONES.every((name) => a.mapping.bones[name] === name)).toBe(true);
    expect(METACARPAL_BONES.some((name) => b.mapping.bones[name])).toBe(false);

    let worst = 0;
    for (const exercise of EXERCISES) {
      const clip = generateClip(rig, exercise);
      for (const fraction of [0, 0.25, 0.5, 0.75]) {
        const pose = sampleClip(clip, clip.duration * fraction).pose;
        applyRetarget(a, pose);
        applyRetarget(b, pose);
        for (const [name, bone] of withPalm.bones) {
          const x = bone.matrixWorld.elements;
          const y = without.bones.get(name)!.matrixWorld.elements;
          for (let k = 0; k < 16; k += 1) worst = Math.max(worst, Math.abs(x[k] - y[k]));
        }
      }
    }
    expect(worst).toBeLessThan(1e-9);
  });

  it.each([
    ['same-side, rolled rest', false, true],
    ['mirrored, rolled rest', true, true],
    ['same-side, rig proportions', false, false],
    ['mirrored, rig proportions', true, false],
  ] as const)('%s: carries a metacarpal\'s own motion onto the palm and the finger it holds', (_label, mirrored, biased) => {
    const character = palmCharacter(mirrored, biased);
    const mapping = createMapping('palm', 'palm');
    mapping.bones = guessMapping(character.boneNames);
    const binding = bindRetarget(character, mapping);
    const evaluation = new PoseEvaluation(rig);
    const pose = restPose();
    applyRetarget(binding, pose);
    const hand = character.bones.get('hand_l')!;
    const palm = character.bones.get('metacarpal_pinky_l')!;
    const relativeAtRest = hand.getWorldQuaternion(new Quaternion()).invert().multiply(palm.getWorldQuaternion(new Quaternion()));

    // Cup the little finger's metacarpal: 20° of flexion, 10° towards the thumb.
    pose.rotations.metacarpal_pinky_l = { x: 0, y: 10 * R, z: 20 * R };
    applyRetarget(binding, pose);
    evaluation.apply(pose);
    const relative = hand.getWorldQuaternion(new Quaternion()).invert().multiply(palm.getWorldQuaternion(new Quaternion()));
    const turned = (2 * Math.acos(Math.min(1, Math.abs(relativeAtRest.clone().invert().multiply(relative).w)))) / R;
    const canonical = (2 * Math.acos(Math.min(1, Math.abs(new Quaternion().setFromEuler(new Euler(0, 10 * R, 20 * R, EULER_ORDER)).w)))) / R;
    expect(canonical).toBeGreaterThan(20);
    // The palm bone turns relative to its hand by exactly the metacarpal's angle.
    expect(Math.abs(turned - canonical)).toBeLessThan(1e-6);
    // And the knuckle it carries swings with it: about the palm bone's base,
    // through the same angle and at the same radius as the rig's knuckle about
    // its metacarpal's base. Measured about the base, so the check does not
    // depend on the hand frame, which the retargeter already places within its
    // own palm tolerance (0.57° off the rig's, for this very geometry, before
    // any palm bone moves). Checked on the characters whose rest geometry is
    // the rig's own; a rolled rest carries its knuckles somewhere else.
    if (biased) return;
    const swing = (base: Vector3, before: Vector3, after: Vector3) => ({
      radius: before.distanceTo(base),
      angle: before.clone().sub(base).angleTo(after.clone().sub(base)) / R,
    });
    const at = (name: string) => character.bones.get(name)!.getWorldPosition(new Vector3());
    const rest = restPose();
    applyRetarget(binding, rest);
    evaluation.apply(rest);
    const baseRest = at('metacarpal_pinky_l');
    const knuckleRest = at('pinky_01_l');
    const rigBase = evaluation.head('metacarpal_pinky_l', new Vector3());
    const rigKnuckleRest = evaluation.head('pinky_01_l', new Vector3());
    applyRetarget(binding, pose);
    evaluation.apply(pose);
    const moved = swing(baseRest, knuckleRest, at('pinky_01_l').sub(at('metacarpal_pinky_l')).add(baseRest));
    const expected = swing(rigBase, rigKnuckleRest, evaluation.head('pinky_01_l', new Vector3()).sub(evaluation.head('metacarpal_pinky_l', new Vector3())).add(rigBase));
    // 20° exactly: the 10° about the metacarpal's own axis cannot swing a
    // knuckle that lies on that axis; the flexion does.
    expect(expected.angle).toBeCloseTo(20, 9);
    // The swing's axis comes through the character's hand frame, so it can be
    // no truer than that frame is, and it is held to exactly that. For this
    // geometry the retargeter places the hand 0.57° off the rig's (a knuckle
    // mean against the rig's own hand tail), and — measured on the 55-bone rig
    // too, with no palm bones anywhere — a mirrored character's knuckle fan
    // 5.55° off: a property of hand retargeting that predates the palm, which
    // palm mapping leaves exactly as it was (the rest-pose test above). The
    // swing itself lands within 0.1° of the rig's in both conventions.
    // Measured from the hand's geometry — wrist to knuckle centre, and across
    // the knuckle fan — so it reads the same on a mirrored character, whose bone
    // frames belong to the other side's geometry.
    const handAxes = (point: (name: string) => Vector3) => {
      const wrist = point('hand_l');
      const knuckles = ['index', 'middle', 'ring', 'pinky'].map((finger) => point(`${finger}_01_l`));
      const centre = knuckles.reduce((sum, knuckle) => sum.add(knuckle), new Vector3()).multiplyScalar(0.25);
      return [centre.sub(wrist), knuckles[0].clone().sub(knuckles[3])];
    };
    applyRetarget(binding, rest);
    evaluation.apply(rest);
    const flip = (v: Vector3) => (mirrored ? new Vector3(-v.x, v.y, v.z) : v);
    const characterAxes = handAxes((name) => flip(at(name)));
    const rigAxes = handAxes((name) => evaluation.head(name as BoneName, new Vector3()));
    const handOffset = Math.max(...characterAxes.map((axis, index) => axis.angleTo(rigAxes[index]) / R));
    expect(handOffset).toBeLessThan(mirrored ? 5.6 : 0.6);
    expect(Math.abs(moved.angle - expected.angle)).toBeLessThan(Math.min(handOffset, 0.1));
    expect(Math.abs(moved.radius - expected.radius)).toBeLessThan(1e-9);
  });
});

describe.skipIf(!existsSync(ASSET))('the production character\'s palm bones', () => {
  it('are recognised by name and refused on measurement, leaving its fingers on its hand', async () => {
    const bytes = readFileSync(ASSET);
    const scene = (await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '')).scene;
    scene.updateMatrixWorld(true);
    const character = readCharacter(scene);
    const mapping = createMapping('production', 'production');
    mapping.bones = guessMapping(character.boneNames);
    // Rigify's DEF-palm bones are guessed as the metacarpals...
    expect(mapping.bones.metacarpal_index_l).toBe('DEF-palm01L');
    expect(mapping.bones.metacarpal_pinky_r).toBe('DEF-palm04R');
    // ...and every one of them fails: a metacarpal's base lies inside its hand.
    const kept = plausiblePalms(character, mapping);
    expect(METACARPAL_BONES.filter((name) => kept.bones[name])).toEqual([]);
    for (const side of ['l', 'r'] as const) {
      for (const finger of ['index', 'middle', 'ring', 'pinky'] as const) {
        const base = character.restWorldPosition.get(mapping.bones[`metacarpal_${finger}_${side}`]!)!;
        const knuckle = character.restWorldPosition.get(mapping.bones[`${finger}_01_${side}`]!)!;
        const wrist = character.restWorldPosition.get(mapping.bones[`hand_${side}`]!)!;
        expect(base.distanceTo(knuckle) / wrist.distanceTo(knuckle), `${finger} ${side}`).toBeGreaterThan(1.4);
      }
    }
    const binding = bindRetarget(character, mapping);
    expect(METACARPAL_BONES.some((name) => binding.mapping.bones[name])).toBe(false);
    expect(reportMapping(binding.mapping).missing).toEqual(expect.arrayContaining(METACARPAL_BONES));
    expect(reportMapping(binding.mapping).missingRequired).toEqual([]);
  });
});
