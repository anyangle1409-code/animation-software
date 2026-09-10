import type { Bone, KeyframeTrack, Object3D, SkinnedMesh, Skeleton as ThreeSkeleton } from 'three';
import type { BoneName } from '../rig/boneNames';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Pose } from '../rig/types';

/**
 * The character layer.
 *
 * The studio animates a canonical skeleton. What that skeleton *wears* is a
 * separate concern, and this is its boundary: a `CharacterSource` builds a
 * surface bound to the canonical bones, and everything downstream — viewport,
 * exporter, equipment — talks to the result rather than to any particular mesh.
 *
 * Three layers, kept apart on purpose:
 *
 * 1. **Rig** (`src/rig`) — bones, limits, poses. Knows nothing about surfaces.
 * 2. **Skinning/deformation** (this module) — how a surface is attached to
 *    those bones, plus whatever per-character corrections that surface needs.
 * 3. **Visible mesh** — the geometry and materials themselves, supplied by a
 *    source and replaceable without touching either layer above.
 */

/** The character's own surface, or the same body read as an écorché. */
export type CharacterVariant = 'skin' | 'ecorche';

/**
 * What a character can do, asked rather than assumed. The anatomy view, for
 * one, is only possible on a surface whose vertex colours the écorché mapping
 * understands — a textured import has no such mapping and must say so.
 */
export interface CharacterCapabilities {
  /** The écorché (anatomy) view can be built from this surface. */
  anatomy: boolean;
  /** Carries UVs and material maps rather than vertex colours. */
  textured: boolean;
}

export interface DeformationContext {
  rig: Skeleton;
  pose: Pose;
  evaluation: PoseEvaluation;
  character: CharacterBuild;
}

/**
 * Per-frame corrections belonging to one character.
 *
 * These are mesh-specific by nature — a corrective is authored against
 * particular vertices — so they travel with the source that needs them and are
 * never inherited by another. A well-weighted mesh may have none at all.
 */
export interface DeformationStack {
  /** Called each frame, after the bone matrices have been written. */
  update(context: DeformationContext): void;
  /**
   * A sampler for the exporter, or null when nothing extra needs baking. The
   * viewport and the exported file must deform alike, so anything `update`
   * does that the bone tracks do not carry has to come out here.
   */
  sampler?(): DeformationSampler | null;
}

/** Bakes a stack's per-frame state into animation tracks. */
export interface DeformationSampler {
  /** One resolved pose, in clip order. */
  sample(pose: Pose): void;
  /** The tracks for everything sampled so far. */
  tracks(times: number[]): KeyframeTrack[];
}

/** A character built and bound to the canonical bones, ready to mount or export. */
export interface CharacterBuild {
  /** Id of the source that produced it. */
  source: string;
  root: Bone;
  bones: Bone[];
  boneByName: Map<BoneName, Bone>;
  skeleton: ThreeSkeleton;
  /** What the viewport mounts and the exporter writes. */
  object: Object3D;
  /** Every skinned surface in the character, in draw order. */
  meshes: SkinnedMesh[];
  deformation: DeformationStack | null;
  capabilities: CharacterCapabilities;
  dispose(): void;
}

export interface CharacterBuildOptions {
  variant?: CharacterVariant;
}

/**
 * A replaceable visible character.
 *
 * `build` is async because the interesting sources load assets. The built-in
 * ones resolve immediately.
 */
export interface CharacterSource {
  id: string;
  label: string;
  /** One line for the panel. */
  note?: string;
  /** A diagnostic model rather than a presentation character. */
  diagnostic?: boolean;
  capabilities: CharacterCapabilities;
  build(rig: Skeleton, options?: CharacterBuildOptions): Promise<CharacterBuild>;
}
