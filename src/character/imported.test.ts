import { describe, expect, it } from 'vitest';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { sampleClip } from '../animation/clip';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { pushUp } from '../exercises/definitions/pushUp';
import { exportGlb } from '../export/glb';
import { anatomicalGripOffset, handAttachmentLocalMatrix } from '../equipment/attach';
import { HgMat4, HgQuat, HgVec3 } from '../core/linearMath';
import { retargetedCharacterSource } from './retargetSource';
import { applyCharacterPose } from './pose';
import type { CharacterBuild } from './types';
import { hgRigifyFixture } from '../test/rigifyGlbFixture';
import { loadHgTestGltfPlayback } from '../test/firstPartyGltfPlayback';
import { parseHgGlb } from '../core/glbContainer';
import { readHgGltfScene } from '../core/gltfScene';

/**
 * An imported character is *preserved*: the studio drives its skeleton and
 * changes nothing else about it.
 *
 * The fixture is a Rigify-shaped character built here and round-tripped
 * through a real GLB — deform-bone names, numbered spine, twist bones, and a
 * helper bone parented to the armature rather than to the head, which is the
 * arrangement that used to be read as "unweighted" surface.
 */

const rig = canonicalSkeleton;
const studioClip = generateClip(rig, bicepCurl);
/** Bottom of the rep, and the top, as clip fractions. */
const TOP = 0.4545;

function curlPose(time: number) {
  const evaluation = new PoseEvaluation(rig);
  const anchors = lockAnchors(evaluation, sampleClip(studioClip, 0).pose, studioClip.locks);
  return { frame: resolveFrame(rig, evaluation, studioClip, time, { anchors }), evaluation };
}

const fixture = hgRigifyFixture();
const importedSource = () =>
  retargetedCharacterSource({ id: 'fixture', label: 'Fixture', data: fixture.data });

/** Where a bone of the character's own skeleton has ended up. */
const boneAt = (character: CharacterBuild, name: string): HgVec3 => {
  const bone = character.bones.find(
    (each) => each.name.replace(/[.]/g, '') === name.replace(/[.]/g, ''),
  );
  if (!bone) throw new Error(`no bone ${name}`);
  bone.updateWorldMatrix(true, false);
  return new HgVec3().setFromMatrixPosition(bone.matrixWorld);
};

describe('an imported character', () => {
  it('keeps its rest geometry, changing only where it stands and how big it is', async () => {
    const source = importedSource();
    const character = await source.build(rig);

    const position = character.meshes[0].geometry.getAttribute('position');
    expect(position.count).toBe(fixture.positions.length / 3);
    // Vertex for vertex, exactly as authored. Nothing is re-placed, blended or
    // rebound: the only change is the uniform scale on the root, and that is a
    // transform, not a rewrite.
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      expect(position.getX(vertex), `x${vertex}`).toBeCloseTo(fixture.positions[vertex * 3], 6);
      expect(position.getY(vertex), `y${vertex}`).toBeCloseTo(fixture.positions[vertex * 3 + 1], 6);
      expect(position.getZ(vertex), `z${vertex}`).toBeCloseTo(fixture.positions[vertex * 3 + 2], 6);
    }

    character.object.updateWorldMatrix(true, false);
    const scale = new HgVec3();
    new HgMat4().copy(character.object.matrixWorld).decompose(
      new HgVec3(),
      new HgQuat(),
      scale,
    );
    expect(scale.x).toBeCloseTo(scale.y, 6);
    expect(scale.y).toBeCloseTo(scale.z, 6);
    expect(scale.x).toBeGreaterThan(0);
    expect(character.sourceScale).toBeCloseTo(scale.x, 6);
    expect(character.preservedGlb?.byteLength).toBe(fixture.data.byteLength);
    character.dispose();
  });

  it('drives the mapped source bones with the canonical curl', async () => {
    const character = await importedSource().build(rig);

    /** The angle at the character's own elbow, from its own bones. */
    const elbowAngle = () => {
      const shoulder = boneAt(character, 'DEF-upper_arm.R');
      const elbow = boneAt(character, 'DEF-forearm.R');
      const wrist = boneAt(character, 'DEF-hand.R');
      return elbow.clone().sub(shoulder).angleTo(wrist.clone().sub(elbow));
    };
    /** The same angle on the rig that is driving it. */
    const canonicalAngle = (evaluation: PoseEvaluation) => {
      const upper = evaluation.quaternion('upperarm_r');
      const forearm = evaluation.quaternion('forearm_r');
      return new HgVec3(0, 1, 0)
        .applyQuaternion(upper)
        .angleTo(new HgVec3(0, 1, 0).applyQuaternion(forearm));
    };

    const bottom = curlPose(0);
    applyCharacterPose(character, rig, bottom.frame.pose, bottom.evaluation);
    const low = boneAt(character, 'DEF-hand.R');
    const elbowLow = boneAt(character, 'DEF-forearm.R');
    const straight = elbowAngle();

    const top = curlPose(studioClip.duration * TOP);
    applyCharacterPose(character, rig, top.frame.pose, top.evaluation);
    const high = boneAt(character, 'DEF-hand.R');
    const elbowHigh = boneAt(character, 'DEF-forearm.R');
    const flexed = elbowAngle();

    // The hand travels the better part of a forearm, and the elbow stays where
    // it is — which is what makes it a curl rather than a row.
    expect(high.distanceTo(low)).toBeGreaterThan(0.15);
    expect(elbowHigh.distanceTo(elbowLow)).toBeLessThan(0.1);

    // And the angle that arrived at the character's elbow is the angle the rig
    // is holding, not merely some movement: this is the transfer working.
    expect(straight).toBeCloseTo(canonicalAngle(bottom.evaluation), 1);
    expect(flexed).toBeCloseTo(canonicalAngle(top.evaluation), 1);
    expect(flexed - straight).toBeGreaterThan(1.5);
    character.dispose();
  });

  it('leaves twist bones rigid with the limb that carries them', async () => {
    const character = await importedSource().build(rig);
    const twist = character.bones.find((each) => /upper_armR001|upper_arm\.R\.001/.test(each.name))!;
    const parent = twist.parent!;
    const restLocal = twist.quaternion.clone();
    const restOffset = twist.position.clone();

    for (const fraction of [0, 0.2327, TOP, 0.8]) {
      const { frame, evaluation } = curlPose(studioClip.duration * fraction);
      applyCharacterPose(character, rig, frame.pose, evaluation);

      // Never driven, so it keeps the local transform the file gave it …
      expect(twist.quaternion.angleTo(restLocal), `rotation at ${fraction}`).toBeLessThan(1e-6);
      expect(twist.position.distanceTo(restOffset), `offset at ${fraction}`).toBeLessThan(1e-9);

      // … and therefore travels with the upper arm rather than staying behind.
      parent.updateWorldMatrix(true, false);
      twist.updateWorldMatrix(true, false);
      const gap = new HgVec3()
        .setFromMatrixPosition(twist.matrixWorld)
        .distanceTo(new HgVec3().setFromMatrixPosition(parent.matrixWorld));
      expect(gap, `distance from its parent at ${fraction}`).toBeGreaterThan(0.01);
    }
    character.dispose();
  });

  it('treats helper and face bones as undriven, not as unweighted surface', async () => {
    const source = importedSource();
    const character = await source.build(rig);
    const report = source.lastReport!;

    // Every canonical bone the rig needs found a home …
    expect(report.mapping.missingRequired).toEqual([]);
    // … and the bones it has no use for are simply not driven. They are not
    // errors, and nothing about the surface they carry is redistributed.
    expect(report.passive).toBeGreaterThan(0);
    expect(report.driven + report.passive).toBe(report.bones);

    const helper = character.bones.find((each) => /jaw/i.test(each.name))!;
    expect(helper, 'the helper bone survives the import').toBeDefined();
    const restWorld = new HgVec3().setFromMatrixPosition(helper.matrixWorld);

    // It rides its parent: posing the character moves it, and it does not fly
    // off to the origin or stay pinned while the body moves.
    const { frame, evaluation } = curlPose(studioClip.duration * TOP);
    applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
    helper.updateWorldMatrix(true, false);
    const posed = new HgVec3().setFromMatrixPosition(helper.matrixWorld);
    expect(posed.length()).toBeGreaterThan(0.1);
    expect(posed.distanceTo(restWorld)).toBeLessThan(0.35);
    character.dispose();
  });

  it('keeps a hand-held item locked to the hand it is carried in', async () => {
    const character = await importedSource().build(rig);
    expect(character.handMatrix, 'a preserved import places its own hands').toBeDefined();

    const offsets: number[] = [];
    for (const fraction of [0, 0.2327, TOP, 0.8]) {
      const { frame, evaluation } = curlPose(studioClip.duration * fraction);
      applyCharacterPose(character, rig, frame.pose, evaluation);

      const held = character.handMatrix!('r', new HgMat4());
      expect(held, 'the right hand resolves').not.toBeNull();
      const grip = new HgVec3(
        held!.elements[12],
        held!.elements[13],
        held!.elements[14],
      );
      const hand = boneAt(character, 'DEF-hand.R');
      offsets.push(grip.distanceTo(hand));
    }

    // The grip frame is the hand's own, at every point in the rep — so whatever
    // is attached to it cannot drift out of the hand.
    for (const offset of offsets) expect(offset).toBeLessThan(1e-6);
    character.dispose();
  });

  it('exposes a pose-invariant local grip frame for first-party equipment export', async () => {
    const character = await importedSource().build(rig);
    expect(character.handFrameLocalMatrix).toBeDefined();

    let reference: number[] | null = null;
    for (const fraction of [0, 0.2327, TOP, 0.8]) {
      const { frame, evaluation } = curlPose(studioClip.duration * fraction);
      applyCharacterPose(character, rig, frame.pose, evaluation);

      const local = character.handFrameLocalMatrix!('r');
      expect(local).not.toBeNull();
      expect(local).toHaveLength(16);
      if (!reference) reference = local!;
      else local!.forEach((value, index) => {
        expect(value).toBeCloseTo(reference![index], 6);
      });

      const hand = character.boneByName.get('hand_r')!;
      hand.updateWorldMatrix(true, false);
      const rebuilt = new HgMat4().copy(hand.matrixWorld).multiply(
        new HgMat4().fromArray(local!),
      );
      const expected = character.handMatrix!('r', new HgMat4())!;
      expect(Math.max(
        ...rebuilt.elements.map((value, index) =>
          Math.abs(value - expected.elements[index]),
        ),
      )).toBeLessThan(1e-6);
    }

    character.dispose();
  });

  it('applies a character-authored grip-frame calibration', async () => {
    const source = retargetedCharacterSource({
      id: 'calibrated', label: 'Calibrated', data: fixture.data,
      gripFrameOffsets: { r: { x: 0.01, y: 0.02, z: -0.03 } },
    });
    const character = await source.build(rig);
    const { frame, evaluation } = curlPose(studioClip.duration * TOP);
    applyCharacterPose(character, rig, frame.pose, evaluation);
    const held = character.handMatrix!('r', new HgMat4())!;
    const grip = new HgVec3(
      held.elements[12],
      held.elements[13],
      held.elements[14],
    );
    const hand = boneAt(character, 'DEF-hand.R');
    expect(grip.distanceTo(hand)).toBeCloseTo(Math.sqrt(0.0014), 6);
    character.dispose();
  });

  it('passes resolved contacts into the preserved source-proportion solve', async () => {
    const character = await importedSource().build(rig);
    const clip = generateClip(rig, pushUp);
    const evaluation = new PoseEvaluation(rig);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);

    for (const fraction of [0, 0.45]) {
      const frame = resolveFrame(rig, evaluation, clip, clip.duration * fraction, { anchors });
      expect(frame.contacts).toHaveLength(2);
      applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
      const hand = character.handMatrix!('r', new HgMat4())!;
      const grip = new HgVec3(
        hand.elements[12],
        hand.elements[13],
        hand.elements[14],
      );
      const target = frame.contacts.find((contact) => contact.chain === 'arm_r')!.target;
      // This fixture uses the same opposite-side convention as the real asset.
      expect(Math.abs(grip.x + target.x)).toBeLessThan(0.02);
      expect(Math.abs(grip.z - target.z)).toBeLessThan(0.02);
    }
    character.dispose();
  });

  it('uses the first-party codec for a preserved import when equipment is excluded', async () => {
    const source = importedSource();
    const blob = await exportGlb(studioClip, bicepCurl, {
      fps: 20,
      character: source,
      includeEquipment: false,
    });
    const buffer = await blob.arrayBuffer();
    const view = new DataView(buffer);
    const jsonLength = view.getUint32(12, true);
    const json = JSON.parse(
      new TextDecoder().decode(new Uint8Array(buffer, 20, jsonLength)),
    ) as {
      asset: { generator?: string };
      animations: unknown[];
      meshes: unknown[];
      skins: { joints: number[] }[];
      nodes: { name?: string }[];
    };

    expect(json.asset.generator).toBe('Home Gym PT first-party codec');
    expect(json.animations).toHaveLength(1);
    expect(json.meshes.length).toBeGreaterThan(0);
    expect(json.skins).toHaveLength(1);

    const playback = await loadHgTestGltfPlayback(buffer);
    const time = studioClip.duration * TOP;
    playback.setTime(time);

    const playedHand = playback.object('DEF-handR');
    expect(playedHand, 'the first-party exported hand bone').not.toBeNull();

    const character = await importedSource().build(rig);
    const { frame, evaluation } = curlPose(time);
    applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
    const shown = boneAt(character, 'DEF-hand.R');
    const written = new HgVec3().setFromMatrixPosition(playedHand!.matrixWorld);
    expect(written.distanceTo(shown)).toBeLessThan(0.001);
    character.dispose();
  }, 30_000);

  it('exports its own mesh and skeleton, posed as the viewport poses it', async () => {
    const source = importedSource();
    const blob = await exportGlb(studioClip, bicepCurl, { fps: 20, character: source });
    const buffer = await blob.arrayBuffer();

    const view = new DataView(buffer);
    const jsonLength = view.getUint32(12, true);
    const json = JSON.parse(
      new TextDecoder().decode(new Uint8Array(buffer, 20, jsonLength)),
    ) as {
      asset: { generator?: string };
      meshes: { name?: string }[];
      skins: { joints: number[] }[];
      nodes: { name?: string; children?: number[] }[];
      animations: { channels: unknown[] }[];
    };

    // The file carries the imported character, not a rebuilt stand-in.
    expect(json.meshes.length).toBeGreaterThan(0);
    expect(json.skins).toHaveLength(1);
    const joints = json.skins[0].joints.map((node) => json.nodes[node].name ?? '');
    // The first-party writer preserves the authored GLB node names exactly;
    // The first-party writer keeps dots in the source bone names exactly.
    expect(joints).toContain('DEF-hand.R');
    expect(joints).toContain('DEF-upper_arm.R.001');
    expect(json.animations).toHaveLength(1);
    expect(json.asset.generator).toBe('Home Gym PT first-party codec');

    // The dumbbell hangs off the character's own hand bone.
    const hand = json.nodes.findIndex((node) => node.name === 'DEF-hand.R');
    expect(hand).toBeGreaterThanOrEqual(0);
    const held = (json.nodes[hand].children ?? []).map((child) => json.nodes[child].name ?? '');
    expect(held.some((name) => /dumbbell/i.test(name))).toBe(true);

    // And playing it back reproduces the pose the viewport shows.
    const playback = await loadHgTestGltfPlayback(buffer);
    const time = studioClip.duration * TOP;
    playback.setTime(time);

    const playedHand = playback.object('DEF-handR');
    expect(playedHand, 'the exported hand bone').not.toBeNull();

    const character = await importedSource().build(rig);
    const { frame, evaluation } = curlPose(time);
    applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
    const shown = boneAt(character, 'DEF-hand.R');
    const written = new HgVec3().setFromMatrixPosition(playedHand!.matrixWorld);

    // Within a millimetre: the difference is the baked clip's sampling
    // interval, not a different pose.
    expect(written.distanceTo(shown)).toBeLessThan(0.001);

    let playedDumbbell = null as import('../core/sceneGraph').HgObject3D | null;
    playback.scene.traverse((object) => {
      if (/right.*dumbbell/i.test(object.name)) playedDumbbell = object;
    });
    expect(playedDumbbell, 'the first-party dumbbell is exported').not.toBeNull();

    const expectedDumbbell = character.handMatrix!('r', new HgMat4())!
      .multiply(handAttachmentLocalMatrix(
        anatomicalGripOffset('r'),
        { x: 0, y: 0, z: 0 },
      ));
    const expectedPosition = new HgVec3().setFromMatrixPosition(expectedDumbbell);
    const writtenPosition = new HgVec3().setFromMatrixPosition(playedDumbbell!.matrixWorld);
    expect(writtenPosition.distanceTo(expectedPosition)).toBeLessThan(0.001);

    const expectedRotation = new HgQuat().setFromRotationMatrix(
      new HgMat4().extractRotation(expectedDumbbell),
    );
    const writtenRotation = new HgQuat().setFromRotationMatrix(
      new HgMat4().extractRotation(playedDumbbell!.matrixWorld),
    );
    expect(writtenRotation.angleTo(expectedRotation)).toBeLessThan(0.001);

    // Nothing about the surface changed on the way out either.
    const decoded = readHgGltfScene(parseHgGlb(buffer));
    const exportedBody = decoded.meshes.find((mesh) => mesh.name === 'FixtureBody');
    expect(exportedBody).toBeDefined();
    expect(exportedBody!.primitives[0].attributes.POSITION?.count)
      .toBe(fixture.positions.length / 3);
    character.dispose();
  }, 30_000);
});
