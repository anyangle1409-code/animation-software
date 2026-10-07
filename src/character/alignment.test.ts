import { describe, expect, it } from 'vitest';
import { Bone, Quaternion, Vector3 } from 'three';
import { BoneCorrector, parseCorrections, serializeCorrections, ZERO_CORRECTION } from './alignment';

function chain() {
  const root = new Bone(); root.name = 'root';
  const arm = new Bone(); arm.name = 'upperarm_l'; arm.position.set(0.2, 1.4, 0);
  root.add(arm);
  root.updateMatrixWorld(true);
  return { root, arm };
}

describe('bone alignment corrections', () => {
  it('applies a correction once, not cumulatively, on a bone the driver does not rewrite', () => {
    const { root, arm } = chain();
    const corrector = new BoneCorrector();
    const corrections = { upperarm_l: { ...ZERO_CORRECTION, ty: 2, rz: 10 } };
    for (let frame = 0; frame < 5; frame++) corrector.apply([root, arm], corrections, root);
    expect(arm.position.y).toBeCloseTo(1.42, 6);
    const expected = new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), (10 * Math.PI) / 180);
    expect(arm.quaternion.angleTo(expected)).toBeLessThan(1e-6);
  });

  it('re-applies on top of a fresh driven pose each frame', () => {
    const { root, arm } = chain();
    const corrector = new BoneCorrector();
    const corrections = { upperarm_l: { ...ZERO_CORRECTION, tx: 1 } };
    for (let frame = 0; frame < 3; frame++) {
      arm.position.set(0.3, 1.4, 0); // the driver writes the bone every frame
      corrector.apply([root, arm], corrections, root);
    }
    expect(arm.position.x).toBeCloseTo(0.31, 6);
  });

  it('removes a correction cleanly when it is reset', () => {
    const { root, arm } = chain();
    const corrector = new BoneCorrector();
    corrector.apply([root, arm], { upperarm_l: { ...ZERO_CORRECTION, tz: 3, rx: 20 } }, root);
    corrector.apply([root, arm], {}, root);
    expect(arm.position.z).toBeCloseTo(0, 6);
    expect(arm.quaternion.angleTo(new Quaternion())).toBeLessThan(1e-6);
  });

  it('works on matrix-driven bones (canonical bind)', () => {
    const { root, arm } = chain();
    arm.matrixAutoUpdate = false;
    arm.updateMatrix();
    const corrector = new BoneCorrector();
    for (let frame = 0; frame < 4; frame++) corrector.apply([root, arm], { upperarm_l: { ...ZERO_CORRECTION, ty: -1 } }, root);
    const p = new Vector3().setFromMatrixPosition(arm.matrix);
    expect(p.y).toBeCloseTo(1.39, 6);
  });

  it('round-trips through text and rejects bad input', () => {
    const text = serializeCorrections({ a: { ...ZERO_CORRECTION, rx: 5 }, b: { ...ZERO_CORRECTION } });
    expect(Object.keys(JSON.parse(text))).toEqual(['a']);
    expect(parseCorrections(text).a.rx).toBe(5);
    expect(() => parseCorrections('{"a": {"rx": "x"}}')).toThrow();
    expect(() => parseCorrections('[1]')).toThrow();
  });
});
