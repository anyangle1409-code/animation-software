import type { Tempo } from '../exercises/types';
import type { IntentGrip, IntentSupport, TempoProfile } from './intent';

/**
 * The words in a request that any family might care about, read once.
 *
 * Deterministic on purpose: the same sentence always produces the same slots,
 * which is what lets a generated exercise be regenerated, tested and reviewed.
 * Each slot keeps the words it was read from, so the review can show why the
 * parser decided what it did — and so a conflict ("hammer … palms up") can be
 * reported in the user's own words rather than as a code.
 */

export interface Slot<T> {
  value: T;
  /** The text it was read from. */
  words: string;
}

export type Equipment =
  | 'dumbbell'
  | 'barbell'
  | 'ez_bar'
  | 'cable'
  | 'kettlebell'
  | 'band'
  | 'machine'
  | 'bodyweight';

export interface PromptSlots {
  /** Lower case, whitespace collapsed. */
  text: string;
  grips: Slot<IntentGrip>[];
  supports: Slot<IntentSupport>[];
  angles: Slot<number>[];
  /** Kilograms per hand. */
  loads: Slot<number>[];
  tempo: Slot<{ profile: Exclude<TempoProfile, 'family'> } | { explicit: Tempo }>[];
  execution: Slot<'alternating' | 'single'>[];
  equipment: Slot<Equipment>[];
}

const GRIP_WORDS: [RegExp, IntentGrip][] = [
  [/\bneutral(?:[-\s]grip)?\b/g, 'neutral'],
  [/\bpalms?\s+(?:facing\s+)?(?:each other|in|inwards?)\b/g, 'neutral'],
  [/\bhammer[-\s]grip\b/g, 'neutral'],
  [/\bthumbs?[-\s]up\b/g, 'neutral'],
  [/\bsupinat(?:ed|ion)\b/g, 'supinated'],
  [/\bunderhand\b/g, 'supinated'],
  [/\bpalms?\s+(?:facing\s+)?up\b/g, 'supinated'],
  [/\bpronat(?:ed|ion)\b/g, 'pronated'],
  [/\boverhand\b/g, 'pronated'],
  [/\bpalms?\s+(?:facing\s+)?(?:down|forwards?)\b/g, 'pronated'],
];

const SUPPORT_WORDS: [RegExp, IntentSupport][] = [
  [/\bstanding\b/g, 'standing'],
  [/\b(?:seated|sitting|sat)\b/g, 'seated'],
  [/\binclined?\b/g, 'incline'],
  [/\b(?:dead[-\s]?hang|hanging)\b/g, 'hanging'],
];

const TEMPO_WORDS: [RegExp, Exclude<TempoProfile, 'family'>][] = [
  [/\bcontroll?ed\b|\bunder control\b/g, 'controlled'],
  [/\bslow(?:ly)?\b/g, 'slow'],
  [/\bfast\b|\bexplosive(?:ly)?\b|\bquick(?:ly)?\b/g, 'fast'],
];

const EQUIPMENT_WORDS: [RegExp, Equipment][] = [
  [/\bdumb-?bells?\b|\bdbs?\b/g, 'dumbbell'],
  [/\bez[-\s]?(?:curl[-\s]?)?bar\b/g, 'ez_bar'],
  [/\bbarbells?\b/g, 'barbell'],
  [/\bcables?\b|\bpulley\b/g, 'cable'],
  [/\bkettle-?bells?\b|\bkbs?\b/g, 'kettlebell'],
  [/\b(?:resistance\s+)?bands?\b/g, 'band'],
  [/\bmachines?\b/g, 'machine'],
  [/\bbody-?weight\b/g, 'bodyweight'],
];

function collect<T>(text: string, table: [RegExp, T][]): Slot<T>[] {
  const found: (Slot<T> & { at: number })[] = [];
  for (const [pattern, value] of table) {
    for (const match of text.matchAll(pattern)) found.push({ value, words: match[0], at: match.index ?? 0 });
  }
  return found.sort((a, b) => a.at - b.at).map(({ value, words }) => ({ value, words }));
}

const POUND = 0.45359237;

export function readSlots(prompt: string): PromptSlots {
  const text = prompt.toLowerCase().replace(/\s+/g, ' ').trim();

  const loads: Slot<number>[] = [];
  for (const match of text.matchAll(/(\d+(?:\.\d+)?)\s*(kgs?|kilo(?:gram)?s?|lbs?|pounds?)\b/g)) {
    const amount = Number(match[1]);
    const pounds = /^(?:lb|pound)/.test(match[2]);
    // Pounds are converted to the nearest half kilogram, the smallest step a
    // dumbbell rack is made in.
    loads.push({ value: pounds ? Math.round(amount * POUND * 2) / 2 : amount, words: match[0] });
  }

  const angles: Slot<number>[] = [];
  for (const match of text.matchAll(/(\d+(?:\.\d+)?)\s*(?:°|º|-?deg(?:ree)?s?\b)/g)) {
    angles.push({ value: Number(match[1]), words: match[0] });
  }

  const tempo: PromptSlots['tempo'] = [];
  // Standard tempo notation: lowering, pause at the bottom, lifting, pause at
  // the top, in seconds — "tempo 3-1-2-0".
  for (const match of text.matchAll(/\btempo\s*(\d(?:\.\d)?)[-–:/](\d(?:\.\d)?)[-–:/](\d(?:\.\d)?)[-–:/](\d(?:\.\d)?)/g)) {
    const [eccentric, pauseStretched, concentric, pauseContracted] = match.slice(1, 5).map(Number);
    tempo.push({ value: { explicit: { eccentric, pauseStretched, concentric, pauseContracted } }, words: match[0] });
  }
  if (tempo.length === 0) tempo.push(...collect(text, TEMPO_WORDS).map((slot) => ({ ...slot, value: { profile: slot.value } })));

  const execution: PromptSlots['execution'] = [];
  for (const match of text.matchAll(/\balternat(?:e|ing|ed)\b/g)) execution.push({ value: 'alternating', words: match[0] });
  for (const match of text.matchAll(/\b(?:single|one)[-\s]arm(?:ed)?\b|\bunilateral\b/g)) {
    execution.push({ value: 'single', words: match[0] });
  }

  return {
    text,
    grips: collect(text, GRIP_WORDS),
    supports: collect(text, SUPPORT_WORDS),
    angles,
    loads,
    tempo,
    execution,
    equipment: collect(text, EQUIPMENT_WORDS),
  };
}

/** The distinct values a slot list holds. */
export const distinct = <T>(slots: Slot<T>[]): T[] => [...new Set(slots.map((slot) => slot.value))];
