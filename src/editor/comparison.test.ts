import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { frontPoseDiagram } from './comparison';

const clip = generateClip(canonicalSkeleton, bicepCurl);

describe('pose comparison diagram', () => {
  it('keeps every projected core-bone endpoint inside the normalised viewport', () => {
    const diagram = frontPoseDiagram(clip.keyframes[0].pose);
    expect(diagram.length).toBeGreaterThan(15);
    for (const line of diagram) {
      for (const value of [line.x1, line.y1, line.x2, line.y2]) {
        expect(value).toBeGreaterThanOrEqual(0);
        expect(value).toBeLessThanOrEqual(1);
      }
    }
  });

  it('shows the curl peak as a different forearm shape from the start pose', () => {
    const start = frontPoseDiagram(clip.keyframes[0].pose).find((line) => line.bone === 'forearm_l')!;
    const peak = frontPoseDiagram(clip.keyframes[1].pose).find((line) => line.bone === 'forearm_l')!;
    const distance = Math.hypot(start.x2 - peak.x2, start.y2 - peak.y2);
    expect(distance).toBeGreaterThan(0.08);
  });
});
