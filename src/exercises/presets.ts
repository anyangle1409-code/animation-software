import type { PointRef, Severity, TechniqueRule } from '../constraints/types';
import { bilateralRule, mirrorPoint } from './mirror';

/**
 * Rules that every exercise needs, written once.
 *
 * Only two are here, and that is deliberate. The library was surveyed for
 * repetition before anything was extracted, and exactly two patterns recur with
 * the same *meaning* rather than merely the same shape:
 *
 * - **a contact that must not move** — five uses, and every standing, seated or
 *   supported movement will need one;
 * - **the two sides staying level** — five uses, and every bilateral movement
 *   needs one.
 *
 * Three other candidates were rejected on the evidence:
 *
 * - **Tempo profiles.** All five exercises have a different tempo and no two
 *   share a single field. A named set of profiles would be invented here rather
 *   than extracted, and the first exercise that did not fit one would get a
 *   worse tempo to avoid adding another name.
 * - **A torso-angle preset.** Four rules measure a segment against vertical, but
 *   at 8, 10, 18 and 50 degrees under three different names. That is four
 *   intents that happen to share a shape — an upright press, a quiet curl, a
 *   hanging trunk, a squat's forward lean — and a preset would flatten the
 *   difference to save five lines each.
 * - **Grip presets.** `GRIP_PROFILES` already does this.
 *
 * The presets here fix ids rather than taking them, which is the other half of
 * their job: the same rule was already spelled `feet_planted_l` in the curl and
 * `foot_planted_l` in the squat and the press, and drift like that is what makes
 * a library stop being searchable. Labels stay authored, because they are what a
 * coach reads and a generated one would be worse than a written one.
 */

export interface PlantedContact {
  /** The point that must not move. Author the left; the right is derived. */
  point: PointRef;
  /** Maximum drift over the repetition, metres. */
  tolerance: number;
  /** Shown in the UI. The right-hand twin's label is derived from it. */
  label: string;
  /**
   * Defaults to `<bone>_planted_l` — `foot_l` gives `foot_planted_l`. Pass one
   * only when an exercise means something more specific by it.
   */
  id?: string;
  severity?: Severity;
}

/**
 * A foot on the floor, a hand on the mat, a grip on the bar: a point that has to
 * end the repetition where it started.
 *
 * This is the rule that catches a foot sliding, a hand walking forward under
 * load, or a limb the solver has quietly dragged off its contact — so it
 * defaults to `error` rather than a warning.
 */
export function plantedContact(contact: PlantedContact): [TechniqueRule, TechniqueRule] {
  const bone = contact.point.bone;
  const base = bone.endsWith('_l') || bone.endsWith('_r') ? bone.slice(0, -2) : bone;
  return bilateralRule({
    kind: 'stationary',
    id: contact.id ?? `${base}_planted_l`,
    label: contact.label,
    point: contact.point,
    tolerance: contact.tolerance,
    severity: contact.severity ?? 'error',
  });
}

export interface EvenSides {
  /** The left-hand point. The right is its mirror, so it cannot disagree. */
  point: PointRef;
  /** How far the two sides may differ once reflected, metres. */
  tolerance: number;
  id: string;
  label: string;
  severity?: Severity;
}

/**
 * The two sides stay level with one another.
 *
 * A single rule rather than a pair — the evaluator reflects the right-hand point
 * and compares — which is why it takes one point and derives the other instead
 * of going through `bilateralRule`. Authoring both halves by hand was the last
 * place in the definitions where a left and a right were written out separately
 * and could be made to name unrelated bones.
 *
 * The id stays explicit: `even_press`, `even_pull` and `dumbbells_aligned` are
 * what the exercise calls this, and deriving `forearm_even` from the bone would
 * lose that.
 */
export function evenSides(sides: EvenSides): TechniqueRule {
  return {
    kind: 'symmetry',
    id: sides.id,
    label: sides.label,
    left: sides.point,
    right: mirrorPoint(sides.point),
    tolerance: sides.tolerance,
    severity: sides.severity ?? 'error',
  };
}
