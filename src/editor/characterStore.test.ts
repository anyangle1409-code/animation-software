import { afterEach, describe, expect, it } from 'vitest';
import type { CharacterBuild, DeformationControl } from '../character';
import { characterStore } from './characterStoreCore';

describe('framework-neutral character store', () => {
  it('supports direct state updates on the durable store instance', () => {
    const before = characterStore.getState().deformationRevision;
    characterStore.setState({ deformationRevision: before + 1 });
    expect(characterStore.getState().deformationRevision).toBe(before + 1);
    characterStore.setState({ deformationRevision: before });
    expect(characterStore.getState().deformationRevision).toBe(before);
  });
});

describe('character deformation review revision', () => {
  afterEach(() => {
    characterStore.setState({ active: null, deformationRevision: 0, correctivesPreview: true });
  });

  it('increments only when an effective production deformation value changes', () => {
    let value = 0.25;
    const control: DeformationControl = {
      id: 'outer-elbow',
      label: 'Outer elbow',
      min: 0,
      max: 1,
      step: 0.05,
      defaultValue: 0,
      get value() {
        return value;
      },
      set(next) {
        value = Math.max(0, Math.min(1, next));
      },
    };
    const active = {
      deformation: { update: () => undefined, controls: [control] },
    } as unknown as CharacterBuild;
    characterStore.setState({ active, deformationRevision: 0 });

    characterStore.getState().setDeformationControl('outer-elbow', 0.5);
    expect(value).toBe(0.5);
    expect(characterStore.getState().deformationRevision).toBe(1);

    characterStore.getState().setDeformationControl('outer-elbow', 0.5);
    expect(characterStore.getState().deformationRevision).toBe(1);

    characterStore.getState().setDeformationControl('missing', 0.9);
    expect(characterStore.getState().deformationRevision).toBe(1);

    characterStore.getState().setDeformationControl('outer-elbow', 2);
    expect(value).toBe(1);
    expect(characterStore.getState().deformationRevision).toBe(2);
  });
});
