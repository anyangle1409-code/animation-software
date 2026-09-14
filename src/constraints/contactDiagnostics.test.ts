import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { pullUp } from '../exercises/definitions/pullUp';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { vec3 } from '../rig/types';
import { lockAnchors } from './locks';
import { contactDiagnostics } from './contactDiagnostics';

const skeleton = canonicalSkeleton;

const anchorsFor = (clip: ReturnType<typeof generateClip>) =>
  lockAnchors(new PoseEvaluation(skeleton), sampleClip(clip, 0).pose, clip.locks);

describe('live contact diagnostics', () => {
  it('reports the curl floor locks from the same resolved frame used by the viewport', () => {
    const clip = generateClip(skeleton, bicepCurl);
    const diagnostics = contactDiagnostics(
      skeleton,
      new PoseEvaluation(skeleton),
      clip,
      clip.duration * 0.5,
      anchorsFor(clip),
    );

    expect(diagnostics).toHaveLength(2);
    for (const diagnostic of diagnostics) {
      expect(diagnostic.mode).toBe('floor');
      expect(diagnostic.target).not.toBeNull();
      expect(diagnostic.actual).not.toBeNull();
      expect(Number.isFinite(diagnostic.error)).toBe(true);
      expect(diagnostic.error!).toBeLessThan(0.01);
      expect(diagnostic.status).not.toBe('unresolved');
    }
  });

  it('resolves pull-up hand contacts through the rack sockets', () => {
    const clip = generateClip(skeleton, pullUp);
    const diagnostics = contactDiagnostics(
      skeleton,
      new PoseEvaluation(skeleton),
      clip,
      clip.duration * 0.45,
    );

    expect(diagnostics).toHaveLength(2);
    for (const diagnostic of diagnostics) {
      expect(diagnostic.mode).toBe('equipment');
      expect(diagnostic.equipmentId).toBe('rack');
      expect(diagnostic.socket).toMatch(/^pullup_[lr]$/);
      expect(diagnostic.target).not.toBeNull();
      expect(diagnostic.actual).not.toBeNull();
      expect(Number.isFinite(diagnostic.error)).toBe(true);
    }
  });

  it('surfaces a physically over-extended target instead of hiding it', () => {
    const clip = generateClip(skeleton, bicepCurl);
    const impossible = {
      ...clip,
      locks: [
        {
          id: 'far_arm',
          chain: 'arm_l' as const,
          mode: 'world' as const,
          position: vec3(8, 8, 8),
          enabled: true,
        },
      ],
    };
    const [diagnostic] = contactDiagnostics(
      skeleton,
      new PoseEvaluation(skeleton),
      impossible,
      0,
    );

    expect(diagnostic.status).toBe('overextended');
    expect(diagnostic.reached).toBe(false);
    expect(diagnostic.overExtended).toBe(true);
    expect(diagnostic.error).not.toBeNull();
    expect(diagnostic.error!).toBeGreaterThan(1);
  });
});
