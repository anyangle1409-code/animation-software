import type { Bone, KeyframeTrack, Matrix4, Object3D, SkinnedMesh, Skeleton as ThreeSkeleton } from 'three';
import type { BoneName } from '../rig/boneNames';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { GripKind } from '../exercises/types';
import type { Pose } from '../rig/types';
import type { ResolvedContact } from '../constraints/types';


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

/** Per-frame data a proportion-aware imported character may need. */
export interface CharacterPoseContext {
  contacts?: ResolvedContact[];
  /**
   * What the hands are holding this frame, for a character that carries a
   * solved grip. The canonical pose already has the authored profile baked
   * into its finger rotations; this says which family and how closed, so the
   * solved rows can be substituted at the character's own proportions.
   */
  grip?: { kind: GripKind; closure: number };
}

/**
 * Per-frame corrections belonging to one character.
 *
 * These are mesh-specific by nature — a corrective is authored against
 * particular vertices — so they travel with the source that needs them and are
 * never inherited by another. A well-weighted mesh may have none at all.
 */
export interface DeformationControl {
  /** Stable id for authoring UI and tests. */
  id: string;
  label: string;
  min: number;
  max: number;
  step: number;
  /** Value authored in the character source before interactive review. */
  defaultValue: number;
  /** Current source-level value; export reads the same backing state. */
  readonly value: number;
  note?: string;
  set(value: number): void;
}

export interface DeformationStack {
  /** Called each frame, after the bone matrices have been written. */
  update(context: DeformationContext): void;
  /** Character-specific authoring controls shared with the export sampler. */
  controls?: readonly DeformationControl[];
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
  sample(pose: Pose, context?: CharacterPoseContext): void;
  /** The tracks for everything sampled so far. */
  tracks(times: number[]): KeyframeTrack[];
}

/** Which side a hand-held item is carried on. */
export type Side = 'l' | 'r';

/** A character built and ready to mount or export. */
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

  /**
   * How this character is posed, when it is not bound to the canonical bones.
   *
   * A character that keeps its own skeleton — an import, preserved rather than
   * rebound — is driven by transferring joint angles onto that skeleton. It
   * supplies the transfer here, and `applyCharacterPose` uses it instead of
   * writing the canonical bone matrices directly.
   */
  driver?: (pose: Pose, context?: CharacterPoseContext) => void;

  /**
   * Where a hand is, in the canonical hand frame, for the equipment a hand
   * carries. Null or absent means the character's bones *are* the canonical
   * bones and the frame pipeline's own transform already applies.
   *
   * A preserved import has its own proportions, so its hand is not where the
   * canonical hand is. Equipment follows this rather than the rig, which is
   * what keeps a dumbbell in the hand of a character the rig only drives.
   */
  handMatrix?: (side: Side, target: Matrix4) => Matrix4 | null;
  
  /**
   * Centre of a held cylindrical handle inside this character's closed fist,
   * in the frame `handMatrix` returns. Distinct from that frame's own origin,
   * which is the palm contact point floor and bar locks aim at.
   */
  gripOffset?(side: Side): { x: number; y: number; z: number };
  /**
   * Key into the solved-grip table in `./solvedGrip`. A character without one
   * poses its fingers straight from the authored profile, as before.
   */
  gripSolutionId?: string;

  /**
   * Animation tracks for this character's own skeleton, when the canonical
   * bone tracks do not describe it. The exporter bakes these instead.
   */
  sampler?: () => DeformationSampler | null;

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
