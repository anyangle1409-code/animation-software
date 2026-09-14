import { BufferAttribute, BufferGeometry, SkinnedMesh } from 'three';
import { describe, expect, it } from 'vitest';
import { correctiveDiagnostics, suppressCorrectives } from './correctiveDiagnostics';

function mesh(relative = true): SkinnedMesh {
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new BufferAttribute(new Float32Array([0, 0, 0, 1, 0, 0]), 3));
  geometry.morphTargetsRelative = relative;
  const values = relative
    ? new Float32Array([0.008, 0, 0, 0, 0, 0])
    : new Float32Array([0.008, 0, 0, 1, 0, 0]);
  const corrective = new BufferAttribute(values, 3);
  corrective.name = 'homeGymPT_elbow_l';
  const face = new BufferAttribute(new Float32Array([0, 0, 0, 0, 0, 0]), 3);
  face.name = 'smile';
  geometry.morphAttributes.position = [corrective, face];
  const skinned = new SkinnedMesh(geometry);
  skinned.name = 'Body';
  skinned.morphTargetDictionary = { homeGymPT_elbow_l: 0, smile: 1 };
  skinned.morphTargetInfluences = [0.5, 0.75];
  return skinned;
}

describe('corrective diagnostics', () => {
  it('measures relative corrective displacement and live influence', () => {
    const diagnostic = correctiveDiagnostics([mesh(true)])[0];
    expect(diagnostic.name).toBe('homeGymPT_elbow_l');
    expect(diagnostic.affectedVertices).toBe(1);
    expect(diagnostic.maxDisplacement).toBeCloseTo(0.008, 6);
    expect(diagnostic.liveMaxDisplacement).toBeCloseTo(0.004, 6);
  });

  it('preserves absolute morph convention when measuring', () => {
    expect(correctiveDiagnostics([mesh(false)])[0].maxDisplacement).toBeCloseTo(0.008, 6);
  });

  it('bypasses only Studio correctives and leaves unrelated morphs alone', () => {
    const target = mesh(true);
    suppressCorrectives([target]);
    expect(target.morphTargetInfluences).toEqual([0, 0.75]);
  });
});
