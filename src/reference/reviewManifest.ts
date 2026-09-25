import { sampleClip, sortedKeyframes } from '../animation/clip';
import type { StudioClip } from '../animation/clip';
import type { ReferenceReviewView, ReferenceSpec } from './types';

export type ReviewMomentId = 'start' | 'mid_outbound' | 'peak' | 'mid_return' | 'return';

export interface ReviewMoment {
  id: ReviewMomentId;
  label: string;
  time: number;
  normalizedTime: number;
  phaseId?: string;
}

export interface ReviewCapture {
  id: string;
  moment: ReviewMoment;
  view: ReferenceReviewView;
}

export interface ReviewManifest {
  referenceId: string;
  exerciseId: string;
  duration: number;
  moments: ReviewMoment[];
  captures: ReviewCapture[];
}

function markerTime(clip: StudioClip, marker: 'peak' | 'return'): number | null {
  return sortedKeyframes(clip).find((keyframe) => keyframe.marker === marker)?.time ?? null;
}

const normalized = (time: number, duration: number) => (duration <= 0 ? 0 : time / duration);

function moment(
  clip: StudioClip,
  id: ReviewMomentId,
  label: string,
  time: number,
): ReviewMoment {
  const clamped = Math.max(0, Math.min(clip.duration, time));
  // Sampling exactly at the loop end may wrap in some players. The phase id is
  // evidence metadata only, so read just inside the final instant there while
  // retaining the exact authored return time in the manifest.
  const phaseTime =
    clamped >= clip.duration && clip.duration > 0
      ? Math.max(0, clip.duration - 1e-9)
      : clamped;
  const phaseId = sampleClip(clip, phaseTime).phaseId;
  return {
    id,
    label,
    time: clamped,
    normalizedTime: normalized(clamped, clip.duration),
    ...(phaseId ? { phaseId } : {}),
  };
}

/**
 * Build five chronological, movement-family-independent review moments.
 *
 * "Concentric" and "eccentric" cannot define review ordering: a curl goes
 * concentric first while a squat/RDL goes eccentric first, and stepping lunges
 * call their travelling phases "step" and "drive". Every generated two-endpoint
 * clip does, however, have the same structural story:
 *
 * start -> first transition -> peak -> return transition -> returned start.
 *
 * Midpoints are therefore placed in time between the authored start/peak and
 * peak/return markers. This works for curls, presses, squats, hinges, rows and
 * stepping/static lunges without family-specific review code.
 */
export function buildReviewManifest(reference: ReferenceSpec, clip: StudioClip): ReviewManifest {
  if (!(clip.duration > 0)) throw new Error('Review capture requires a clip with positive duration.');

  const peak = markerTime(clip, 'peak');
  if (peak === null || peak <= 0 || peak >= clip.duration) {
    throw new Error(
      `Review capture requires one interior peak marker; "${clip.exerciseId}" has peak ${String(peak)} in a ${clip.duration}s clip.`,
    );
  }
  const returned = markerTime(clip, 'return') ?? clip.duration;
  if (returned <= peak) {
    throw new Error(
      `Review return (${returned}s) must occur after peak (${peak}s) for "${clip.exerciseId}".`,
    );
  }

  const moments: ReviewMoment[] = [
    moment(clip, 'start', 'Start', 0),
    moment(clip, 'mid_outbound', 'Mid outbound', peak / 2),
    moment(clip, 'peak', 'Peak / end range', peak),
    moment(clip, 'mid_return', 'Mid return', peak + (returned - peak) / 2),
    moment(clip, 'return', 'Return', returned),
  ];

  const views = reference.reviewViews ?? [];
  const captures = moments.flatMap((entry) =>
    views.map((view): ReviewCapture => ({
      id: `${entry.id}__${view.id}`,
      moment: entry,
      view,
    })),
  );

  return {
    referenceId: reference.id,
    exerciseId: clip.exerciseId,
    duration: clip.duration,
    moments,
    captures,
  };
}
