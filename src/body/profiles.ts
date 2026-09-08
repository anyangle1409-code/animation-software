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
 * this one list, so the character in the studio and the mesh in the exported
 * file cannot drift apart.
 *
 * The figure is an athletic adult male on the canonical 1.75 m rig, and the
 * numbers are anthropometric rather than decorative: 0.46 m across the
 * shoulders, 0.36 m across the chest, a 0.28 m waist, 0.34 m hips, a 0.32 m
 * upper-arm girth. Trained, not inflated.
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
  /** Surface colour from this ring on, for clothing. Defaults to skin. */
  colour?: string;
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

/** A small rigid lump — a nose, an ear, an eyeball — riding one bone. */
export interface BodyBlob {
  bone: BoneName;
  /** Centre in the bone's own frame. */
  centre: [number, number, number];
  /** Radii along the bone's x, y and z. */
  radii: [number, number, number];
  colour?: string;
  /** Rings around the blob; small features need fewer. */
  detail?: number;
}

/**
 * The character's palette. Skin is a warm mid tone so the red muscle
 * highlighting reads against it; clothing remains dark and unobtrusive.
 */
export const BODY_COLOURS = {
  skin: '#c8a184',
  shorts: '#24272e',
  waistband: '#31353e',
  sclera: '#ded4c8',
  iris: '#2f3a46',
  lips: '#a9705f',
  brow: '#7a5b47',
  hair: '#3b3029',
} as const;

const ring = (t: number, rx: number, rz: number, oz = 0, ox = 0, colour?: string): Ring => ({
  t,
  rx,
  rz,
  oz,
  ox,
  ...(colour ? { colour } : {}),
});

const clothed = (t: number, rx: number, rz: number, oz = 0, ox = 0): Ring =>
  ring(t, rx, rz, oz, ox, BODY_COLOURS.shorts);

// ---------------------------------------------------------------------------
// Trunk: crotch to crown, six bones, one tube
// ---------------------------------------------------------------------------

const TRUNK: BodyChain = {
  id: 'trunk',
  sides: 22,
  domeStart: 0.28,
  domeEnd: 0.6,
  parts: [
    {
      // The pelvis bone is 8 cm long but the body around it is a quarter of a
      // metre, so its rings reach well below their own joint. All of it is
      // inside the shorts, whose waistband sits on the hip at the top ring.
      bone: 'pelvis',
      rings: [
        clothed(-1.15, 0.124, 0.093, -0.008),
        clothed(-0.95, 0.151, 0.105, -0.017),
        clothed(-0.6, 0.17, 0.114, -0.018),
        clothed(-0.1, 0.168, 0.111, -0.007),
        clothed(0.45, 0.157, 0.104, 0),
        // Waistband: a hair wider than the skin under it, like fabric.
        ring(0.88, 0.152, 0.102, 0.003, 0, BODY_COLOURS.waistband),
        ring(1.0, 0.145, 0.098, 0.004),
      ],
    },
    {
      // Waist. Narrower than both the ribcage above and the hips below, which
      // is the whole of the V-taper.
      bone: 'spine_01',
      blend: 0.06,
      rings: [
        ring(0.15, 0.139, 0.097, 0.005),
        ring(0.5, 0.135, 0.095, 0.007),
        ring(0.85, 0.137, 0.098, 0.007),
      ],
    },
    {
      // Lower ribcage flaring into the lats.
      bone: 'spine_02',
      blend: 0.06,
      rings: [
        ring(0.08, 0.142, 0.102, 0.006),
        ring(0.45, 0.158, 0.112, 0.003),
        ring(0.85, 0.176, 0.119, 0),
      ],
    },
    {
      // Chest and shoulder shelf. The pectoral mass sits forward of the bone,
      // which is why the ring centres move with it.
      bone: 'spine_03',
      blend: 0.06,
      rings: [
        ring(0.05, 0.182, 0.118, -0.002),
        // Under-pec ledge, then the pectoral mass above it: a male chest is a
        // full ribcage with a shelf, not a pair of mounds.
        ring(0.24, 0.191, 0.121, 0),
        ring(0.42, 0.194, 0.124, 0.002),
        ring(0.62, 0.193, 0.12, -0.004),
        ring(0.82, 0.183, 0.105, -0.014),
        ring(0.96, 0.163, 0.093, -0.018),
      ],
    },
    {
      // Neck: thick at the base where the trapezius carries it, then a column.
      bone: 'neck',
      blend: 0.05,
      rings: [
        ring(0.02, 0.104, 0.089, -0.017),
        ring(0.3, 0.072, 0.07, -0.009),
        ring(0.62, 0.063, 0.064, -0.005),
        ring(0.9, 0.061, 0.063, -0.003),
      ],
    },
    {
      // Skull: cranium, brow, cheekbones, and a jaw with corners. The face sits
      // forward of the bone, because the bone runs up the middle of the head
      // and a face does not.
      bone: 'head',
      blend: 0.035,
      rings: [
        ring(0.02, 0.066, 0.073, 0.008),
        ring(0.1, 0.076, 0.088, 0.019),
        ring(0.2, 0.082, 0.097, 0.023),
        ring(0.32, 0.084, 0.101, 0.021),
        ring(0.46, 0.084, 0.103, 0.016),
        ring(0.6, 0.083, 0.103, 0.009),
        ring(0.72, 0.079, 0.098, 0.001),
        ring(0.82, 0.07, 0.088, -0.007),
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
      rings: [
        ring(0.15, 0.032, 0.048, -0.012),
        ring(0.6, 0.03, 0.044, -0.007),
        ring(0.92, 0.034, 0.048, -0.002),
      ],
    },
  ],
});

/**
 * Shoulder to fingertips.
 *
 * The shapes a coach looks at are all here: the deltoid cap over the joint, the
 * biceps belly forward of the bone and the triceps behind it, a narrow elbow
 * with the forearm flaring immediately below it, and a wrist half the thickness
 * of the forearm above it.
 */
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
        ring(-0.06, 0.055, 0.054, -0.002),
        ring(0.02, 0.061, 0.059, 0.002),
        ring(0.16, 0.06, 0.06, 0.006),
        ring(0.34, 0.057, 0.059, 0.007),
        ring(0.55, 0.05, 0.053, 0.004),
        ring(0.78, 0.043, 0.046, 0.001),
        // The elbow itself: narrow across, a little deeper for the olecranon.
        ring(0.95, 0.037, 0.041, -0.003),
      ],
    },
    {
      bone: `forearm_${side}` as BoneName,
      blend: 0.05,
      rings: [
        ring(0.05, 0.04, 0.044, 0.001),
        ring(0.2, 0.049, 0.05, 0.003),
        ring(0.42, 0.043, 0.044, 0.002),
        ring(0.66, 0.033, 0.033, 0.001),
        ring(0.88, 0.028, 0.027, 0),
        // Wrist.
        ring(0.98, 0.026, 0.024, 0),
      ],
    },
    {
      // The palm is thin across the back of the hand and wide from thumb to
      // little finger, which in this rig's frame is a small rx and a large rz.
      bone: `hand_${side}` as BoneName,
      blend: 0.025,
      rings: [
        ring(0.08, 0.023, 0.032, 0.003),
        ring(0.4, 0.022, 0.039, 0.004),
        ring(0.78, 0.02, 0.04, 0.004),
        ring(1.0, 0.018, 0.036, 0.002),
      ],
    },
  ],
});

// ---------------------------------------------------------------------------
// Legs
// ---------------------------------------------------------------------------

/**
 * Hip to ankle. The shorts end at mid-thigh, on their own pair of rings so the
 * hem is a clean line rather than a gradient, and the quadriceps sweep, knee and
 * calf are all below it where they can be seen.
 */
const leg = (side: Side): BodyChain => ({
  id: `leg_${side}`,
  sides: 16,
  domeEnd: 0.4,
  parts: [
    {
      bone: `thigh_${side}` as BoneName,
      blend: 0.07,
      rings: [
        clothed(-0.04, 0.083, 0.094, -0.012),
        clothed(0.08, 0.092, 0.101, -0.008),
        clothed(0.26, 0.086, 0.094, -0.004),
        // Hem, then the leg itself a few millimetres narrower.
        clothed(0.4, 0.081, 0.088, -0.001),
        ring(0.43, 0.08, 0.087, -0.001),
        ring(0.62, 0.074, 0.08, 0.001),
        // Knee: the patella stands forward of the joint.
        ring(0.86, 0.061, 0.062, 0.004),
        ring(0.98, 0.057, 0.06, 0.005),
      ],
    },
    {
      bone: `shin_${side}` as BoneName,
      blend: 0.06,
      rings: [
        ring(0.05, 0.055, 0.061, 0),
        ring(0.16, 0.061, 0.069, -0.015),
        ring(0.35, 0.057, 0.064, -0.018),
        ring(0.58, 0.046, 0.049, -0.011),
        ring(0.82, 0.036, 0.036, -0.002),
        ring(0.99, 0.033, 0.032, 0.002),
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
        ring(-0.4, 0.034, 0.036, 0.029),
        ring(-0.18, 0.039, 0.045, 0.022),
        ring(0.12, 0.041, 0.05, 0.013),
        ring(0.5, 0.043, 0.045, 0.008),
        ring(0.85, 0.045, 0.039, 0.005),
      ],
    },
    {
      bone: `toe_${side}` as BoneName,
      blend: 0.022,
      rings: [
        ring(0.05, 0.044, 0.034, 0.007),
        ring(0.55, 0.042, 0.03, 0.006),
        ring(0.95, 0.034, 0.024, 0.005),
      ],
    },
  ],
});

// ---------------------------------------------------------------------------
// Fingers
// ---------------------------------------------------------------------------

const FINGER_RADIUS: Record<string, [number, number, number]> = {
  thumb: [0.0128, 0.0113, 0.0095],
  index: [0.0105, 0.0095, 0.0082],
  middle: [0.0108, 0.0098, 0.0085],
  ring: [0.0102, 0.0093, 0.008],
  pinky: [0.0093, 0.0083, 0.0072],
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
        rings: [
          ring(0.04, radius, radius * 0.95),
          ring(0.55, radius * 0.97, radius * 0.92),
          ring(0.96, radius * 0.9, radius * 0.86),
        ],
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
 * Features too small to be worth a chain of their own, and the face.
 *
 * Each one is a closed ellipsoid that intersects the surface it sits on, so how
 * deep it sits is what decides whether it reads as anatomy. Buried to its own
 * radius it lies almost tangent to the skin and the two surfaces fight for the
 * same pixels; sitting on the surface it reads as a ball stuck on. Roughly half
 * a radius in crosses the skin at about 60° and looks like one form.
 *
 * The skull's face front stands about 0.12 m ahead of the head bone, and its
 * side about 0.084 m out, which is what every number below is measured from.
 */
const EYE_X = 0.032;
const EYE_Y = 0.112;
const EYE_Z = 0.107;

const eye = (sign: 1 | -1): BodyBlob[] => [
  // The eyeball sits in its socket with only the front third proud, so it reads
  // as an eye rather than as a bead on the surface.
  {
    bone: 'head',
    centre: [sign * EYE_X, EYE_Y, EYE_Z],
    radii: [0.0125, 0.0115, 0.0115],
    colour: BODY_COLOURS.sclera,
    detail: 8,
  },
  // Iris and pupil, only just proud of the eyeball.
  {
    bone: 'head',
    centre: [sign * (EYE_X + 0.001), EYE_Y - 0.0005, EYE_Z + 0.0075],
    radii: [0.0068, 0.0068, 0.005],
    colour: BODY_COLOURS.iris,
    detail: 8,
  },
  // Upper lid: a skin-coloured shell over the top of the eyeball, which is what
  // stops an open sphere looking like a doll's eye.
  {
    bone: 'head',
    centre: [sign * EYE_X, EYE_Y + 0.0105, EYE_Z - 0.004],
    radii: [0.017, 0.008, 0.013],
    detail: 8,
  },
  // Lower lid and the cheekbone under it.
  {
    bone: 'head',
    centre: [sign * EYE_X, EYE_Y - 0.0125, EYE_Z - 0.006],
    radii: [0.02, 0.009, 0.014],
    detail: 8,
  },
  // Brow ridge above the eye, angled slightly out.
  {
    bone: 'head',
    centre: [sign * 0.031, 0.132, 0.087],
    radii: [0.026, 0.008, 0.011],
    colour: BODY_COLOURS.brow,
    detail: 8,
  },
];

export const BODY_BLOBS: BodyBlob[] = [
  ...eye(1),
  ...eye(-1),
  // Nose: a ridge down the middle of the face, then the tip.
  { bone: 'head', centre: [0, 0.098, 0.108], radii: [0.013, 0.03, 0.015] },
  { bone: 'head', centre: [0, 0.075, 0.112], radii: [0.0165, 0.013, 0.014] },
  // Mouth: an upper and a lower lip, both barely proud of the face.
  { bone: 'head', centre: [0, 0.05, 0.1], radii: [0.022, 0.005, 0.008], colour: BODY_COLOURS.lips, detail: 10 },
  { bone: 'head', centre: [0, 0.041, 0.099], radii: [0.02, 0.0055, 0.008], colour: BODY_COLOURS.lips, detail: 10 },
  // Chin and jaw corners.
  { bone: 'head', centre: [0, 0.024, 0.089], radii: [0.03, 0.019, 0.016] },
  { bone: 'head', centre: [-0.062, 0.04, 0.04], radii: [0.016, 0.018, 0.026] },
  { bone: 'head', centre: [0.062, 0.04, 0.04], radii: [0.016, 0.018, 0.026] },
  // Ears, standing a few millimetres proud of the skull.
  { bone: 'head', centre: [-0.079, 0.078, -0.004], radii: [0.009, 0.023, 0.014] },
  { bone: 'head', centre: [0.079, 0.078, -0.004], radii: [0.009, 0.023, 0.014] },
  // A close crop rather than modelled hair: a shell over the crown and back of
  // the skull only, tapering out at the hairline so it never reaches the face.
  { bone: 'head', centre: [0, 0.176, -0.014], radii: [0.091, 0.064, 0.107], colour: BODY_COLOURS.hair, detail: 16 },
  // The pad at the base of each thumb.
  { bone: 'hand_l', centre: [0, 0.03, 0.03], radii: [0.017, 0.028, 0.014] },
  { bone: 'hand_r', centre: [0, 0.03, 0.03], radii: [0.017, 0.028, 0.014] },
];
