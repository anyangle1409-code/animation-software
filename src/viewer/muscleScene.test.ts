import { Color } from 'three';
import { describe, expect, it, vi } from 'vitest';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { ACTIVATION_STYLES, activationMap, activationOf } from '../muscles/activation';
import { MUSCLES } from '../muscles/model';
import { createMuscleScene } from './muscleScene';

describe('host-neutral muscle scene', () => {
  it('builds every overlay muscle with the authored activation style', () => {
    const resources = createMuscleScene(bicepCurl.muscles);
    const activation = activationMap(bicepCurl.muscles);

    expect([...resources.meshes.keys()]).toEqual(MUSCLES.map((muscle) => muscle.id));
    expect(resources.group.children).toHaveLength(MUSCLES.length);

    for (const muscle of MUSCLES) {
      const mesh = resources.meshes.get(muscle.id)!;
      const style = ACTIVATION_STYLES[activationOf(activation, muscle.group)];
      expect(mesh.material.color.getHex()).toBe(new Color(style.colour).getHex());
      expect(mesh.material.emissive.getHex()).toBe(new Color(style.colour).getHex());
      expect(mesh.material.emissiveIntensity).toBe(style.emissive);
      expect(mesh.material.opacity).toBe(style.opacity);
      expect(mesh.castShadow).toBe(true);
    }

    resources.dispose();
  });

  it('owns and disposes its geometry/material resources exactly once', () => {
    const resources = createMuscleScene(bicepCurl.muscles);
    const first = resources.meshes.values().next().value!;
    const geometryDispose = vi.spyOn(first.geometry, 'dispose');
    const materialDispose = vi.spyOn(first.material, 'dispose');

    resources.dispose();
    resources.dispose();

    expect(geometryDispose).toHaveBeenCalledTimes(1);
    expect(materialDispose).toHaveBeenCalledTimes(1);
    expect(resources.group.children).toHaveLength(0);
  });
});
