import { extensionFamily } from '../families/extension';

/**
 * Cable triceps pushdown with a straight bar.
 *
 * The elbow-extension family at a cable tower: the upper arms pinned at the
 * sides, the forearms pushing a bar down from a high pulley to lockout in front
 * of the thighs. The first exercise with a cable, and the first with a bar held
 * in both hands.
 */
export const cablePushdown = extensionFamily({
  id: 'cable_triceps_pushdown',
  name: 'Cable Triceps Pushdown',
  clipName: 'cable_triceps_pushdown',
  position: 'pushdown',
  description:
    'Standing at a high pulley with an overhand grip on a straight bar. ' +
    'The elbows stay at the sides while the forearms push the bar down to ' +
    'lockout in front of the thighs and let it rise back to parallel.',
});
