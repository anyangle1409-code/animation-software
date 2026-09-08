import {
  AnimationClip,
  Group,
  Object3D,
  QuaternionKeyframeTrack,
  VectorKeyframeTrack,
} from 'three';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import { clone as cloneSkeleton } from 'three/examples/jsm/utils/SkeletonUtils.js';
import type { StudioClip } from '../animation/clip';
import { sampleClip } from '../animation/clip';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { resolveRetargetedEquipment } from '../equipment/attach';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import {
  applyRetarget,
  bindRetarget,
  readCharacter,
} from '../retargeting/retarget';
import type { RetargetBinding, TargetCharacter } from '../retargeting/retarget';
import { buildEquipmentObject } from './rigBuilder';

export interface RetargetedGlbOptions {
  fps?: number;
  includeEquipment?: boolean;
}

/**
 * Export the character currently loaded in the studio with the canonical clip
 * baked onto its own bone names. The preview character is cloned and never
 * mutated by export.
 */
export async function exportRetargetedGlb(
  studioClip: StudioClip,
  source: RetargetBinding,
  options: RetargetedGlbOptions = {},
): Promise<Blob> {
  const character = cloneInRestPose(source);
  const binding = bindRetarget(character, source.mapping);
  const fps = options.fps ?? studioClip.fps;
  const frameCount = Math.max(2, Math.round(studioClip.duration * fps));
  const times = Array.from(
    { length: frameCount + 1 },
    (_, index) => index === frameCount ? studioClip.duration : (index / frameCount) * studioClip.duration,
  );

  character.root.name ||= 'imported_character';
  const rotationValues = new Map(
    binding.bones.map((entry) => [entry.bone.name, [] as number[]]),
  );
  const rootPositions: number[] = [];
  const rootRotations: number[] = [];
  const equipmentValues = new Map(
    studioClip.equipment
      .filter((instance) => instance.visible)
      .map((instance) => [instance.id, { position: [] as number[], rotation: [] as number[] }]),
  );

  const evaluation = new PoseEvaluation(canonicalSkeleton);
  const anchors = lockAnchors(
    evaluation,
    sampleClip(studioClip, 0).pose,
    studioClip.locks,
  );

  for (const time of times) {
    const frame = resolveFrame(canonicalSkeleton, evaluation, studioClip, time, { anchors });
    applyRetarget(binding, frame.pose);

    for (const entry of binding.bones) {
      rotationValues.get(entry.bone.name)?.push(
        entry.bone.quaternion.x,
        entry.bone.quaternion.y,
        entry.bone.quaternion.z,
        entry.bone.quaternion.w,
      );
    }
    rootPositions.push(
      character.root.position.x,
      character.root.position.y,
      character.root.position.z,
    );
    rootRotations.push(
      character.root.quaternion.x,
      character.root.quaternion.y,
      character.root.quaternion.z,
      character.root.quaternion.w,
    );

    const equipment = resolveRetargetedEquipment(binding, studioClip.equipment);
    for (const [id, values] of equipmentValues) {
      const transform = equipment.get(id);
      if (!transform) continue;
      values.position.push(transform.position.x, transform.position.y, transform.position.z);
      values.rotation.push(
        transform.quaternion.x,
        transform.quaternion.y,
        transform.quaternion.z,
        transform.quaternion.w,
      );
    }
  }

  const tracks: (QuaternionKeyframeTrack | VectorKeyframeTrack)[] = [...rotationValues].map(
    ([name, values]) => new QuaternionKeyframeTrack(`${name}.quaternion`, times, values),
  );
  tracks.push(
    new VectorKeyframeTrack(`${character.root.name}.position`, times, rootPositions),
    new QuaternionKeyframeTrack(`${character.root.name}.quaternion`, times, rootRotations),
  );

  const scene = new Group();
  scene.name = studioClip.name;
  scene.add(character.root);

  if (options.includeEquipment !== false) {
    for (const instance of studioClip.equipment.filter((item) => item.visible)) {
      const object = buildEquipmentObject(instance.kind);
      object.name = `equipment_${instance.id}`;
      scene.add(object);
      const values = equipmentValues.get(instance.id);
      if (!values || values.position.length !== times.length * 3) continue;
      tracks.push(
        new VectorKeyframeTrack(`${object.name}.position`, times, values.position),
        new QuaternionKeyframeTrack(`${object.name}.quaternion`, times, values.rotation),
      );
    }
  }

  const clip = new AnimationClip(studioClip.name, studioClip.duration, tracks);
  const result = await new GLTFExporter().parseAsync(scene as Object3D, {
    binary: true,
    animations: [clip],
    onlyVisible: false,
    includeCustomExtensions: false,
  });
  return new Blob([result as ArrayBuffer], { type: 'model/gltf-binary' });
}

/** Clone the imported scene but restore the true import-time rest transform. */
function cloneInRestPose(source: RetargetBinding): TargetCharacter {
  const root = cloneSkeleton(source.character.root);
  let character = readCharacter(root);
  for (const [name, bone] of character.bones) {
    const rest = source.character.restLocal.get(name);
    if (rest) bone.quaternion.copy(rest);
  }
  root.position.copy(source.character.rootRestPosition);
  root.quaternion.copy(source.character.rootRestQuaternion);
  root.updateMatrixWorld(true);
  character = readCharacter(root);
  return character;
}
