import { createStoreHook as create } from '../core/store';
import { EXERCISE_BY_ID } from '../exercises/library';
import { generateExerciseAsync } from '../generation/generate';
import type { GenerationResult } from '../generation/generate';
import { canonicalSkeleton } from '../rig/skeleton';
import { useStudio } from './store';

/**
 * Generated candidates for this session.
 *
 * A candidate lives here and nowhere else: it is never added to `EXERCISES`,
 * never written to disk, and gone when the page reloads. Approving one records
 * that a person has looked at it and is content; putting it in the library is
 * still a code change — the variant the panel shows, passed to its family
 * builder in a definition file — made deliberately and reviewed like any other.
 */

export interface Candidate {
  key: string;
  prompt: string;
  result: GenerationResult;
  approved: boolean;
}

interface GenerationState {
  prompt: string;
  running: boolean;
  progress: string[];
  candidates: Candidate[];
  selected: string | null;
  /** Which character the body checks measure, once known. */
  validationCharacter: string | null;

  setPrompt: (prompt: string) => void;
  generate: () => Promise<void>;
  preview: (key: string) => void;
  approve: (key: string) => void;
  discard: (key: string) => void;
}

/**
 * No production validation surface is mounted during the standalone migration.
 *
 * The old path silently loaded the legacy V8 GLBs from public/characters when
 * somebody dropped them into the working tree. That made generated-exercise
 * certification depend on a prohibited legacy asset. Until ORIGINAL v1 is
 * promoted, body-dependent checks stay explicitly unavailable and candidates
 * report unverified rather than borrowing a legacy character.
 */
let counter = 0;

export const useGeneration = create<GenerationState>((set, get) => ({
  prompt: 'Create a standing hammer curl with 12 kg dumbbells and controlled tempo.',
  running: false,
  progress: [],
  candidates: [],
  selected: null,
  validationCharacter: null,

  setPrompt: (prompt) => set({ prompt }),

  generate: async () => {
    const prompt = get().prompt.trim();
    if (!prompt || get().running) return;
    set({
      running: true,
      progress: ['Preparing standalone validation'],
      validationCharacter: null,
    });
    const result = await generateExerciseAsync(
      prompt,
      { rig: canonicalSkeleton, library: (id) => EXERCISE_BY_ID.get(id) },
      (progress) => set({ progress: [...get().progress, progress.message] }),
    );
    counter += 1;
    const candidate: Candidate = { key: `candidate_${counter}`, prompt, result, approved: false };
    set({ running: false, candidates: [candidate, ...get().candidates], selected: candidate.key });
    // A blocked request has nothing to show; anything built is previewed at once.
    if (result.exercise) get().preview(candidate.key);
  },

  preview: (key) => {
    const candidate = get().candidates.find((entry) => entry.key === key);
    if (!candidate?.result.exercise) return;
    set({ selected: key });
    useStudio.getState().loadDefinition(candidate.result.exercise);
  },

  approve: (key) =>
    set({
      candidates: get().candidates.map((entry) =>
        // Only a candidate every automatic check passed can be approved.
        entry.key === key && entry.result.status === 'passed' ? { ...entry, approved: true } : entry,
      ),
    }),

  discard: (key) =>
    set({
      candidates: get().candidates.filter((entry) => entry.key !== key),
      selected: get().selected === key ? null : get().selected,
    }),
}));
