import type { BoneName, Side } from '../rig/boneNames';
import { FINGERS } from '../rig/boneNames';

/**
 * The character's surface, as data.
 *
 * A chain is one continuous tube of cross-sections running along several bones:
 * the trunk from the crotch to the crown, an arm from the shoulder to the
 * fingertips. Each ring is an ellipse placed along its own bone — `t` runs from
 * that bone's joint (0) to its far end (1) — with a half-width across the bone
 * (`rx`), a half-depth front to back (`rz`) and, where a shape is not centred on
 * its bone, an offset (`ox`, `oz`).
 *
 * Building limbs as continuous tubes rather than one capsule per bone is what
 * removes the seams: there is no join to z-fight, and the rings either side of a
 * joint share their weight between the two bones, so an elbow creases instead of
 * two rigid parts scissoring through each other.
 *
 * Everything the viewport shows and everything the GLB exports is lofted from
 * this one list, so the mannequin in the studio and the mesh in the exported
 * file cannot drift apart.
 *
 * Numbers are metres on the canonical 1.75 m rig, and anthropometric rather than
 * decorative: 0.44 m across the shoulders, 0.34 m across the hips, a 0.24 m deep
 * chest, a wrist half the thickness of the forearm.
 */
export interface Ring {
  /** Position along the bone: 0 is its joint, 1 its far end. */
  t: number;
  /** Half-width across the bone's own x axis. */
  rx: number;
  /** Half-depth along the bone's own z axis (forward). */
  rz: number;
  /** Sideways offset of the ring's centre. */
  ox?: number;
  /** Forward offset of the ring's centre — a belly, a calf, a set of glutes. */
  oz?: number;
}

export interface BodyPart {
  bone: BoneName;
  /** Ordered along the chain; rings outside 0..1 are only legal at either end. */
  rings: Ring[];
  /**
   * Distance either side of this part's own joint over which its vertices hand
   * over to the bone before it. This is what makes a knee crease, and it is why
   * the exported mesh is no longer one bone per vertex.
   */
  blend?: number;
}

export interface BodyChain {
  id: string;
  parts: BodyPart[];
  /** Vertices around each ring; fingers need far fewer than a torso. */
  sides?: number;
  /** Round the ends off, as a fraction of the end ring's radius. */
  domeStart?: number;
  domeEnd?: number;
}

/** A small rigid lump — a nose, an ear, a thumb pad — riding one bone. */
export interface BodyBlob {
  bone: BoneName;
  /** Centre in the bone's own frame. */
  centre: [number, number, number];
  /** Radii along the bone's x, y and z. */
  radii: [number, number, number];
}

const ring = (t: number, rx: number, rz: number, oz = 0, ox = 0): Ring => ({ t, rx, rz, oz, ox });

// ---------------------------------------------------------------------------
// Trunk: crotch to crown, six bones, one tube
// ---------------------------------------------------------------------------

const TRUNK: BodyChain = {
  id: 'trunk',
  sides: 20,
  domeStart: 0.28,
  domeEnd: 0.6,
  parts: [
    {
      // The pelvis bone is 8 cm long but the body around it is a quarter of a
      // metre, so its rings reach well below their own joint.
      bone: 'pelvis',
      rings: [
        ring(-1.15, 0.121, 0.09, -0.008),
        ring(-0.95, 0.148, 0.102, -0.016),
        ring(-0.6, 0.167, 0.111, -0.016),
        ring(-0.1, 0.166, 0.108, -0.006),
        ring(0.45, 0.157, 0.102, 0),
        ring(0.95, 0.15, 0.1, 0.003),
      ],
    },
    {
      bone: 'spine_01',
      blend: 0.06,
      rings: [ring(0.1, 0.147, 0.1, 0.004), ring(0.45, 0.141, 0.099, 0.006), ring(0.8, 0.139, 0.1, 0.006)],
    },
    {
      bone: 'spine_02',
      blend: 0.06,
      rings: [ring(0.05, 0.142, 0.103, 0.005), ring(0.45, 0.153, 0.111, 0.002), ring(0.85, 0.166, 0.117, 0)],
    },
    {
      bone: 'spine_03',
      blend: 0.06,
      rings: [
        ring(0.05, 0.171, 0.119, -0.002),
        ring(0.35, 0.181, 0.121, -0.004),
        ring(0.62, 0.183, 0.114, -0.009),
        ring(0.88, 0.169, 0.098, -0.015),
      ],
    },
    {
      bone: 'neck',
      blend: 0.05,
      rings: [
        ring(0.02, 0.107, 0.088, -0.016),
        ring(0.3, 0.068, 0.066, -0.008),
        ring(0.62, 0.059, 0.06, -0.005),
        ring(0.9, 0.057, 0.059, -0.003),
      ],
    },
    {
      // Skull: cranium, brow, cheekbones, and a jaw tapering to the chin. The
      // face sits forward of the bone, because the bone runs up the middle of
      // the head and a face does not.
      bone: 'head',
      blend: 0.035,
      rings: [
        ring(0.02, 0.064, 0.07, 0.006),
        ring(0.12, 0.073, 0.086, 0.018),
        ring(0.26, 0.079, 0.096, 0.021),
        ring(0.42, 0.083, 0.102, 0.016),
        ring(0.56, 0.084, 0.103, 0.009),
        ring(0.68, 0.081, 0.099, 0.002),
        ring(0.78, 0.073, 0.09, -0.005),
      ],
    },
  ],
};

// ---------------------------------------------------------------------------
// Arms
// ---------------------------------------------------------------------------

/** Collarbone and the top of the trapezius, tucked inside the chest and deltoid. */
const clavicle = (side: Side): BodyChain => ({
  id: `clavicle_${side}`,
  sides: 10,
  parts: [
    {
      bone: `clavicle_${side}` as BoneName,
      blend: 0.03,
      rings: [ring(0.15, 0.03, 0.046, -0.012), ring(0.6, 0.028, 0.042, -0.007), ring(0.92, 0.032, 0.046, -0.002)],
    },
  ],
});

/** Shoulder to fingertips: deltoid cap, biceps belly, forearm flare, palm. */
const arm = (side: Side): BodyChain => ({
  id: `arm_${side}`,
  sides: 14,
  domeStart: 0.4,
  domeEnd: 0.45,
  parts: [
    {
      bone: `upperarm_${side}` as BoneName,
      blend: 0.05,
      rings: [
        ring(-0.06, 0.051, 0.05, -0.002),
        ring(0.02, 0.055, 0.054, 0.002),
        ring(0.15, 0.054, 0.053, 0.004),
        ring(0.4, 0.049, 0.051, 0.005),
        ring(0.68, 0.043, 0.046, 0.003),
        ring(0.92, 0.038, 0.04, 0),
      ],
    },
    {
      bone: `forearm_${side}` as BoneName,
      blend: 0.05,
      rings: [
        ring(0.06, 0.038, 0.041, 0.001),
        ring(0.22, 0.044, 0.045, 0.002),
        ring(0.5, 0.037, 0.038, 0.001),
        ring(0.75, 0.03, 0.03, 0),
        ring(0.95, 0.026, 0.025, 0),
      ],
    },
    {
      // The palm is thin across the back of the hand and wide from thumb to
      // little finger, which in this rig's frame is a small rx and a large rz.
      bone: `hand_${side}` as BoneName,
      blend: 0.025,
      rings: [
        ring(0.08, 0.022, 0.031, 0.003),
        ring(0.4, 0.021, 0.038, 0.004),
        ring(0.78, 0.019, 0.039, 0.004),
        ring(1.0, 0.017, 0.035, 0.002),
      ],
    },
  ],
});

// ---------------------------------------------------------------------------
// Legs
// ---------------------------------------------------------------------------

/** Hip to ankle: glute and quadriceps sweep, knee, calf, then a narrow ankle. */
const leg = (side: Side): BodyChain => ({
  id: `leg_${side}`,
  sides: 16,
  domeStart: 0.5,
  domeEnd: 0.4,
  parts: [
    {
      bone: `thigh_${side}` as BoneName,
      blend: 0.07,
      rings: [
        ring(-0.08, 0.086, 0.097, -0.012),
        ring(0.08, 0.089, 0.098, -0.008),
        ring(0.35, 0.081, 0.088, -0.002),
        ring(0.62, 0.07, 0.076, 0.001),
        ring(0.87, 0.059, 0.061, 0.002),
      ],
    },
    {
      bone: `shin_${side}` as BoneName,
      blend: 0.06,
      rings: [
        ring(0.06, 0.053, 0.058, -0.002),
        ring(0.17, 0.056, 0.063, -0.014),
        ring(0.36, 0.052, 0.06, -0.016),
        ring(0.6, 0.044, 0.047, -0.01),
        ring(0.84, 0.035, 0.035, -0.002),
        ring(0.99, 0.032, 0.031, 0.002),
      ],
    },
  ],
});

/**
 * The foot runs from the ankle down to the ball, so its rings tilt with the
 * bone. `oz` lifts each ring's centre until the sole sits flat on the floor — a
 * foot whose underside is a cylinder reads as a hoof.
 */
const foot = (side: Side): BodyChain => ({
  id: `foot_${side}`,
  sides: 12,
  domeStart: 0.75,
  domeEnd: 0.9,
  parts: [
    {
      bone: `foot_${side}` as BoneName,
      blend: 0.035,
      rings: [
        ring(-0.4, 0.033, 0.035, 0.029),
        ring(-0.18, 0.038, 0.044, 0.022),
        ring(0.12, 0.04, 0.049, 0.013),
        ring(0.5, 0.042, 0.044, 0.008),
        ring(0.85, 0.044, 0.038, 0.005),
      ],
    },
    {
      bone: `toe_${side}` as BoneName,
      blend: 0.022,
      rings: [ring(0.05, 0.043, 0.033, 0.007), ring(0.55, 0.041, 0.029, 0.006), ring(0.95, 0.033, 0.023, 0.005)],
    },
  ],
});

// ---------------------------------------------------------------------------
// Fingers
// ---------------------------------------------------------------------------

const FINGER_RADIUS: Record<string, [number, number, number]> = {
  thumb: [0.0125, 0.011, 0.0092],
  index: [0.0102, 0.0092, 0.008],
  middle: [0.0105, 0.0095, 0.0082],
  ring: [0.0099, 0.009, 0.0077],
  pinky: [0.009, 0.008, 0.0069],
};

const fingerChains = (side: Side): BodyChain[] =>
  FINGERS.map((finger) => {
    const radii = FINGER_RADIUS[finger];
    return {
      id: `${finger}_${side}`,
      sides: 7,
      domeStart: 0.5,
      domeEnd: 0.95,
      parts: radii.map((radius, index) => ({
        bone: `${finger}_0${index + 1}_${side}` as BoneName,
        blend: 0.009,
        rings: [ring(0.04, radius, radius * 0.95), ring(0.55, radius * 0.97, radius * 0.92), ring(0.96, radius * 0.9, radius * 0.86)],
      })),
    };
  });

// ---------------------------------------------------------------------------
// The whole body
// ---------------------------------------------------------------------------

const perSide = (side: Side): BodyChain[] => [
  clavicle(side),
  arm(side),
  leg(side),
  foot(side),
  ...fingerChains(side),
];

export const BODY_CHAINS: BodyChain[] = [TRUNK, ...perSide('l'), ...perSide('r')];

/**
 * Features too small to be worth a chain of their own. A nose and a pair of ears
 * are the difference between a head and an egg.
 *
 * Each one is a closed ellipsoid that intersects the surface it sits on, so how
 * deep it sits is what decides whether it reads as anatomy. Buried to its own
 * radius it lies almost tangent to the skin and the two surfaces fight for the
 * same pixels; sitting on the surface it reads as a ball stuck on. Half a radius
 * in crosses the skin at about 60° and looks like one form. The skull's face
 * front stands about 0.118 m ahead of the head bone.
 */
export const BODY_BLOBS: BodyBlob[] = [
  // Nose: one ridge down the middle of the face.
  { bone: 'head', centre: [0, 0.088, 0.11], radii: [0.0095, 0.032, 0.014] },
  // Chin and jaw.
  { bone: 'head', centre: [0, 0.024, 0.086], radii: [0.031, 0.019, 0.016] },
  // Ears.
  { bone: 'head', centre: [-0.077, 0.078, -0.004], radii: [0.009, 0.023, 0.014] },
  { bone: 'head', centre: [0.077, 0.078, -0.004], radii: [0.009, 0.023, 0.014] },
  // The pad at the base of each thumb.
  { bone: 'hand_l', centre: [0, 0.03, 0.03], radii: [0.017, 0.028, 0.014] },
  { bone: 'hand_r', centre: [0, 0.03, 0.03], radii: [0.017, 0.028, 0.014] },
];
