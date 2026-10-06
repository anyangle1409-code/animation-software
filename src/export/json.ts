import { canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { round } from '../core/math';
import type { StudioClip } from '../animation/clip';
import type { ExerciseDefinition } from '../exercises/types';
import { repetitionDuration } from '../exercises/types';
import { phaseBoundaries } from '../animation/generate';
import { bakeClipData, type BakedBoneTrackData } from './clipData';
import { MUSCLE_GROUPS } from '../muscles/groups';

export const ANIMATION_FORMAT = 'hgpt-animation';
export const METADATA_FORMAT = 'hgpt-exercise';
/**
 * Canonical skeleton identity written into animation JSON and exercise metadata.
 *
 * The live standalone runtime uses the first-party ORIGINAL-v1 v4 canonical
 * hierarchy. Export metadata must name the rig actually used; retaining the
 * historical v3 label would make PT-App provenance ambiguous and unsafe.
 */
export const SKELETON_ID = 'hgpt_canonical_v4_original';

export interface AnimationJson {
  format: typeof ANIMATION_FORMAT;
  version: 1;
  name: string;
  exerciseId: string;
  skeleton: string;
  duration: number;
  fps: number;
  loop: boolean;
  /** Rotation tracks, one per animated bone, as quaternions. */
  tracks: {
    bone: string;
    property: 'quaternion' | 'position';
    times: number[];
    values: number[];
  }[];
  /**
   * Legacy Three-compatible JSON shape, generated from project-owned baked
   * data so consumers using `AnimationClip.parse` keep working without the
   * exporter itself constructing a Three animation object.
   */
  threeClip: unknown;
}

/**
 * Animation-only export.
 *
 * Bone rotations and nothing else, so one character model can play every
 * exercise in the library rather than each exercise shipping its own copy of
 * the mesh.
 */
function legacyThreeTrackJson(track: BakedBoneTrackData) {
  return {
    name: `${track.bone}.${track.property}`,
    times: [...track.times],
    values: [...track.values],
    type: track.property === 'quaternion' ? 'quaternion' : 'vector',
  };
}

function legacyThreeClipJson(
  name: string,
  duration: number,
  tracks: readonly BakedBoneTrackData[],
): unknown {
  return {
    name,
    duration,
    tracks: tracks.map(legacyThreeTrackJson),
    uuid: `hgpt-clip-${name}`,
    // Three's normal animation blend mode. Kept as a file-format compatibility
    // value; no Three runtime object is needed to produce it.
    blendMode: 2500,
  };
}

export function exportAnimationJson(
  studioClip: StudioClip,
  exercise: ExerciseDefinition,
  rig: Skeleton = canonicalSkeleton,
  fps?: number,
): AnimationJson {
  const baked = bakeClipData(studioClip, rig, { fps });

  return {
    format: ANIMATION_FORMAT,
    version: 1,
    name: studioClip.name,
    exerciseId: exercise.id,
    skeleton: SKELETON_ID,
    duration: round(studioClip.duration, 6),
    fps: baked.fps,
    loop: studioClip.loop,
    tracks: baked.tracks.map((track) => ({
      bone: track.bone,
      property: track.property,
      times: track.times.map((time) => round(time, 5)),
      values: track.values.map((value) => round(value, 6)),
    })),
    threeClip: legacyThreeClipJson(studioClip.name, studioClip.duration, baked.tracks),
  };
}

export interface ExerciseMetadataJson {
  format: typeof METADATA_FORMAT;
  version: 1;
  exercise: ExerciseDefinition;
  derived: {
    clipName: string;
    repetitionDuration: number;
    phases: { id: string; label: string; start: number; end: number; contraction: string }[];
    muscles: {
      primary: { id: string; label: string }[];
      secondary: { id: string; label: string }[];
      stabilisers: { id: string; label: string }[];
    };
    skeleton: string;
  };
}

/**
 * The exercise as data for Home Gym PT: the whole definition plus the derived
 * numbers an app would otherwise have to recompute.
 */
export function exportMetadataJson(exercise: ExerciseDefinition): ExerciseMetadataJson {
  const label = (id: keyof typeof MUSCLE_GROUPS) => ({ id, label: MUSCLE_GROUPS[id].label });

  return {
    format: METADATA_FORMAT,
    version: 1,
    exercise,
    derived: {
      clipName: exercise.clipName,
      repetitionDuration: round(repetitionDuration(exercise), 4),
      phases: phaseBoundaries(exercise).map(({ phase, start, end }) => ({
        id: phase.id,
        label: phase.label,
        start,
        end,
        contraction: phase.contraction,
      })),
      muscles: {
        primary: exercise.muscles.primary.map(label),
        secondary: exercise.muscles.secondary.map(label),
        stabilisers: exercise.muscles.stabilisers.map(label),
      },
      skeleton: SKELETON_ID,
    },
  };
}
