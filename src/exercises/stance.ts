import { vec3 } from '../rig/types';
import type { EffectorLock, TechniqueRule } from '../constraints/types';
import type { EquipmentInstance } from '../equipment/types';
import type { FootSpec } from './types';
import { bilateralLock } from './mirror';
import { plantedContact } from './presets';

/**
 * How a standing exercise meets the floor, and what it holds.
 *
 * Extracted on the same evidence rule as `presets.ts`: only what two families
 * already say *identically*. Comparing the curl family against the shoulder
 * press, four things matched word for word — the planted-foot rule with its
 * 12 mm tolerance, the pair of floor locks, the foot spec, and the pair of
 * hand-held dumbbells. Everything else differs for a reason. The press holds
 * its torso to 8° where the curl allows 10°, and that is the difference between
 * a movement that must not lean back to cheat the weight overhead and one that
 * must not swing it up; flattening the two to save five lines would erase the
 * distinction rather than share it.
 *
 * The point is not the lines saved. It is that "standing on two planted feet"
 * is now one definition, so a future family cannot invent a third foot
 * tolerance, and the generator has one thing to reach for rather than a choice
 * between three spellings.
 */

/** The feet: their spec, their floor locks and the rule that holds them still. */
export interface PlantedStance {
  feet: FootSpec;
  locks: EffectorLock[];
  technique: TechniqueRule[];
}

/**
 * A shoulder-width stance with both feet locked to the floor.
 *
 * The 12 mm tolerance is what the curl, the press and the squat all settled on
 * independently — tight enough that a sliding foot fails, loose enough that the
 * solver's own sub-millimetre motion does not.
 */
export function plantedStance(): PlantedStance {
  return {
    feet: { width: 0.32, toeOut: 6, planted: true },
    locks: [...bilateralLock({ id: 'foot_l', chain: 'leg_l', mode: 'floor', enabled: true })],
    technique: [
      ...plantedContact({
        point: { bone: 'foot_l' },
        tolerance: 0.012,
        label: 'Left foot stays planted',
      }),
    ],
  };
}

/**
 * One dumbbell rigidly held in each hand.
 *
 * No grip rotation is calibrated here: the implement is rigid in the hand, so
 * whatever the forearm does carries it. That is what lets a hammer curl turn its
 * dumbbells by naming a grip rather than by placing them.
 */
export function handDumbbells(mass: number): EquipmentInstance[] {
  return (['l', 'r'] as const).map((side) => ({
    id: `dumbbell_${side}`,
    kind: 'dumbbell' as const,
    label: `${side === 'l' ? 'Left' : 'Right'} dumbbell`,
    mass,
    position: vec3(0, 0, 0),
    rotation: vec3(0, 0, 0),
    visible: true,
    attachment: { mode: 'hand' as const, side, socket: 'grip' },
  }));
}
