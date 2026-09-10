import { Vector3 } from 'three';
import type { BufferGeometry } from 'three';
import { canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { ANATOMICAL_PALETTE } from './anatomicalPalette';
import { boneInfluence, smoothstep } from './skinning';

/**
 * The head.
 *
 * Three things about the source head read wrong at any distance, and all three
 * are shape rather than detail, so they are corrected here on the shared surface
 * where the studio, the anatomy view and the exported file all get them.
 *
 * **The skull is pinched above the ears.** Measured across, the head is 184 mm
 * at the ears and cheekbones and only 150 mm through the cranium above them. A
 * real skull is the other way round: widest at the parietal eminences, above and
 * behind the ear, and narrower through the face. Rendered, the source's ordering
 * reads as a cone — a tall narrow dome on a wide jaw, with hollow temples.
 *
 * **The eyes stand on the face rather than in it.** The eyeball sits proud of
 * the surrounding lids, so the sclera catches the light as a bright ring and the
 * figure stares.
 *
 * **There is no hair.** The source's hair is a set of helper strips the
 * generator deliberately drops — they are rig guides, not geometry — which
 * leaves a bald scalp.
 */

/** Cropped hair: a colour, and the small volume a short cut actually has. */
export const HAIR_LIFT = 0.004;

const SKULL = {
  /** The cranium, widened between these heights. */
  low: 1.6,
  high: 1.72,
  /** How much wider at its fullest. */
  widen: 0.06,
  /** The ear-and-cheek band, eased in by the same reasoning. */
  earLow: 1.54,
  earHigh: 1.6,
  narrow: 0.06,
  /**
   * Only the sides. Applying the widening across the whole head would spread
   * the nose and the mouth with it; fading it in from the midline moves the
   * temples and the parietals, which is where the shape is wrong.
   */
  midline: 0.022,
  flank: 0.05,
  /** The crown, brought down a little: the forehead runs tall in the source. */
  brow: 1.66,
  lower: 0.05,
};

const EYES = {
  /** How far the eyeball is set back into its socket, metres. */
  recess: 0.005,
  /** How much of the eye's own radius is taken off, to show less white. */
  shrink: 0.22,
};

const HAIR = {
  /** The hairline: high at the brow, lower round the back. */
  front: 1.674,
  back: 1.632,
  /** How far the cut stands off the scalp, and the band it fades over. */
  lift: HAIR_LIFT,
  fade: 0.022,
  /** The ears keep their own colour and shape. */
  ear: 0.072,
};

export interface HeadReport {
  /** Vertices whose position the skull correction moved. */
  shaped: number;
  /** The largest correction applied to the skull, metres. */
  maxDisplacement: number;
  /** Head width through the cranium before and after, metres. */
  craniumBefore: number;
  craniumAfter: number;
  /** Vertices painted as hair. */
  hair: number;
  /** Eye vertices recessed into their sockets. */
  eyes: number;
}

/** How wide the head is across a 20 mm band at one height. */
const widthAt = (
  position: { count: number; getX(i: number): number; getY(i: number): number },
  height: number,
): number => {
  let half = 0;
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    if (Math.abs(position.getY(vertex) - height) > 0.01) continue;
    const reach = Math.abs(position.getX(vertex));
    if (reach > 0.13) continue;
    half = Math.max(half, reach);
  }
  return half * 2;
};

/**
 * Round out the skull, set the eyes into their sockets and crop the hair.
 *
 * Runs inside `buildAnatomicalBodyGeometry`, on the decoded surface, before
 * anything reads it.
 */
export function shapeHead(
  geometry: BufferGeometry,
  rig: Skeleton = canonicalSkeleton,
): HeadReport {
  const position = geometry.getAttribute('position');
  const colour = geometry.getAttribute('color');
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const head = new Set<string>(['head']);

  const craniumBefore = widthAt(position, 1.66);

  /** Head-owned surface, and the eye parts inside it. */
  const onHead = new Float32Array(position.count);
  const sclera = paletteBytes(ANATOMICAL_PALETTE.sclera);
  const iris = paletteBytes(ANATOMICAL_PALETTE.iris);
  const pupil = paletteBytes(ANATOMICAL_PALETTE.pupil);
  const isEye = (vertex: number) =>
    matches(colour, vertex, sclera) || matches(colour, vertex, iris) || matches(colour, vertex, pupil);

  const eyeMiddle = new Vector3();
  let eyeCount = 0;
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    onHead[vertex] = boneInfluence(skinIndex, skinWeight, vertex, head, rig);
    if (onHead[vertex] < 0.5 || !isEye(vertex)) continue;
    // One side's worth: the eyes are mirrored, so the centre is taken on |x|.
    eyeMiddle.x += Math.abs(position.getX(vertex));
    eyeMiddle.y += position.getY(vertex);
    eyeMiddle.z += position.getZ(vertex);
    eyeCount += 1;
  }
  if (eyeCount > 0) eyeMiddle.multiplyScalar(1 / eyeCount);

  let shaped = 0;
  let maxDisplacement = 0;
  const point = new Vector3();

  for (let vertex = 0; vertex < position.count; vertex += 1) {
    if (onHead[vertex] < 0.5) continue;
    const x = position.getX(vertex);
    const y = position.getY(vertex);
    const reach = Math.abs(x);

    // Widen through the cranium, ease in through the ears and cheeks, and let
    // both fall to nothing at the midline so the face keeps its own width.
    const sides = smoothstep(SKULL.midline, SKULL.flank, reach);
    const parietal =
      smoothstep(SKULL.low, (SKULL.low + SKULL.high) / 2, y) *
      (1 - smoothstep((SKULL.low + SKULL.high) / 2, SKULL.high, y));
    const cheek =
      smoothstep(SKULL.earLow, (SKULL.earLow + SKULL.earHigh) / 2, y) *
      (1 - smoothstep((SKULL.earLow + SKULL.earHigh) / 2, SKULL.earHigh, y));
    const scale = 1 + sides * (SKULL.widen * parietal - SKULL.narrow * cheek);

    // And bring the crown down, which is where the source runs tall: the brow
    // to the crown is 110 mm against about 95 mm on a head this size.
    const dome = smoothstep(SKULL.brow, 1.74, y);
    const drop = SKULL.lower * dome * (y - SKULL.brow);

    if (Math.abs(scale - 1) < 1e-6 && Math.abs(drop) < 1e-9) continue;
    point.set(x * scale, y - drop, position.getZ(vertex));
    const moved = Math.hypot(point.x - x, point.y - y);
    position.setXYZ(vertex, point.x, point.y, point.z);
    if (moved > 1e-6) {
      shaped += 1;
      maxDisplacement = Math.max(maxDisplacement, moved);
    }
  }

  // The eyes, set back into their sockets and taken in a little. Both together
  // are what turns a stare into a look: less of the white shows, and what does
  // show is inside the lids rather than standing on them.
  let eyes = 0;
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    if (onHead[vertex] < 0.5 || !isEye(vertex)) continue;
    const side = Math.sign(position.getX(vertex)) || 1;
    point.set(
      side * eyeMiddle.x + (position.getX(vertex) - side * eyeMiddle.x) * (1 - EYES.shrink),
      eyeMiddle.y + (position.getY(vertex) - eyeMiddle.y) * (1 - EYES.shrink),
      eyeMiddle.z + (position.getZ(vertex) - eyeMiddle.z) * (1 - EYES.shrink) - EYES.recess,
    );
    position.setXYZ(vertex, point.x, point.y, point.z);
    eyes += 1;
  }

  // Cropped hair. The scalp is painted and lifted by four millimetres, which is
  // what a short cut stands off the skull; the hairline runs high at the brow
  // and lower round the back, and the ears are left out of it.
  const hairColour = paletteBytes(ANATOMICAL_PALETTE.hair);
  let hair = 0;
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    if (onHead[vertex] < 0.5 || isEye(vertex)) continue;
    const y = position.getY(vertex);
    const z = position.getZ(vertex);
    const reach = Math.abs(position.getX(vertex));
    const line = HAIR.back + (HAIR.front - HAIR.back) * smoothstep(-0.02, 0.06, z);
    const above = smoothstep(line, line + HAIR.fade, y);
    if (above <= 0) continue;
    // Not over the ears, which sit below the line anyway except at their tops.
    const ear = 1 - smoothstep(HAIR.ear, HAIR.ear + 0.012, reach) * (1 - smoothstep(1.62, 1.65, y));
    const amount = above * ear;
    if (amount <= 0.01) continue;

    // Graded rather than switched. The mesh's rows are a centimetre apart, so a
    // hard threshold on the same field cuts the hairline into a zigzag; blending
    // the colour across the band gives the soft edge a cropped cut has.
    const skinColour = paletteBytes(ANATOMICAL_PALETTE.skin);
    colour.setXYZ(
      vertex,
      (skinColour[0] + (hairColour[0] - skinColour[0]) * amount) / 255,
      (skinColour[1] + (hairColour[1] - skinColour[1]) * amount) / 255,
      (skinColour[2] + (hairColour[2] - skinColour[2]) * amount) / 255,
    );
    if (amount > 0.5) hair += 1;
    const out = new Vector3(position.getX(vertex), y - 1.63, z).normalize();
    position.setXYZ(
      vertex,
      position.getX(vertex) + out.x * HAIR.lift * amount,
      y + out.y * HAIR.lift * amount,
      z + out.z * HAIR.lift * amount,
    );
  }

  position.needsUpdate = true;
  colour.needsUpdate = true;
  return {
    shaped,
    maxDisplacement,
    craniumBefore,
    craniumAfter: widthAt(position, 1.66),
    hair,
    eyes,
  };
}

/** Vertex colours are stored pre-linearised, so a palette entry is matched in the same space. */
function paletteBytes(hex: string): [number, number, number] {
  const value = Number.parseInt(hex.slice(1), 16);
  return [16, 8, 0].map((shift) => {
    const channel = ((value >> shift) & 255) / 255;
    const linear = channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    return Math.round(linear * 255);
  }) as [number, number, number];
}

const matches = (
  colour: { getX(i: number): number; getY(i: number): number; getZ(i: number): number },
  vertex: number,
  bytes: [number, number, number],
): boolean =>
  Math.abs(Math.round(colour.getX(vertex) * 255) - bytes[0]) <= 1 &&
  Math.abs(Math.round(colour.getY(vertex) * 255) - bytes[1]) <= 1 &&
  Math.abs(Math.round(colour.getZ(vertex) * 255) - bytes[2]) <= 1;
