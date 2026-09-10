import { describe, expect, it } from 'vitest';
import { AnimationMixer, Matrix4, Object3D, Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { bakeClip } from '../export/clipBuilder';
import { getExercise } from '../exercises/library';
import { buildSkinnedRig } from './skin';
import { buildBodyGeometry } from './mesh';
import { MUSCLE_GROUP_IDS } from '../muscles/groups';
import { MUSCLES, createMuscleTransform, resolveMuscle } from '../muscles/model';
import { showsMuscleBellies } from '../editor/store';
import type { ViewMode } from '../editor/store';
import { restPose } from '../rig/pose';
import {
  ELBOW_SAFE_PUSH,
  applyElbowCorrective,
  buildElbowCorrective,
  elbowFlexion,
} from './elbow';
import {
  ECORCHE_GREYSCALE,
  ECORCHE_GROUPS,
  ECORCHE_SAFE_MAX,
  ECORCHE_SAFE_MOVE,
  ECORCHE_PALETTE,
  ECORCHE_UNMAPPED,
  applyActivation,
  blendedSkinMatrix,
  boneInfluence,
  buildEcorcheGeometry,
  ecorcheColours,
  ecorcheFields,
  ecorcheHeight,
  skinnedFibre,
} from './ecorche';

const skeleton = canonicalSkeleton;
const curl = getExercise('dumbbell_bicep_curl');
const base = buildBodyGeometry(skeleton).geometry;
const geometry = buildEcorcheGeometry(skeleton);
const group = geometry.getAttribute('muscleGroup');
const position = geometry.getAttribute('position');
const basePosition = base.getAttribute('position');
const skinIndex = geometry.getAttribute('skinIndex');
const skinWeight = geometry.getAttribute('skinWeight');
const bicepsId = MUSCLE_GROUP_IDS.indexOf('biceps');

/**
 * The lower edge of the biceps field's skin-weight gate. The gate is a band
 * rather than a threshold — a hard cut leaves a step along the edge of a weight
 * island — so this, not the middle of the band, is what a mapped vertex has to
 * clear.
 */
const GATE_FLOOR = 0.1;

/**
 * Bones the anatomy view has no business displacing the surface over. The torso
 * round added the spine, the pelvis and the neck to what the view legitimately
 * sculpts, so what is left out is the head, the hands and everything below the
 * hips — the regions this milestone explicitly does not cover.
 */
const BLOCKED = new Set([
  'head',
  'hand_l',
  'hand_r',
  'thigh_l',
  'thigh_r',
  'shin_l',
  'shin_r',
  'foot_l',
  'foot_r',
]);
const SCULPTED = new Set([
  'upperarm_l',
  'upperarm_r',
  'forearm_l',
  'forearm_r',
  'clavicle_l',
  'clavicle_r',
  'neck',
  'spine_01',
  'spine_02',
  'spine_03',
  'pelvis',
]);

/** Every vertex the map assigns to a group. */
const mapped = (id: number): number[] => {
  const out: number[] = [];
  for (let index = 0; index < group.count; index += 1) {
    if (group.getX(index) === id) out.push(index);
  }
  return out;
};

const bicepsVertices = mapped(bicepsId);

/** Every vertex the anatomy build moved off the character's own surface. */
const movedVertices: number[] = [];
for (let index = 0; index < position.count; index += 1) {
  const distance = Math.hypot(
    position.getX(index) - basePosition.getX(index),
    position.getY(index) - basePosition.getY(index),
    position.getZ(index) - basePosition.getZ(index),
  );
  if (distance > 1e-9) movedVertices.push(index);
}

/** Bottom, mid-lift and top of a repetition. */
const CURL_TIMES = [0, 1, 2.5];

describe('the muscle map', () => {
  it('classifies every vertex as a real group or as nothing at all', () => {
    for (let index = 0; index < group.count; index += 1) {
      const id = group.getX(index);
      // Whole numbers: a normalised attribute would arrive as 0..1 fractions and
      // every id would silently collapse to zero.
      expect(Number.isInteger(id), `vertex ${index}`).toBe(true);
      if (id === ECORCHE_UNMAPPED) continue;
      expect(id, `vertex ${index}`).toBeGreaterThanOrEqual(0);
      expect(id, `vertex ${index}`).toBeLessThan(MUSCLE_GROUP_IDS.length);
    }
  });

  it('maps only the groups this revision claims to map', () => {
    const seen = new Set<string>();
    for (let index = 0; index < group.count; index += 1) {
      const id = group.getX(index);
      if (id !== ECORCHE_UNMAPPED) seen.add(MUSCLE_GROUP_IDS[id]);
    }
    // A subset, not an equality: classification goes to the strongest field at
    // each vertex, and a sheet lying under a stronger neighbour — a mid trapezius
    // beneath the upper one — can legitimately never win a vertex outright while
    // still contributing its shape. What must not happen is a group appearing
    // that this revision does not sculpt at all.
    for (const id of seen) expect(ECORCHE_GROUPS).toContain(id);
    for (const id of ['biceps', 'triceps', 'pectoralis', 'latissimus']) {
      expect(seen, `${id} should own some surface`).toContain(id);
    }
  });

  it('gives the biceps a patch on each arm, mirrored', () => {
    expect(bicepsVertices.length).toBeGreaterThan(100);
    let left = 0;
    let right = 0;
    for (const index of bicepsVertices) {
      if (position.getX(index) < 0) left += 1;
      else right += 1;
    }
    // The body is mirror-symmetric and so is the muscle model, so the two sides
    // should come out the same to within a vertex or two on the centre line.
    expect(Math.abs(left - right)).toBeLessThan(4);
  });

  it('only claims a vertex the muscle has real skin influence over', () => {
    const biceps = MUSCLES.filter((muscle) => muscle.group === 'biceps');
    for (const index of bicepsVertices) {
      // Weight-based, not an exact bone match: a vertex blended across the elbow
      // still belongs to the biceps.
      const best = Math.max(
        ...biceps.map((muscle) =>
          boneInfluence(
            skinIndex,
            skinWeight,
            index,
            new Set([muscle.origin.bone, muscle.insertion.bone]),
            skeleton,
          ),
        ),
      );
      expect(best, `vertex ${index}`).toBeGreaterThanOrEqual(GATE_FLOOR);
    }
  });
});

describe('the sculpted arm', () => {
  it('moves the surface by an amount a body could actually have', () => {
    expect(movedVertices.length).toBeGreaterThan(400);
    const height = ecorcheHeight(geometry);
    for (const index of movedVertices) {
      expect(height[index], `relief at ${index}`).toBeLessThanOrEqual(ECORCHE_SAFE_MAX);
      const distance = Math.hypot(
        position.getX(index) - basePosition.getX(index),
        position.getY(index) - basePosition.getY(index),
        position.getZ(index) - basePosition.getZ(index),
      );
      expect(distance, `movement at ${index}`).toBeLessThanOrEqual(ECORCHE_SAFE_MOVE);
    }
  });

  it('touches the arm and upper body and nothing else', () => {
    for (const index of movedVertices) {
      // Not "which bone is strongest" — a vertex at the deltoid, the armpit or
      // the elbow is legitimately blended across several. What must hold is that
      // the sculpted regions own it and the head, hands and legs do not.
      const blocked = boneInfluence(skinIndex, skinWeight, index, BLOCKED, skeleton);
      if (blocked >= 0.32) {
        // The one exception, and it has to stay one: the character binds the
        // whole neck to the head, so repairing that junction means touching
        // head-weighted surface. Anything that does must be inside the neck's own
        // band — within a wrist's width of its axis and below the jaw — which is
        // nowhere near the face.
        expect(position.getY(index), `neck exception at ${index}`).toBeLessThan(1.55);
        expect(position.getY(index), `neck exception at ${index}`).toBeGreaterThan(1.32);
        expect(
          Math.hypot(position.getX(index), position.getZ(index)),
          `neck exception at ${index}`,
        ).toBeLessThan(0.095);
        continue;
      }
      expect(
        boneInfluence(skinIndex, skinWeight, index, SCULPTED, skeleton),
        `sculpted influence at ${index}`,
      ).toBeGreaterThan(0.3);
    }
  });

  it('leaves the character surface exactly as it was', () => {
    // The anatomy build displaces a bind pose. If it were writing through a
    // shared buffer, Character mode and the GLB export would quietly inherit
    // every muscle in this view.
    const fresh = buildBodyGeometry(skeleton).geometry.getAttribute('position');
    for (let index = 0; index < fresh.count; index += 1) {
      expect(fresh.getX(index)).toBe(basePosition.getX(index));
      expect(fresh.getY(index)).toBe(basePosition.getY(index));
      expect(fresh.getZ(index)).toBe(basePosition.getZ(index));
    }
  });
});

describe('the arm through the curl', () => {
  const rig = buildSkinnedRig(skeleton, { geometry });
  const plain = buildSkinnedRig(skeleton, { geometry: base });
  const holder = new Object3D().add(rig.mesh);
  const plainHolder = new Object3D().add(plain.mesh);
  const clip = generateClip(skeleton, curl);
  const baked = bakeClip(clip, skeleton, { fps: 30 }).clip;
  const mixer = new AnimationMixer(holder);
  const plainMixer = new AnimationMixer(plainHolder);
  mixer.clipAction(baked).play();
  plainMixer.clipAction(baked).play();
  const evaluation = new PoseEvaluation(skeleton);
  const transform = createMuscleTransform();

  const poseAt = (time: number) => {
    for (const [each, root] of [
      [mixer, holder],
      [plainMixer, plainHolder],
    ] as const) {
      each.setTime(time);
      root.updateMatrixWorld(true);
    }
    rig.skeleton.update();
    plain.skeleton.update();
    evaluation.apply(clip.keyframes[0].pose);
  };

  const posed = (mesh: SkinnedMesh, index: number, out: Vector3): Vector3 => {
    out.fromBufferAttribute(mesh.geometry.getAttribute('position'), index);
    return mesh.applyBoneTransform(index, out);
  };

  it('stays on the front of the upper arm once the arm has moved', () => {
    // The count is fixed by construction, so counting proves nothing. What has
    // to hold is that these same vertices are still anatomically where the
    // biceps is after the skin has deformed.
    const point = new Vector3();
    const local = new Vector3();

    for (const time of CURL_TIMES) {
      poseAt(time);
      for (const side of ['l', 'r'] as const) {
        const muscle = MUSCLES.find((entry) => entry.group === 'biceps' && entry.side === side)!;
        resolveMuscle(evaluation, muscle, transform);

        let checked = 0;
        for (const index of bicepsVertices) {
          const onThisSide = side === 'l' ? position.getX(index) < 0 : position.getX(index) > 0;
          if (!onThisSide) continue;
          posed(rig.mesh, index, point);
          // In the humerus's own frame: in front of the bone, and along it.
          evaluation.worldToLocal(`upperarm_${side}`, point, local);
          expect(local.z, `vertex ${index} at ${time}s`).toBeGreaterThan(-0.01);
          expect(local.y, `vertex ${index} at ${time}s`).toBeGreaterThan(-0.02);
          expect(
            local.y,
            `vertex ${index} at ${time}s`,
          ).toBeLessThan(skeleton.bone(`upperarm_${side}`).length + 0.06);
          checked += 1;
        }
        expect(checked, `${side} biceps vertices`).toBeGreaterThan(40);
      }
    }
  });

  it('deforms without the sculpt tearing loose or folding where it should not', () => {
    // Measured against this surface itself, not against the character's. The two
    // no longer share their elbow weights on purpose, so a disagreement there is
    // the change working, not a defect. What has to hold is that the anatomy
    // mesh stays consistent with its own skinning: a triangle's posed normal
    // must still agree with its bind normal carried through the same weighted
    // transform, and no triangle may be crushed out of existence.
    const moved = new Set(movedVertices);
    const index = geometry.getIndex()!;
    const affected: number[] = [];
    for (let corner = 0; corner < index.count; corner += 3) {
      const a = index.getX(corner);
      const b = index.getX(corner + 1);
      const c = index.getX(corner + 2);
      if (moved.has(a) || moved.has(b) || moved.has(c)) affected.push(corner);
    }
    expect(affected.length).toBeGreaterThan(400);

    const here = new Vector3();
    const there = new Vector3();
    const posedCorner = [new Vector3(), new Vector3(), new Vector3()];
    const bindCorner = [new Vector3(), new Vector3(), new Vector3()];
    const posedNormal = new Vector3();
    const bindNormal = new Vector3();
    const expected = new Vector3();
    const carried = new Vector3();
    const matrix = new Matrix4();
    const edge = new Vector3();
    const other = new Vector3();
    const cross = new Vector3();
    const normalOf = (triangle: Vector3[]): Vector3 =>
      cross.crossVectors(
        edge.subVectors(triangle[1], triangle[0]),
        other.subVectors(triangle[2], triangle[0]),
      );

    /**
     * How many triangles fold through themselves at the top of the curl, and how
     * far from an elbow the furthest one is. Both are measured, not aspired to:
     * the inside of the elbow does self-intersect at 126°, on the character's own
     * weights as much as on these. The bound is here so the fold cannot spread
     * beyond the crease, or get worse, without a test saying so.
     */
    const INVERTED_AT_TOP = 80;
    /**
     * Far enough to cover both places this body folds: the elbow crease, and the
     * flank where the hanging arm presses against the waist. Nothing on the
     * chest, the back or the abdomen away from an arm may invert.
     */
    const CREASE_REACH = 0.14;

    for (const time of CURL_TIMES) {
      poseAt(time);
      const elbow = ['l', 'r'].map((side) =>
        evaluation.head(`forearm_${side as 'l' | 'r'}`, new Vector3()),
      );
      let inverted = 0;

      for (const vertex of movedVertices) {
        posed(rig.mesh, vertex, here);
        posed(plain.mesh, vertex, there);
        expect(
          here.distanceTo(there),
          `vertex ${vertex} at ${time}s`,
        ).toBeLessThan(ECORCHE_SAFE_MOVE * 1.6);
      }

      for (const corner of affected) {
        for (let slot = 0; slot < 3; slot += 1) {
          const vertex = index.getX(corner + slot);
          posed(rig.mesh, vertex, posedCorner[slot]);
          bindCorner[slot].fromBufferAttribute(position, vertex);
        }
        posedNormal.copy(normalOf(posedCorner));
        bindNormal.copy(normalOf(bindCorner));
        if (posedNormal.lengthSq() < 1e-18 || bindNormal.lengthSq() < 1e-18) continue;
        posedNormal.normalize();
        bindNormal.normalize();

        // The bind normal, carried by the same weighted transform the vertices
        // get. Where the surface is behaving, the posed normal matches it.
        expected.set(0, 0, 0);
        for (let slot = 0; slot < 3; slot += 1) {
          carried.copy(bindNormal);
          blendedSkinMatrix(rig.mesh, index.getX(corner + slot), matrix);
          expected.add(carried.transformDirection(matrix));
        }
        if (expected.lengthSq() < 1e-18) continue;

        if (posedNormal.dot(expected.normalize()) > 0) continue;
        inverted += 1;
        // Wherever it folds, it folds in the crease and nowhere else.
        const distance = Math.min(
          ...posedCorner.map((point) => Math.min(...elbow.map((joint) => point.distanceTo(joint)))),
        );
        expect(distance, `inverted triangle ${corner} at ${time}s`).toBeLessThan(CREASE_REACH);
      }
      expect(inverted, `inverted triangles at ${time}s`).toBeLessThanOrEqual(INVERTED_AT_TOP);
    }
  });

  it('skins the fibre direction the way the vertex itself is skinned', () => {
    // The shader builds its own weighted bone transform for the fibre. Three's
    // own skinning is the independent reference: skin two points a hair apart
    // along the bind-pose fibre and the direction between them is what the
    // fibre must become.
    const here = new Vector3();
    const there = new Vector3();
    const expected = new Vector3();
    const actual = new Vector3();
    const fibre = geometry.getAttribute('muscleFibre');
    const step = 1e-4;

    for (const time of CURL_TIMES) {
      poseAt(time);
      for (const index of bicepsVertices.slice(0, 60)) {
        here.fromBufferAttribute(position, index);
        there
          .copy(here)
          .addScaledVector(
            new Vector3(fibre.getX(index), fibre.getY(index), fibre.getZ(index)),
            step,
          );
        rig.mesh.applyBoneTransform(index, here);
        rig.mesh.applyBoneTransform(index, there);
        expected.subVectors(there, here).normalize();

        skinnedFibre(rig.mesh, index, actual).normalize();
        expect(actual.length()).toBeCloseTo(1, 5);
        expect(actual.dot(expected), `vertex ${index} at ${time}s`).toBeGreaterThan(0.999);
      }
    }
  });
});

describe('the elbow correction', () => {
  const corrective = buildElbowCorrective(geometry, skeleton);
  const at = (drive: [number, number]): Float32Array => {
    applyElbowCorrective(geometry, corrective, drive);
    const out = new Float32Array(corrective.vertex.length * 3);
    for (let slot = 0; slot < corrective.vertex.length; slot += 1) {
      const vertex = corrective.vertex[slot];
      out[slot * 3] = position.getX(vertex);
      out[slot * 3 + 1] = position.getY(vertex);
      out[slot * 3 + 2] = position.getZ(vertex);
    }
    return out;
  };

  it('returns the surface exactly at extension, so the loop still closes', () => {
    const bent = at([1, 1]);
    const straight = at([0, 0]);
    let moved = 0;
    for (let slot = 0; slot < corrective.vertex.length; slot += 1) {
      // Exactly, not nearly: a correction that leaves a residue at extension
      // would put the first frame of the clip somewhere the last frame is not.
      expect(straight[slot * 3]).toBe(corrective.bind[slot * 3]);
      expect(straight[slot * 3 + 1]).toBe(corrective.bind[slot * 3 + 1]);
      expect(straight[slot * 3 + 2]).toBe(corrective.bind[slot * 3 + 2]);
      if (Math.abs(bent[slot * 3] - straight[slot * 3]) > 1e-9) moved += 1;
    }
    expect(moved).toBeGreaterThan(20);
    expect(elbowFlexion(new PoseEvaluation(skeleton).apply(restPose()), 'l')).toBe(0);
  });

  it('corrects both elbows the same way', () => {
    const magnitude = { l: [] as number[], r: [] as number[] };
    for (let slot = 0; slot < corrective.vertex.length; slot += 1) {
      const size = Math.hypot(
        corrective.offset[slot * 3],
        corrective.offset[slot * 3 + 1],
        corrective.offset[slot * 3 + 2],
      );
      magnitude[corrective.side[slot] === 0 ? 'l' : 'r'].push(size);
      expect(size, `vertex ${corrective.vertex[slot]}`).toBeLessThanOrEqual(ELBOW_SAFE_PUSH);
    }
    expect(Math.abs(magnitude.l.length - magnitude.r.length)).toBeLessThan(4);
    const total = (values: number[]) => values.reduce((carry, value) => carry + value, 0);
    expect(total(magnitude.l)).toBeCloseTo(total(magnitude.r), 4);
  });
});

describe('the anatomy view', () => {
  it('renders in grey, with the muscle field still built underneath', () => {
    applyActivation(geometry, curl.muscles);
    const activation = geometry.getAttribute('muscleActivation');
    for (let index = 0; index < activation.count; index += 1) {
      const value = activation.getX(index);
      expect(value).toBeGreaterThanOrEqual(0);
      expect(value).toBeLessThanOrEqual(1);
      // This round judges anatomy and movement, so the activation path is wired
      // up and held at zero rather than removed.
      if (ECORCHE_GREYSCALE) expect(value).toBe(0);
    }

    // The field the colour would read is real, continuous and on the biceps.
    const biceps = ecorcheFields(geometry).biceps;
    expect(biceps).toBeDefined();
    let peak = 0;
    for (const index of bicepsVertices) peak = Math.max(peak, biceps[index]);
    expect(peak).toBeGreaterThan(0.5);
    expect(peak).toBeLessThanOrEqual(1);
  });

  it('draws one surface and no bellies', () => {
    const modes: ViewMode[] = ['skeleton', 'muscles', 'combined', 'character', 'anatomy'];
    expect(modes.filter(showsMuscleBellies)).toEqual(['muscles', 'combined']);
    expect(showsMuscleBellies('anatomy')).toBe(false);
  });

  it('restates the character in the écorché palette', () => {
    // On the character's own colours, not on an already-restated copy.
    const colours = ecorcheColours(buildBodyGeometry(skeleton).geometry);
    const distinct = new Set<string>();
    for (let index = 0; index < colours.length; index += 3) {
      distinct.add(`${colours[index]},${colours[index + 1]},${colours[index + 2]}`);
    }
    // Muscle, hair, clothing, sclera, iris and pupil: the same six parts the
    // character has, restated rather than reduced. Every vertex lands on one of
    // them — including the graded hairline, which has no exact palette colour
    // and must still be restated rather than left as skin.
    expect(distinct.size).toBe(6);
    const palette = new Set(
      Object.values(ECORCHE_PALETTE).map((hex) => {
        const value = Number.parseInt(hex.slice(1), 16);
        return [16, 8, 0]
          .map((shift) => {
            const channel = ((value >> shift) & 255) / 255;
            const linear = channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
            return Math.round(linear * 255);
          })
          .join(',');
      }),
    );
    for (const entry of distinct) expect(palette.has(entry), entry).toBe(true);
  });
});
