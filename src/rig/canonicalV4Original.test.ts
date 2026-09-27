import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { EXERCISES } from '../exercises/library';
import { IK_CHAINS } from '../ik/chains';
import { ALL_BONES, mirrorBoneName } from './boneNames';
import { Skeleton } from './skeleton';
import {
  HGPT_CANONICAL_V4_ORIGINAL_BONES,
  HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS,
  HGPT_CANONICAL_V4_ORIGINAL_ID,
} from './canonicalV4Original';

const skeleton = new Skeleton(HGPT_CANONICAL_V4_ORIGINAL_BONES);

describe('hgpt_canonical_v4_original clean numerical rest rig', () => {
  it('has a new identity and the complete project-owned 63-bone architecture', () => {
    expect(HGPT_CANONICAL_V4_ORIGINAL_ID).toBe('hgpt_canonical_v4_original');
    expect(skeleton.bones).toHaveLength(63);
    expect(new Set(skeleton.names)).toEqual(new Set(ALL_BONES));
    expect(skeleton.bone('scapula_l').parent).toBe('clavicle_l');
    expect(skeleton.bone('upperarm_l').parent).toBe('scapula_l');
    expect(skeleton.bone('metacarpal_pinky_l').parent).toBe('hand_l');
    expect(skeleton.bone('pinky_01_l').parent).toBe('metacarpal_pinky_l');
  });

  it('is finite, non-degenerate, and exactly symmetric where designed', () => {
    for (const bone of skeleton.bones) {
      expect(Number.isFinite(bone.length), bone.name).toBe(true);
      expect(bone.length, bone.name).toBeGreaterThan(0.004);
      if (!bone.name.endsWith('_l')) continue;
      const opposite = skeleton.bone(mirrorBoneName(bone.name));
      expect(opposite.restHead.x, `${bone.name} head x`).toBeCloseTo(-bone.restHead.x, 12);
      expect(opposite.restTail.x, `${bone.name} tail x`).toBeCloseTo(-bone.restTail.x, 12);
      expect(opposite.restHead.y, `${bone.name} head y`).toBeCloseTo(bone.restHead.y, 12);
      expect(opposite.restTail.y, `${bone.name} tail y`).toBeCloseTo(bone.restTail.y, 12);
      expect(opposite.restHead.z, `${bone.name} head z`).toBeCloseTo(bone.restHead.z, 12);
      expect(opposite.restTail.z, `${bone.name} tail z`).toBeCloseTo(bone.restTail.z, 12);
    }
  });

  it('matches the independently declared ORIGINAL design dimensions', () => {
    const d = HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS;
    expect(skeleton.bone('head').restTail.y).toBeCloseTo(d.height, 12);
    expect(skeleton.bone('upperarm_l').restHead.x * -2).toBeCloseTo(d.shoulderBreadth, 12);
    expect(skeleton.bone('thigh_l').restHead.x * -2).toBeCloseTo(d.hipJointBreadth, 12);
    expect(skeleton.bone('upperarm_l').length).toBeCloseTo(d.upperArmLength, 12);
    expect(skeleton.bone('forearm_l').length).toBeCloseTo(d.forearmLength, 12);
    expect(skeleton.bone('middle_01_l').length).toBeCloseTo(d.fingers.middle[0], 12);
  });

  it('contains every complete IK and hand chain', () => {
    for (const chain of Object.values(IK_CHAINS)) {
      expect(skeleton.has(chain.root), `${chain.id} root`).toBe(true);
      expect(skeleton.has(chain.mid), `${chain.id} mid`).toBe(true);
      expect(skeleton.has(chain.end), `${chain.id} end`).toBe(true);
      expect(skeleton.isAncestorOf(chain.root, chain.mid), chain.id).toBe(true);
      expect(skeleton.isAncestorOf(chain.mid, chain.end), chain.id).toBe(true);
    }
    for (const side of ['l', 'r'] as const) {
      for (const finger of ['thumb', 'index', 'middle', 'ring', 'pinky'] as const) {
        expect(skeleton.bone(`${finger}_01_${side}`).children).toContain(`${finger}_02_${side}`);
        expect(skeleton.bone(`${finger}_02_${side}`).children).toContain(`${finger}_03_${side}`);
      }
    }
  });

  it('can resolve every exercise structurally without a character asset', () => {
    for (const exercise of EXERCISES) {
      const clip = generateClip(skeleton, exercise);
      expect(clip.keyframes.length, exercise.id).toBeGreaterThan(0);
    }
  }, 60_000);

  it('does not import the v3 numerical rig definition', () => {
    const source = readFileSync(new URL('./canonicalV4Original.ts', import.meta.url), 'utf8');
    expect(source).not.toContain("from './humanoid'");
    expect(source).not.toContain('HUMANOID_BONES');
    expect(source).not.toContain('SHOULDER_WIDENING');
    expect(source).not.toContain('SHOULDER_SETBACK');
  });
});
