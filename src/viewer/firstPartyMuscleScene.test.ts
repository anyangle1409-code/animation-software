import { describe, expect, it, vi } from 'vitest';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import {
  ACTIVATION_STYLES,
  activationMap,
  activationOf,
} from '../muscles/activation';
import { MUSCLES } from '../muscles/model';
import { canonicalSkeleton } from '../rig/skeleton';
import { createSceneState } from './sceneStateCore';
import { captureMuscleFrame } from './muscleFrameSnapshot';
import {
  applyHgMuscleFrame,
  createHgMuscleScene,
} from './firstPartyMuscleScene';
import { HgPerspectiveCamera } from '../core/sceneGraph';
import { HgPrimitiveSceneRenderer } from '../core/webglSceneRenderer';

describe('first-party muscle visual scene', () => {
  it('builds every muscle with the authored activation style', () => {
    const resources = createHgMuscleScene(bicepCurl.muscles);
    const activation = activationMap(bicepCurl.muscles);

    expect([...resources.meshes.keys()]).toEqual(
      MUSCLES.map((muscle) => muscle.id),
    );
    expect(resources.group.children).toHaveLength(MUSCLES.length);

    for (const muscle of MUSCLES) {
      const mesh = resources.meshes.get(muscle.id)!;
      const style = ACTIVATION_STYLES[
        activationOf(activation, muscle.group)
      ];
      expect(mesh.material.colour[3]).toBe(style.opacity);
      expect(mesh.material.emissiveIntensity).toBe(style.emissive);
      expect(mesh.userData.hgptMuscle).toBe(muscle.id);
      expect(mesh.geometry.positions.length).toBeGreaterThan(0);
    }

    resources.dispose();
  });

  it('applies the exact renderer-neutral muscle frame transforms', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const sceneState = createSceneState();
    sceneState.frame = resolveFrame(
      canonicalSkeleton,
      sceneState.evaluation,
      clip,
      0.8,
    );
    sceneState.evaluation.apply(sceneState.frame.pose);

    const snapshot = captureMuscleFrame(sceneState.evaluation);
    const resources = createHgMuscleScene(bicepCurl.muscles);
    applyHgMuscleFrame(resources, snapshot);

    const biceps = resources.meshes.get('biceps_l')!;
    const expected = snapshot.get('biceps_l')!;
    expect(biceps.position.toArray()).toEqual(expected.position);
    expect(biceps.quaternion.toArray()).toEqual(expected.quaternion);
    expect(biceps.scale.toArray()).toEqual(expected.scale);

    resources.dispose();
  });

  it('submits the complete overlay through the first-party scene renderer', () => {
    const resources = createHgMuscleScene(bicepCurl.muscles);
    const litDraw = vi.fn();
    const flatDraw = vi.fn();
    const renderer = new HgPrimitiveSceneRenderer(
      { draw: litDraw },
      { draw: flatDraw },
    );
    const count = renderer.render(
      resources.group,
      new HgPerspectiveCamera(),
    );

    expect(count).toBe(MUSCLES.length);
    expect(litDraw).toHaveBeenCalledTimes(MUSCLES.length);
    expect(flatDraw).not.toHaveBeenCalled();
    resources.dispose();
  });

  it('disposes deterministically', () => {
    const resources = createHgMuscleScene(bicepCurl.muscles);
    resources.dispose();
    resources.dispose();
    expect(resources.group.children).toHaveLength(0);
    expect(resources.meshes.size).toBe(0);
  });
});
