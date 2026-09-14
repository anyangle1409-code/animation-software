import { resolveFrame } from '../animation/pipeline';
import type { StudioClip } from '../animation/clip';
import { applyCharacterPose } from '../character';
import type { CharacterBuild } from '../character';
import { suppressCorrectives } from '../character/correctiveDiagnostics';
import { meshStrainDiagnostics } from '../character/meshStrain';
import { PoseEvaluation, type Skeleton } from '../rig/skeleton';

export interface TimedStrainValue {
  value: number;
  time: number;
}

export interface MeshStrainWorstPoint {
  mesh: string;
  p95: TimedStrainValue;
  p99: TimedStrainValue;
  max: TimedStrainValue;
  severeCompression: TimedStrainValue;
  severeStretch: TimedStrainValue;
  sampledEdges: number;
}

const updateWorst = (current: TimedStrainValue, value: number, time: number): TimedStrainValue =>
  value > current.value ? { value, time } : current;

function applyAtTime(
  character: CharacterBuild,
  rig: Skeleton,
  clip: StudioClip,
  time: number,
  correctivesEnabled: boolean,
  evaluation: PoseEvaluation,
): void {
  const frame = resolveFrame(rig, evaluation, clip, time);
  evaluation.apply(frame.pose);
  applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
  if (!correctivesEnabled) suppressCorrectives(character.meshes);
}

/**
 * Scan strain across every authored animation frame, then restore the character
 * to the playhead pose that was active before the scan.
 *
 * The edge budget is deliberately bounded because this is an interactive
 * authoring locator, not an offline finite-element analysis. Values reuse the
 * same bind-vs-posed edge metric as the live Correctives panel.
 */
export function scanMeshStrainWorstCases(
  character: CharacterBuild,
  rig: Skeleton,
  clip: StudioClip,
  correctivesEnabled: boolean,
  restoreTime: number,
  maxEdgesPerMesh = 1200,
): MeshStrainWorstPoint[] {
  const evaluation = new PoseEvaluation(rig);
  const fps = clip.fps > 0 ? clip.fps : 30;
  const lastFrame = Math.max(1, Math.ceil(clip.duration * fps));
  const out = new Map<string, MeshStrainWorstPoint>();

  try {
    for (let frameIndex = 0; frameIndex <= lastFrame; frameIndex += 1) {
      const time = Math.min(clip.duration, frameIndex / fps);
      applyAtTime(character, rig, clip, time, correctivesEnabled, evaluation);
      for (const diagnostic of meshStrainDiagnostics(character.meshes, maxEdgesPerMesh)) {
        const current = out.get(diagnostic.mesh) ?? {
          mesh: diagnostic.mesh,
          p95: { value: -Infinity, time },
          p99: { value: -Infinity, time },
          max: { value: -Infinity, time },
          severeCompression: { value: -Infinity, time },
          severeStretch: { value: -Infinity, time },
          sampledEdges: diagnostic.sampledEdges,
        };
        current.p95 = updateWorst(current.p95, diagnostic.p95, time);
        current.p99 = updateWorst(current.p99, diagnostic.p99, time);
        current.max = updateWorst(current.max, diagnostic.max, time);
        current.severeCompression = updateWorst(
          current.severeCompression,
          diagnostic.severeCompression,
          time,
        );
        current.severeStretch = updateWorst(current.severeStretch, diagnostic.severeStretch, time);
        current.sampledEdges = diagnostic.sampledEdges;
        out.set(diagnostic.mesh, current);
      }
    }
  } finally {
    applyAtTime(character, rig, clip, restoreTime, correctivesEnabled, evaluation);
  }

  return [...out.values()].filter((item) => Number.isFinite(item.max.value));
}
