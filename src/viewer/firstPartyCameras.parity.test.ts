import { describe, expect, it } from 'vitest';
import { CAMERA_PRESET_IDS } from './cameraTypes';
import { resolveCamera } from './cameras';
import { resolveHgCamera } from './firstPartyCameras';

const recommendation = { preset: 'three_quarter' as const };

function compare(preset: (typeof CAMERA_PRESET_IDS)[number]) {
  const current = resolveCamera(preset, recommendation);
  const hg = resolveHgCamera(preset, recommendation);
  expect(Boolean(hg)).toBe(Boolean(current));
  if (!current || !hg) return;

  expect(hg.position.x).toBeCloseTo(current.position.x, 12);
  expect(hg.position.y).toBeCloseTo(current.position.y, 12);
  expect(hg.position.z).toBeCloseTo(current.position.z, 12);
  expect(hg.target.x).toBeCloseTo(current.target.x, 12);
  expect(hg.target.y).toBeCloseTo(current.target.y, 12);
  expect(hg.target.z).toBeCloseTo(current.target.z, 12);
  expect(hg.fov).toBe(current.fov);
}

describe('first-party camera preset parity', () => {
  it('matches every static/resolved camera mode', () => {
    for (const preset of CAMERA_PRESET_IDS) compare(preset);
  });

  it('matches an explicit exercise camera recommendation', () => {
    const custom = {
      preset: 'front' as const,
      position: { x: 1.2, y: 2.3, z: 4.5 },
      target: { x: -0.2, y: 1.1, z: 0.3 },
      fov: 33,
    };
    const current = resolveCamera('recommended', custom);
    const hg = resolveHgCamera('recommended', custom);
    expect(current).not.toBeNull();
    expect(hg).not.toBeNull();
    expect(hg?.position.x).toBeCloseTo(current!.position.x, 12);
    expect(hg?.position.y).toBeCloseTo(current!.position.y, 12);
    expect(hg?.position.z).toBeCloseTo(current!.position.z, 12);
    expect(hg?.target.x).toBeCloseTo(current!.target.x, 12);
    expect(hg?.target.y).toBeCloseTo(current!.target.y, 12);
    expect(hg?.target.z).toBeCloseTo(current!.target.z, 12);
    expect(hg?.fov).toBe(33);
  });
});
