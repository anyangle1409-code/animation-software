import { describe, expect, it } from 'vitest';
import { hgRuntimeNodeName, hgRuntimeNodeNames } from './gltfRuntimeNames';

describe('first-party glTF runtime names', () => {
  it('matches the established sanitising and de-duplication contract', () => {
    expect(hgRuntimeNodeNames(['arm.R', 'arm:R', 'arm R', 'arm/R'])).toEqual([
      'armR',
      'armR_1',
      'arm_R',
      'armR_2',
    ]);
  });

  it('can continue a shared naming sequence incrementally', () => {
    const used = new Map<string, number>();
    expect(hgRuntimeNodeName('hand.L', used)).toBe('handL');
    expect(hgRuntimeNodeName('hand:L', used)).toBe('handL_1');
  });
});
