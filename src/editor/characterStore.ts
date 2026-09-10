import { create } from 'zustand';
import type { BoneName } from '../rig/boneNames';
import type { BoneMapping, MappingReport } from '../retargeting/boneMap';
import { reportMapping } from '../retargeting/boneMap';
import { bindRetarget } from '../retargeting/retarget';
import type { RetargetBinding, TargetCharacter } from '../retargeting/retarget';
import { importCharacter, saveMapping } from '../retargeting/importGlb';
import {
  characterSource,
  defaultCharacterId,
  glbCharacterSource,
  registerCharacterSource,
  unregisterCharacterSource,
} from '../character';
import type { RebindReport } from '../character';
import { canonicalSkeleton } from '../rig/skeleton';

/**
 * Which character is on screen, and how an imported one is attached.
 *
 * Two routes, both first class:
 *
 * - **Rebind** (default) — the file's surface is rebound by bone name onto the
 *   canonical rig and becomes an ordinary registered character. Equipment,
 *   grip and export all work on it exactly as on the built-in one.
 * - **Retarget** — the file keeps its own skeleton and the pose is transferred
 *   onto it each frame. The route to use for a character whose proportions
 *   must be preserved.
 *
 * None of it lives in the undo document: it holds three.js objects, it is not
 * part of the exercise, and loading a model is not an edit anyone wants to
 * undo.
 */
export type BindMode = 'rebind' | 'retarget';

type Status = { kind: 'idle' | 'loading' | 'error'; message?: string };

const IMPORT_SOURCE_ID = 'import';

interface CharacterState {
  /** The active registered character source. */
  sourceId: string;
  sourceStatus: Status;
  /** How the last import was attached, and what the rebind did. */
  bindMode: BindMode;
  rebind: RebindReport[] | null;

  /** Retargeting route: the character's own skeleton, driven per frame. */
  name: string | null;
  character: TargetCharacter | null;
  mapping: BoneMapping | null;
  binding: RetargetBinding | null;
  report: MappingReport | null;
  status: Status;

  setSource: (id: string) => void;
  setSourceStatus: (status: Status) => void;
  setBindMode: (mode: BindMode) => void;
  load: (file: File, mode?: BindMode) => Promise<void>;
  setBone: (canonical: BoneName, targetBone: string | null) => void;
  clear: () => void;
  persist: () => void;
}

export const useCharacter = create<CharacterState>((set, get) => ({
  sourceId: defaultCharacterId(),
  sourceStatus: { kind: 'idle' },
  bindMode: 'rebind',
  rebind: null,

  name: null,
  character: null,
  mapping: null,
  binding: null,
  report: null,
  status: { kind: 'idle' },

  setSource: (sourceId) => {
    // Choosing a registered character retires any retargeted import: only one
    // figure is ever on screen.
    set({ sourceId, binding: null, character: null, report: null, name: null });
  },

  setSourceStatus: (sourceStatus) => set({ sourceStatus }),

  setBindMode: (bindMode) => set({ bindMode }),

  load: async (file, mode) => {
    const bindMode = mode ?? get().bindMode;
    set({ status: { kind: 'loading', message: `Reading ${file.name}…` }, bindMode });

    try {
      if (bindMode === 'retarget') {
        const imported = await importCharacter(file);
        set({
          sourceId: defaultCharacterId(),
          name: imported.name,
          character: imported.character,
          mapping: imported.mapping,
          report: imported.report,
          binding: bindRetarget(imported.character, imported.mapping),
          rebind: null,
          status: { kind: 'idle' },
        });
        return;
      }

      const label = file.name.replace(/\.(glb|gltf)$/i, '');
      const data = await file.arrayBuffer();
      unregisterCharacterSource(IMPORT_SOURCE_ID);
      const source = registerCharacterSource(
        glbCharacterSource({ id: IMPORT_SOURCE_ID, label, note: `Imported from ${file.name}`, data }),
      );

      // Built once here so a bad file reports in the panel rather than as a
      // blank viewport, and so the mapping report is ready to show.
      const probe = await source.build(canonicalSkeleton);
      probe.dispose();

      set({
        sourceId: source.id,
        name: label,
        mapping: null,
        character: null,
        binding: null,
        report: source.lastReport?.mapping ?? null,
        rebind: source.lastReport?.rebind ?? null,
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

  clear: () => {
    unregisterCharacterSource(IMPORT_SOURCE_ID);
    set({
      sourceId: defaultCharacterId(),
      name: null,
      character: null,
      mapping: null,
      binding: null,
      report: null,
      rebind: null,
      status: { kind: 'idle' },
    });
  },

  persist: () => {
    const mapping = get().mapping;
    if (mapping) saveMapping(mapping);
  },
}));

/** What the active character can do — the anatomy view asks before offering itself. */
export const activeCapabilities = (sourceId: string) => characterSource(sourceId).capabilities;
