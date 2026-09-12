import {
  Group,
  Matrix4,
  Object3D,
  Quaternion,
  QuaternionKeyframeTrack,
  Vector3,
  VectorKeyframeTrack,
} from 'three';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import { canonicalSkeleton } from '../rig/skeleton';
import type { StudioClip } from '../animation/clip';
import type { ExerciseDefinition } from '../exercises/types';
import { equipmentSocket } from '../equipment/library';
import { bakeClip, handAttachmentMatrix } from './clipBuilder';
import { buildEquipmentObject } from './rigBuilder';
import { characterSource } from '../character';
import type { CharacterBuild, CharacterSource } from '../character';

export interface GlbExportOptions {
  /** Sampling rate for the baked clip. */
  fps?: number;
  /** Include the equipment meshes in the file. */
  includeEquipment?: boolean;
  /**
   * Export the animation clip without the character mesh, so several exercises
   * can share one downloaded character instead of duplicating the whole mesh.
   */
  clipOnly?: boolean;
  /**
   * Which character to write. Defaults to the registered default, so the
   * exported file is the character the studio is showing rather than a
   * hard-wired mesh.
   */
  character?: CharacterSource | string;
}

/**
 * Export an animated GLB.
 *
 * With `clipOnly`, the file carries the bone hierarchy and the animation but no
 * mesh — which is the file you want when a dozen exercises all play on the same
 * Home Gym PT character.
 */
export async function exportGlb(
  studioClip: StudioClip,
  exercise: ExerciseDefinition,
  options: GlbExportOptions = {},
): Promise<Blob> {
  const { includeEquipment = true, clipOnly = false } = options;
  const source =
    typeof options.character === 'object' ? options.character : characterSource(options.character);
  const character = await source.build(canonicalSkeleton);
  // Whatever the character's deformation stack does beyond posing bones —
  // morph-target correctives, most of it — has to be baked in as well, or the
  // exported animation deforms differently from the studio.
  // A character with its own skeleton carries the animation on that skeleton:
  // the canonical bone tracks would name bones the exported file has no nodes
  // for, and the character's own sampler holds the retargeted rotations.
  const ownSkeleton = Boolean(character.driver);
  const sampler = clipOnly
    ? null
    : character.sampler?.() ?? character.deformation?.sampler?.() ?? null;
  const baked = bakeClip(studioClip, canonicalSkeleton, {
    fps: options.fps,
    deformation: sampler,
    boneTracks: !(ownSkeleton && !clipOnly),
  });

  const scene = new Group();
  scene.name = exercise.clipName;

  if (clipOnly) {
    scene.add(character.root);
  } else {
    scene.add(character.object);
  }

  const animations = [baked.clip];

  if (includeEquipment && !clipOnly) {
    for (const instance of studioClip.equipment) {
      if (!instance.visible) continue;
      const object = buildEquipmentObject(instance.kind);
      object.name = instance.label ?? instance.id;

      if (instance.attachment.mode === 'hand') {
        // Rigidly parented to the hand bone: no extra animation needed, and the
        // attachment stays exact in whatever engine plays the file.
        // Parented to the hand bone, whichever skeleton that hand belongs to,
        // so the attachment stays exact in whatever engine plays the file.
        const side = instance.attachment.side === 'l' ? 'hand_l' : 'hand_r';
        const hand = character.boneByName.get(side);
        const socket = equipmentSocket(instance.kind, instance.attachment.socket);
        const grip = instance.attachment.gripOffset ?? { x: 0, y: 0.045, z: 0 };
        const matrix = handAttachmentMatrix(grip, socket?.position ?? { x: 0, y: 0, z: 0 });
        if (hand) {
          // A preserved import holds its own basis and its own scale. Undo
          // both, so the item sits in the hand at its real size.
          const local = new Matrix4();
          if (hand.matrixWorld) {
            hand.updateWorldMatrix(true, false);
            const worldScale = new Vector3().setFromMatrixScale(hand.matrixWorld);
            const inverse = 1 / (worldScale.x || 1);
            local.makeScale(inverse, inverse, inverse);
          }
          const basis = correctionFor(character, side);
          if (basis) local.multiply(new Matrix4().makeRotationFromQuaternion(basis));
          object.applyMatrix4(local.multiply(matrix));
          hand.add(object);
        }
      } else if (instance.attachment.mode === 'static') {
        object.position.set(instance.position.x, instance.position.y, instance.position.z);
        scene.add(object);
      } else {
        // Driven by both hands, so its motion is baked as its own track.
        applyBakedEquipmentTrack(object, baked, instance.id);
        scene.add(object);
      }
    }
  }

  const exporter = new GLTFExporter();
  const result = await exporter.parseAsync(scene as Object3D, {
    binary: true,
    animations,
    onlyVisible: false,
    includeCustomExtensions: false,
  });

  return new Blob([result as ArrayBuffer], { type: 'model/gltf-binary' });
}

/**
 * Park a two-handed item at its first baked sample and attach the rest of the
 * motion as an animation on that object.
 */
function applyBakedEquipmentTrack(
  object: Object3D,
  baked: ReturnType<typeof bakeClip>,
  id: string,
): void {
  const track = baked.equipmentTracks.get(id);
  if (!track || track.position.length < 3) return;
  object.name = `equipment_${id}`;
  object.position.copy(new Vector3(track.position[0], track.position[1], track.position[2]));

  // three.js binds tracks by object name, which the exporter preserves.
  baked.clip.tracks.push(
    new VectorKeyframeTrack(`${object.name}.position`, baked.times, track.position),
    new QuaternionKeyframeTrack(`${object.name}.quaternion`, baked.times, track.quaternion),
  );
}

/**
 * How a character's hand bone is rotated relative to the canonical hand it
 * stands in for. Read back out of `handMatrix`, which is the one place that
 * change of basis is worked out.
 */
function correctionFor(character: CharacterBuild, side: 'hand_l' | 'hand_r'): Quaternion | null {
  if (!character.handMatrix) return null;
  const bone = character.boneByName.get(side);
  const world = character.handMatrix(side === 'hand_l' ? 'l' : 'r', new Matrix4());
  if (!bone || !world) return null;
  bone.updateWorldMatrix(true, false);
  const boneRotation = new Quaternion().setFromRotationMatrix(
    new Matrix4().extractRotation(bone.matrixWorld),
  );
  const canonical = new Quaternion().setFromRotationMatrix(new Matrix4().extractRotation(world));
  return boneRotation.invert().multiply(canonical);
}
