import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('legacy clip builder containment', () => {
  it('removes both production and test-only legacy clip builders', () => {
    expect(() => readFileSync(new URL('./clipBuilder.ts', import.meta.url), 'utf8')).toThrow();
    expect(() =>
      readFileSync(new URL('./test/clipBuilderCompat.ts', import.meta.url), 'utf8'),
    ).toThrow();
  });

  it('keeps the live equipment viewer off the legacy clip builder', () => {
    const source = readFileSync(
      new URL('../viewer/equipmentDisplayTransforms.ts', import.meta.url),
      'utf8',
    );
    expect(source).not.toContain('../export/clipBuilder');
    expect(source).toContain('handAttachmentLocalMatrix');
  });

  it('keeps animation clip/keyframe construction out of the character production boundary', () => {
    const source = readFileSync(new URL('../character/bones.ts', import.meta.url), 'utf8');
    expect(source).not.toMatch(/AnimationClip|KeyframeTrack|InterpolateLinear/);
  });

  it('does not expose a legacy clip builder from the production export barrel', () => {
    const source = readFileSync(new URL('./index.ts', import.meta.url), 'utf8');
    expect(source).not.toContain("export * from './clipBuilder'");
  });
});
