import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (relative: string) =>
  readFileSync(new URL(relative, import.meta.url), 'utf8');

describe('live first-party viewport cutover', () => {
  it('uses the Home Gym PT scene host and WebGL renderer in production', () => {
    const runtime = read('./firstPartyViewportRuntime.ts');
    expect(runtime).toContain("from './firstPartySceneHost'");
    expect(runtime).toContain("from './firstPartyRendererAdapter'");
    expect(runtime).not.toContain('threeSceneHost');
    expect(runtime).not.toContain('threeRendererAdapter');
    expect(runtime).toContain("hgptRendererBackend = 'home-gym-pt-webgl2'");
  });

  it('uses the complete first-party Studio scene controller', () => {
    const dom = read('./firstPartyViewportDom.ts');
    expect(dom).toContain("from './firstPartyStudioSceneController'");
    expect(dom).not.toContain("from './studioSceneController'");
  });
});
