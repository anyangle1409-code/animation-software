import { create } from 'zustand';
import { characterSources } from '../character';
import { retargetedCharacterSource } from '../character/retargetSource';
import type { CharacterBuild } from '../character';
import { BASELINE_CHARACTER_URL, DRESSED_CHARACTER_URL } from '../character/bundled';
import { EXERCISE_BY_ID } from '../exercises/library';
import { generateExerciseAsync } from '../generation/generate';
import type { GenerationResult } from '../generation/generate';
import { canonicalSkeleton } from '../rig/skeleton';
import { useStudio } from './store';
import { browserReviewCaptureAvailable } from '../reference/browserCapture';
import { captureReferenceEvidence } from '../reference/reviewSession';
import { curlReferenceFor } from '../reference/specs/curl';
import type { ReviewEvidenceBatch } from '../reference/evidence';

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
  review?: {
    status: 'capturing' | 'ready' | 'error';
    batch?: ReviewEvidenceBatch;
    error?: string;
  };
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
 * The character the body checks measure: the bundled production body with its
 * shorts, built separately from the one on screen so measuring never disturbs
 * the viewport. Built once per session.
 */
let validation: Promise<{ build: CharacterBuild; label: string } | null> | null = null;

function validationCharacter(): Promise<{ build: CharacterBuild; label: string } | null> {
  validation ??= (async () => {
    const ids = new Set(characterSources().map((source) => source.id));
    const url = ids.has('baseline-dressed') ? DRESSED_CHARACTER_URL : ids.has('baseline') ? BASELINE_CHARACTER_URL : null;
    if (!url) return null;
    const label = url.replace(/^.*\//, '');
    try {
      const build = await retargetedCharacterSource({ id: 'generation-validation', label, url }).build(canonicalSkeleton);
      return { build, label };
    } catch {
      return null;
    }
  })();
  return validation;
}

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
    set({ running: true, progress: ['Preparing the validation character'] });
    const character = await validationCharacter();
    set({ validationCharacter: character?.label ?? null });
    const result = await generateExerciseAsync(
      prompt,
      { rig: canonicalSkeleton, character: character ?? undefined, library: (id) => EXERCISE_BY_ID.get(id) },
      (progress) => set({ progress: [...get().progress, progress.message] }),
    );
    counter += 1;
    const candidate: Candidate = { key: `candidate_${counter}`, prompt, result, approved: false };
    set({ running: false, candidates: [candidate, ...get().candidates], selected: candidate.key });
    // A blocked request has nothing to show; anything built is previewed at once.
    if (result.exercise) get().preview(candidate.key);

    // Curl is the first family with an independent local reference pack. If the
    // browser capture bridge is present, collect its deterministic review pack
    // automatically. This evidence never changes GenerationStatus or approval.
    if (
      result.exercise &&
      result.family?.id === 'curl' &&
      browserReviewCaptureAvailable()
    ) {
      const key = candidate.key;
      set({
        candidates: get().candidates.map((entry) =>
          entry.key === key ? { ...entry, review: { status: 'capturing' } } : entry,
        ),
      });
      try {
        // Preview loaded a fresh deterministic clip into the Studio. Capture the
        // exact clip the viewport is actually showing rather than a stale copy.
        const document = useStudio.getState().document;
        const batch = await captureReferenceEvidence(
          curlReferenceFor(document.exercise),
          document.exercise,
          document.clip,
        );
        set({
          candidates: get().candidates.map((entry) =>
            entry.key === key ? { ...entry, review: { status: 'ready', batch } } : entry,
          ),
        });
      } catch (error) {
        set({
          candidates: get().candidates.map((entry) =>
            entry.key === key
              ? {
                  ...entry,
                  review: {
                    status: 'error',
                    error: error instanceof Error ? error.message : String(error),
                  },
                }
              : entry,
          ),
        });
      }
    }
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
