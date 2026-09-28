import type { ResolvedContact } from '../constraints/types';
import type { BoneName } from '../rig/boneNames';

type MatrixReader = { readonly elements: ArrayLike<number> };

/** Only the resolved world matrices needed by a scene adapter. */
export interface SceneFrameSnapshot {
  readonly time: number;
  readonly phaseId?: string;
  /** Column-major world transforms, copied from the solved pose. */
  readonly bones: Map<BoneName, number[]>;
  readonly equipment: Map<string, number[]>;
  readonly contacts: ResolvedContact[];
}

/**
 * Copy one fully resolved frame across the renderer boundary. The reader shape
 * deliberately accepts the current Three matrices and future project-owned
 * matrices without importing either implementation at runtime.
 */
export function captureSceneFrame(
  evaluation: { matrix(name: BoneName): MatrixReader },
  frame: {
    time: number;
    phaseId?: string;
    equipment: ReadonlyMap<string, { matrix: MatrixReader }>;
    contacts: readonly ResolvedContact[];
  },
  boneNames: readonly BoneName[],
): SceneFrameSnapshot {
  const bones = new Map<BoneName, number[]>();
  for (const name of boneNames) bones.set(name, Array.from(evaluation.matrix(name).elements));

  const equipment = new Map<string, number[]>();
  for (const [id, transform] of frame.equipment) {
    equipment.set(id, Array.from(transform.matrix.elements));
  }

  const contacts = frame.contacts.map((contact) => ({
    ...contact,
    target: { ...contact.target },
    ...(contact.aim && {
      aim: {
        direction: { ...contact.aim.direction },
        ...(contact.aim.forward && { forward: { ...contact.aim.forward } }),
      },
    }),
  }));
  return { time: frame.time, phaseId: frame.phaseId, bones, equipment, contacts };
}
