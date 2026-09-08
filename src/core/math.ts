/** Small numeric helpers shared across the studio. */

export const DEG = Math.PI / 180;
export const RAD = 180 / Math.PI;

export const toRad = (degrees: number): number => degrees * DEG;
export const toDeg = (radians: number): number => radians * RAD;

export const clamp = (value: number, min: number, max: number): number =>
  value < min ? min : value > max ? max : value;

export const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;

/** Shortest-path interpolation between two angles in radians. */
export function lerpAngle(a: number, b: number, t: number): number {
  let delta = (b - a) % (Math.PI * 2);
  if (delta > Math.PI) delta -= Math.PI * 2;
  if (delta < -Math.PI) delta += Math.PI * 2;
  return a + delta * t;
}

export const approx = (a: number, b: number, epsilon = 1e-6): boolean =>
  Math.abs(a - b) <= epsilon;

/** Round to a fixed number of decimals — keeps exported JSON readable. */
export const round = (value: number, decimals = 4): number => {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
};
