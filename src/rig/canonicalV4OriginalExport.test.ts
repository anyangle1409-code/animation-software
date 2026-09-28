import { describe, expect, it } from 'vitest';
import { HGPT_CANONICAL_V4_ORIGINAL_BONES } from './canonicalV4Original';
import { originalV4RigData } from './canonicalV4OriginalExport';

describe('Blender v4 ORIGINAL rig handoff', () => {
  it('exports every name, parent and rest endpoint without a v3 dependency', () => {
    const data = originalV4RigData();
    expect(data.identity).toBe('hgpt_canonical_v4_original');
    expect(data.coordinate_system).toBe('project_x_right_y_up_z_forward');
    expect(data.bones).toHaveLength(63);
    expect(data.bones).toEqual(HGPT_CANONICAL_V4_ORIGINAL_BONES.map(b => ({
      name: b.name, parent: b.parent,
      head: [b.head.x, b.head.y, b.head.z],
      tail: [b.tail.x, b.tail.y, b.tail.z],
    })));
    expect(data.bones.find(b => b.name === 'head')?.tail[1]).toBe(1.82);
  });
});
