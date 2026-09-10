/**
 * The character's surface colours.
 *
 * Kept apart from the geometry builder so the passes that paint parts of the
 * body — the hair on the scalp, and the anatomy view's greyscale mapping — can
 * read them without importing the builder that calls those passes.
 */
export const ANATOMICAL_PALETTE = {
  skin: '#c8a184',
  hair: '#241c17',
  shorts: '#202226',
  sclera: '#f0e7dc',
  iris: '#5a4030',
  pupil: '#171413',
} as const;

export type AnatomicalPart = keyof typeof ANATOMICAL_PALETTE;
