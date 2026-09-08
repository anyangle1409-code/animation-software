import { create } from 'zustand';
import type { BoneName } from '../rig/boneNames';
import type { BoneMapping, MappingReport } from '../retargeting/boneMap';
import { reportMapping } from '../retargeting/boneMap';
import { bindRetarget } from '../retargeting/retarget';
import type { RetargetBinding, TargetCharacter } from '../retargeting/retarget';
import { importCharacter, saveMapping } from '../retargeting/importGlb';

/**
 * The imported character lives outside the undo document: it holds three.js
 * objects, it is not part of the exercise, and reloading a model is not an edit
 * anybody wants to undo.
 */
interface CharacterState {
  name: string | null;
  character: TargetCharacter | null;
  mapping: BoneMapping | null;
  binding: RetargetBinding | null;
  report: MappingReport | null;
  status: { kind: 'idle' | 'loading' | 'error'; message?: string };

  load: (file: File) => Promise<void>;
  setBone: (canonical: BoneName, targetBone: string | null) => void;
  clear: () => void;
  persist: () => void;
}

export const useCharacter = create<CharacterState>((set, get) => ({
  name: null,
  character: null,
  mapping: null,
  binding: null,
  report: null,
  status: { kind: 'idle' },

  load: async (file) => {
    set({ status: { kind: 'loading', message: `Reading ${file.name}…` } });
    try {
      const imported = await importCharacter(file);
      set({
        name: imported.name,
        character: imported.character,
        mapping: imported.mapping,
        report: imported.report,
        binding: bindRetarget(imported.character, imported.mapping),
        status: { kind: 'idle' },
      });
    } catch (error) {
      set({ status: { kind: 'error', message: (error as Error).message } });
    }
  },

  setBone: (canonical, targetBone) => {
    const { mapping, character } = get();
    if (!mapping || !character) return;
    const bones = { ...mapping.bones };
    if (targetBone) bones[canonical] = targetBone;
    else delete bones[canonical];
    const next = { ...mapping, bones };
    set({
      mapping: next,
      report: reportMapping(next),
      binding: bindRetarget(character, next),
    });
  },

  clear: () =>
    set({ name: null, character: null, mapping: null, binding: null, report: null }),

  persist: () => {
    const mapping = get().mapping;
    if (mapping) saveMapping(mapping);
  },
}));
