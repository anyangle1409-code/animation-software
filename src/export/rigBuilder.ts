/**
 * Legacy test/diagnostic rig construction lives in body/skin. Full GLB export
 * no longer builds renderer equipment objects here; project-owned equipment is
 * written by the first-party GLB codec.
 */
export { buildSkinnedRig, MANNEQUIN_NAME } from '../body/skin';
export type { BuiltRig } from '../body/skin';
