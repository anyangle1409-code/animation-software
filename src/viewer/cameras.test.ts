import { describe, expect, it } from 'vitest';
import { CAMERA_LABELS, resolveCamera } from './cameras';
import { CAMERA_PRESET_IDS } from './cameraTypes';

const recommendation = { preset: 'three_quarter' as const };

describe('diagnostic camera modes', () => {
  it('exposes Focus selected as a camera choice', () => {
    expect(CAMERA_PRESET_IDS).toContain('focus');
    expect(CAMERA_LABELS.focus).toBe('Focus selected');
  });

  it('keeps focus out of the static camera resolver because it follows the live joint', () => {
    expect(resolveCamera('focus', recommendation)).toBeNull();
  });

  it('leaves the existing recommended framing unchanged', () => {
    const camera = resolveCamera('recommended', recommendation);
    expect(camera).not.toBeNull();
    expect(camera?.fov).toBe(38);
  });
});
