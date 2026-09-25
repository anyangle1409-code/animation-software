import type { Tempo } from '../exercises/types';

/**
 * What a user asked for, in the terms a movement family understands.
 *
 * An `ExerciseIntent` is the bridge between a sentence and a family builder.
 * It names only choices a family can act on — the grip, the support, the load,
 * the tempo — and never joint angles: the family owns the biomechanics, and an
 * intent that could carry angles would let a prompt invent motion the family
 * has not been validated for (the plan's "do not allow unsupported
 * biomechanics to be invented silently").
 */

/** The families the generator is certified to build from. */
export type GeneratorFamilyId = 'curl' | 'overhead_press' | 'squat' | 'lunge' | 'hinge' | 'row' | 'vertical_pull' | 'raise' | 'extension';

/** What the body moves against. Bodyweight families hold no equipment yet. */
export type IntentImplement = 'dumbbell' | 'bodyweight';

export type IntentGrip = 'supinated' | 'neutral' | 'pronated';
export type IntentSupport = 'standing' | 'seated' | 'incline' | 'hanging';

/**
 * Which foot steps, for the lunge family's three variants. Undefined is the
 * split squat: both feet stay put and the body sinks between them.
 */
export type IntentStep = 'forward' | 'back';

/**
 * Named tempo prescriptions. `controlled` is the common coaching meaning — a
 * deliberate lift and a slower, three-second lowering — rather than a guess at
 * what one family prefers; `family` leaves the family's own tempo alone.
 */
export type TempoProfile = 'family' | 'controlled' | 'slow' | 'fast';

export const TEMPO_PROFILES: Record<Exclude<TempoProfile, 'family'>, Tempo> = {
  controlled: { concentric: 2, pauseContracted: 1, eccentric: 3, pauseStretched: 0.5 },
  slow: { concentric: 3, pauseContracted: 1, eccentric: 4, pauseStretched: 1 },
  fast: { concentric: 1, pauseContracted: 0.3, eccentric: 1.5, pauseStretched: 0.3 },
};

export interface ExerciseIntent {
  /** The sentence it came from. */
  prompt: string;
  family: GeneratorFamilyId;
  /** Hand-held dumbbells, or a bodyweight lower-body family that holds no equipment yet. */
  equipment: IntentImplement;
  /** Both sides together. Alternating and single-limb work are not certified yet. */
  execution: 'bilateral';
  /** Only the dumbbell families read this. */
  grip?: IntentGrip;
  support: IntentSupport;
  /** Bench back angle from the floor, degrees, when the support is an incline. */
  benchAngle?: number;
  /** Only the lunge family reads this. */
  step?: IntentStep;
  /** Load per hand, kilograms. Always 0 for a bodyweight family. */
  load: number;
  tempo: { profile: TempoProfile } | { explicit: Tempo };
}

/**
 * Something the parser could not settle on its own.
 *
 * `blocking` issues stop generation: the request asks for something no
 * certified family can do (an alternating curl, a 30° incline on a 45° bench),
 * or it is ambiguous in a way that changes the exercise (a "hammer" curl with
 * palms up). Everything else is written down as an assumption and generation
 * goes ahead.
 */
export interface IntentIssue {
  code: string;
  message: string;
  blocking: boolean;
}

export interface ParsedPrompt {
  prompt: string;
  intent: ExerciseIntent | null;
  /** Defaults the parser chose, in words, so the review can see them. */
  assumptions: string[];
  issues: IntentIssue[];
}

export const tempoOf = (intent: ExerciseIntent): Tempo | undefined =>
  'explicit' in intent.tempo
    ? intent.tempo.explicit
    : intent.tempo.profile === 'family'
      ? undefined
      : TEMPO_PROFILES[intent.tempo.profile];
