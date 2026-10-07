import { create } from 'zustand';
import { ZERO_CORRECTION, parseCorrections, serializeCorrections } from '../character/alignment';
import type { BoneCorrection, BoneCorrections } from '../character/alignment';

/**
 * Bone-alignment corrections the reviewer makes on the active character.
 *
 * Kept per character and saved on this device only (browser storage), because
 * they are a review tool rather than part of the exercise document: the way to
 * make them permanent is to copy them out and bake them into the model file.
 */
interface AlignmentState {
  sourceId: string | null;
  corrections: BoneCorrections;
  selected: string | null;
  showCharacterBones: boolean;
  load: (sourceId: string) => void;
  select: (bone: string | null) => void;
  setValue: (bone: string, key: keyof BoneCorrection, value: number) => void;
  resetBone: (bone: string) => void;
  resetAll: () => void;
  toggleCharacterBones: () => void;
  exportText: () => string;
  importText: (text: string) => string | null;
}

const storageKey = (sourceId: string) => `hgpt-bone-alignment:${sourceId}`;

function read(sourceId: string): BoneCorrections {
  try {
    const text = window.localStorage.getItem(storageKey(sourceId));
    return text ? parseCorrections(text) : {};
  } catch {
    return {};
  }
}

function write(sourceId: string | null, corrections: BoneCorrections): void {
  if (!sourceId) return;
  try {
    window.localStorage.setItem(storageKey(sourceId), serializeCorrections(corrections));
  } catch {
    // Storage can be unavailable (private window, blocked site data); the
    // corrections still work for this session.
  }
}

export const useAlignment = create<AlignmentState>((set, get) => ({
  sourceId: null,
  corrections: {},
  selected: null,
  showCharacterBones: false,

  load: (sourceId) => {
    if (get().sourceId === sourceId) return;
    set({ sourceId, corrections: read(sourceId), selected: null });
  },
  select: (selected) => set({ selected }),
  setValue: (bone, key, value) => {
    const corrections = { ...get().corrections, [bone]: { ...(get().corrections[bone] ?? ZERO_CORRECTION), [key]: value } };
    set({ corrections });
    write(get().sourceId, corrections);
  },
  resetBone: (bone) => {
    const corrections = { ...get().corrections };
    delete corrections[bone];
    set({ corrections });
    write(get().sourceId, corrections);
  },
  resetAll: () => {
    set({ corrections: {} });
    write(get().sourceId, {});
  },
  toggleCharacterBones: () => set({ showCharacterBones: !get().showCharacterBones }),
  exportText: () => serializeCorrections(get().corrections),
  importText: (text) => {
    try {
      const corrections = parseCorrections(text);
      set({ corrections });
      write(get().sourceId, corrections);
      return null;
    } catch (error) {
      return (error as Error).message;
    }
  },
}));
