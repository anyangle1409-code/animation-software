import { describe, it } from 'vitest';
import { generateClip } from '../../src/animation/generate';
import { validateClip } from '../../src/animation/validate';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { pushUp } from '../../src/exercises/definitions/pushUp';
import { shoulderPress } from '../../src/exercises/definitions/shoulderPress';
import { pullUp } from '../../src/exercises/definitions/pullUp';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';


describe('phase 2 rule check', () => {
  it('names every violated rule', () => {
    const rig = canonicalSkeleton;
    for (const ex of [bicepCurl, shoulderPress, pushUp, pullUp]) {
      const evaluation = new PoseEvaluation(rig);
      const clip = generateClip(rig, ex);
      const r = validateClip(rig, evaluation, ex, clip);
      console.log(`P2RULE ${ex.id}: ${r.violations.length ? r.violations.map((v) => `${v.ruleId} (${v.label}) worst ${v.worst?.toFixed?.(3) ?? '?'}`).join(' | ') : 'clean'}`);
      if (r.unreachable.length) console.log(`  unreachable: ${r.unreachable.join(', ')}`);
    }
  });
});
