import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('legacy clip builder containment', () => {
  it('removes the legacy clip builder from production source', () => {
    expect(() => readFileSync(new URL('./clipBuilder.ts', import.meta.url), 'utf8')).toThrow();
    const support = readFileSync(
      new URL('./test/clipBuilderCompat.ts', import.meta.url),
      'utf8',
    );
    expect(support).toContain("from 'three'");
  });

  it('keeps the live equipment viewer off the legacy clip builder', () => {
    const source = readFileSync(
      new URL('../viewer/equipmentDisplayTransforms.ts', import.meta.url),
      'utf8',
    );
    expect(source).not.toContain("../export/clipBuilder");
    expect(source).toContain('handAttachmentLocalMatrix');
  });

  it('keeps Three animation clip/keyframe construction out of the character production boundary', () => {
    const source = readFileSync(new URL('../character/bones.ts', import.meta.url), 'utf8');
    expect(source).not.toMatch(/AnimationClip|KeyframeTrack|InterpolateLinear/);
  });

  it('does not expose the legacy clip builder from the production export barrel', () => {
    const source = readFileSync(new URL('./index.ts', import.meta.url), 'utf8');
    expect(source).not.toContain("export * from './clipBuilder'");
  });
});
