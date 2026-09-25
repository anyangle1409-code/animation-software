import { sortedKeyframes } from '../animation/clip';
import type { StudioClip } from '../animation/clip';
import type { ReferenceReviewView, ReferenceSpec } from './types';

export type ReviewMomentId = 'start' | 'mid_concentric' | 'peak' | 'mid_eccentric' | 'return';

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

function phaseSpan(clip: StudioClip, phaseId: string): { start: number; end: number } | null {
  const keyframes = sortedKeyframes(clip);
  for (let index = 0; index < keyframes.length - 1; index += 1) {
    if (keyframes[index].phaseId === phaseId) {
      return { start: keyframes[index].time, end: keyframes[index + 1].time };
    }
  }
  return null;
}

function markerTime(clip: StudioClip, marker: 'peak' | 'return'): number | null {
  return sortedKeyframes(clip).find((keyframe) => keyframe.marker === marker)?.time ?? null;
}

const normalized = (time: number, duration: number) => (duration <= 0 ? 0 : time / duration);

/**
 * Build deterministic local review evidence locations. This is intentionally
 * separate from rendering: any local renderer can consume the manifest later,
 * while tests can verify the exact semantic frames and cameras now.
 */
export function buildReviewManifest(reference: ReferenceSpec, clip: StudioClip): ReviewManifest {
  const concentric = phaseSpan(clip, 'concentric');
  const eccentric = phaseSpan(clip, 'eccentric');
  const peak = markerTime(clip, 'peak');
  const returned = markerTime(clip, 'return') ?? clip.duration;

  const moments: ReviewMoment[] = [
    { id: 'start', label: 'Start / stretch', time: 0, normalizedTime: 0, phaseId: clip.keyframes[0]?.phaseId },
    ...(concentric
      ? [{
          id: 'mid_concentric' as const,
          label: 'Mid concentric',
          time: (concentric.start + concentric.end) / 2,
          normalizedTime: normalized((concentric.start + concentric.end) / 2, clip.duration),
          phaseId: 'concentric',
        }]
      : []),
    ...(peak !== null
      ? [{
          id: 'peak' as const,
          label: 'Peak / contraction',
          time: peak,
          normalizedTime: normalized(peak, clip.duration),
          phaseId: 'squeeze',
        }]
      : []),
    ...(eccentric
      ? [{
          id: 'mid_eccentric' as const,
          label: 'Mid eccentric',
          time: (eccentric.start + eccentric.end) / 2,
          normalizedTime: normalized((eccentric.start + eccentric.end) / 2, clip.duration),
          phaseId: 'eccentric',
        }]
      : []),
    {
      id: 'return',
      label: 'Return',
      time: returned,
      normalizedTime: normalized(returned, clip.duration),
    },
  ];

  const views = reference.reviewViews ?? [];
  const captures = moments.flatMap((moment) =>
    views.map((view): ReviewCapture => ({
      id: `${moment.id}__${view.id}`,
      moment,
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
