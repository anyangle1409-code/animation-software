import { create } from 'zustand';
import type { BoneName } from '../rig/boneNames';
import type { BoneMapping, MappingReport } from '../retargeting/boneMap';
import { reportMapping } from '../retargeting/boneMap';
import { saveMapping } from '../retargeting/importGlb';
import {
  characterSource,
  defaultCharacterId,
  glbCharacterSource,
  registerCharacterSource,
  retargetedCharacterSource,
  unregisterCharacterSource,
} from '../character';
import type { CharacterBuild, ImportReport, RebindReport } from '../character';
import { canonicalSkeleton } from '../rig/skeleton';

/**
 * Which character is on screen, and how an imported one is attached.
 *
 * Two routes:
 *
 * - **Preserve** (default, and the production path) — the file keeps its own
 *   skeleton, bind pose and weights, and the canonical rig drives it. Nothing
 *   about the mesh changes.
 * - **Rebind** — the surface is rebuilt onto the canonical bones. Kept as a
 *   diagnostic: it is the only way to see a character on the studio's own
 *   proportions, and it distorts rest geometry badly on a dense rig, so it is
 *   not what a finished character uses.
 *
 * None of it lives in the undo document: it holds three.js objects, it is not
 * part of the exercise, and loading a model is not an edit anyone wants to
 * undo.
 */
export type BindMode = 'preserve' | 'rebind';

type Status = { kind: 'idle' | 'loading' | 'error'; message?: string };

const IMPORT_SOURCE_ID = 'import';

interface CharacterState {
  /** The active registered character source. */
  sourceId: string;
  sourceStatus: Status;
  /** How the last import was attached, and what each route reported. */
  bindMode: BindMode;
  rebind: RebindReport[] | null;
  imported: ImportReport | null;

  /** The character currently built and mounted, for the systems that follow it. */
  active: CharacterBuild | null;
  /** Viewport-only A/B switch; export remains production-correct. */
  correctivesPreview: boolean;
  /** Changes whenever production-visible character deformation identity changes. */
  deformationRevision: number;

  name: string | null;
  mapping: BoneMapping | null;
  report: MappingReport | null;
  status: Status;

  setSource: (id: string) => void;
  setSourceStatus: (status: Status) => void;
  setActive: (build: CharacterBuild | null) => void;
  setCorrectivesPreview: (enabled: boolean) => void;
  setDeformationControl: (id: string, value: number) => void;
  setBindMode: (mode: BindMode) => void;
  load: (file: File, mode?: BindMode) => Promise<void>;
  setBone: (canonical: BoneName, targetBone: string | null) => void;
  clear: () => void;
  persist: () => void;
}

/** The bytes of the last import, so a mapping edit can rebuild from them. */
let importedData: ArrayBuffer | null = null;
let importedLabel = '';

export const useCharacter = create<CharacterState>((set, get) => ({
  sourceId: defaultCharacterId(),
  sourceStatus: { kind: 'idle' },
  bindMode: 'preserve',
  rebind: null,
  imported: null,
  active: null,
  correctivesPreview: true,
  deformationRevision: 0,

  name: null,
  mapping: null,
  report: null,
  status: { kind: 'idle' },

  setSource: (sourceId) => {
    const state = get();
    if (state.sourceId === sourceId) return;
    set({ sourceId, deformationRevision: state.deformationRevision + 1 });
  },

  setSourceStatus: (sourceStatus) => set({ sourceStatus }),

  setActive: (active) => set({ active }),
  setCorrectivesPreview: (correctivesPreview) => set({ correctivesPreview }),
  setDeformationControl: (id, value) => {
    const state = get();
    const control = state.active?.deformation?.controls?.find((item) => item.id === id);
    if (!control) return;
    const before = control.value;
    control.set(value);
    if (Math.abs(control.value - before) <= 1e-9) return;
    set({ deformationRevision: state.deformationRevision + 1 });
  },

  setBindMode: (bindMode) => set({ bindMode }),

  load: async (file, mode) => {
    const bindMode = mode ?? get().bindMode;
    set({ status: { kind: 'loading', message: `Reading ${file.name}…` }, bindMode });

    try {
      importedLabel = file.name.replace(/\.(glb|gltf)$/i, '');
      importedData = await file.arrayBuffer();
      await registerImport(set, bindMode);
    } catch (error) {
      set({ status: { kind: 'error', message: (error as Error).message } });
    }
  },

  setBone: (canonical, targetBone) => {
    const { mapping, bindMode } = get();
    if (!mapping) return;
    const bones = { ...mapping.bones };
    if (targetBone) bones[canonical] = targetBone;
    else delete bones[canonical];
    const next = { ...mapping, bones };
    set({ mapping: next, report: reportMapping(next) });
    // Rebuild against the corrected mapping, so the viewport follows the edit.
    void registerImport(set, bindMode, next);
  },

  clear: () => {
    unregisterCharacterSource(IMPORT_SOURCE_ID);
    importedData = null;
    importedLabel = '';
    set({
      sourceId: defaultCharacterId(),
      deformationRevision: get().deformationRevision + 1,
      name: null,
      mapping: null,
      report: null,
      rebind: null,
      imported: null,
      status: { kind: 'idle' },
    });
  },

  persist: () => {
    const mapping = get().mapping;
    if (mapping) saveMapping(mapping);
  },
}));

/**
 * Register the imported file as a character source and select it.
 *
 * It is built once here rather than only in the viewport, so a file the studio
 * cannot use reports in the panel instead of as a blank viewport, and so the
 * mapping is ready to show and to correct.
 */
async function registerImport(
  set: (state: Partial<CharacterState>) => void,
  bindMode: BindMode,
  mapping?: BoneMapping,
): Promise<void> {
  if (!importedData) return;
  const shared = {
    id: IMPORT_SOURCE_ID,
    label: importedLabel,
    note: `Imported from ${importedLabel}`,
    data: importedData,
    mapping,
  };
  unregisterCharacterSource(IMPORT_SOURCE_ID);

  if (bindMode === 'rebind') {
    const source = registerCharacterSource(glbCharacterSource(shared));
    const probe = await source.build(canonicalSkeleton);
    probe.dispose();
    set({
      sourceId: source.id,
      deformationRevision: useCharacter.getState().deformationRevision + 1,
      name: importedLabel,
      mapping: mapping ?? null,
      report: source.lastReport?.mapping ?? null,
      rebind: source.lastReport?.rebind ?? null,
      imported: null,
      status: { kind: 'idle' },
    });
    return;
  }

  const source = registerCharacterSource(retargetedCharacterSource(shared));
  const probe = await source.build(canonicalSkeleton);
  probe.dispose();
  set({
    sourceId: source.id,
    name: importedLabel,
    mapping: mapping ?? null,
    report: source.lastReport?.mapping ?? null,
    rebind: null,
    imported: source.lastReport,
    status: { kind: 'idle' },
  });
}

/** What the active character can do — the anatomy view asks before offering itself. */
export const activeCapabilities = (sourceId: string) => characterSource(sourceId).capabilities;
