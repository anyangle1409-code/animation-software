import { describe, it } from 'vitest';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { validateClip } from '../../src/animation/validate';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { toDeg } from '../../src/core/math';

describe('curl technique at the retained rebase', () => {
  it('reports every authored rule and the relative drift', () => {
    const rig = canonicalSkeleton;
    const evaluation = new PoseEvaluation(rig);
    const clip = generateClip(rig, bicepCurl);
    const result = validateClip(rig, evaluation, bicepCurl, clip);
    console.log('RULES authored:', bicepCurl.technique.map((r) => r.id).join(', '));
    console.log('VIOLATIONS:', result.violations.length ? result.violations.map((v) => `${v.ruleId}:${v.label}`).join(', ') : 'none');
    console.log('UNREACHABLE:', result.unreachable.length ? result.unreachable.join(', ') : 'none');
    console.log('LOOP CLOSED:', result.loopClosed);
    const base = bicepCurl.startPose.joints.upperarm_l?.x ?? 0;
    const baseR = bicepCurl.startPose.joints.upperarm_r?.x ?? 0;
    for (const [label, t] of [['Bottom', 0], ['Mid', 1], ['Peak', 2], ['Return', 5.5]] as [string, number][]) {
      const s = sampleClip(clip, t);
      const dl = toDeg(s.pose.rotations.upperarm_l?.x ?? 0) - base;
      const dr = toDeg(s.pose.rotations.upperarm_r?.x ?? 0) - baseR;
      console.log(`DRIFT ${label.padEnd(6)} l ${dl.toFixed(6)}  r ${dr.toFixed(6)}  elbow ${toDeg(s.pose.rotations.forearm_l?.x ?? 0).toFixed(3)}`);
    }
    const late = sampleClip(clip, 3.3);
    console.log(`DRIFT late(3.3s) l ${(toDeg(late.pose.rotations.upperarm_l?.x ?? 0) - base).toFixed(6)}  r ${(toDeg(late.pose.rotations.upperarm_r?.x ?? 0) - baseR).toFixed(6)}`);
  });
});
