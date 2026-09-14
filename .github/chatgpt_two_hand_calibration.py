from pathlib import Path


def read(path):
    return Path(path).read_text()


def write(path, text):
    Path(path).write_text(text)


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)


# --- equipment attachment schema -----------------------------------------
p = 'src/equipment/types.ts'
s = read(p)
s = replace_once(
    s,
    """  | {
      mode: 'hands';
      /** Sockets gripped by the left and right hands. */
      leftSocket: string;
      rightSocket: string;
      gripOffset?: Vec3;
    };""",
    """  | {
      mode: 'hands';
      /** Sockets gripped by the left and right hands. */
      leftSocket: string;
      rightSocket: string;
      /** Shared hand-local grip point retained for backwards compatibility. */
      gripOffset?: Vec3;
      /** Optional side-specific hand-local grip points. */
      leftGripOffset?: Vec3;
      rightGripOffset?: Vec3;
      /** Roll of the rigid two-hand item around the line joining both grips, degrees. */
      gripRoll?: number;
    };""",
    'two-hand attachment schema',
)
write(p, s)


# --- socket-width calibration utility ------------------------------------
p = 'src/equipment/library.ts'
s = read(p)
s += r'''

/**
 * Return a copy of a two-hand equipment instance with its two authored grip
 * sockets moved symmetrically to the requested separation. Passing null removes
 * only the positional calibration and restores the library socket positions;
 * any socket-rotation override remains intact.
 */
export function withTwoHandGripWidth(
  instance: EquipmentInstance,
  width: number | null,
): EquipmentInstance {
  if (instance.attachment.mode !== 'hands') return instance;
  const { leftSocket, rightSocket } = instance.attachment;
  const left = equipmentSocketForInstance(instance, leftSocket);
  const right = equipmentSocketForInstance(instance, rightSocket);
  if (!left || !right) return instance;

  const socketOverrides: EquipmentInstance['socketOverrides'] = {
    ...(instance.socketOverrides ?? {}),
  };

  const setPosition = (socketId: string, position: EquipmentSocket['position'] | null) => {
    const previous = socketOverrides?.[socketId] ?? {};
    if (!position) {
      const { position: _position, ...remaining } = previous;
      if (Object.keys(remaining).length > 0) socketOverrides![socketId] = remaining;
      else delete socketOverrides![socketId];
      return;
    }
    socketOverrides![socketId] = { ...previous, position: { ...position } };
  };

  if (width === null) {
    setPosition(leftSocket, null);
    setPosition(rightSocket, null);
  } else {
    const requested = Math.max(0.1, Math.min(2.0, width));
    const midpoint = {
      x: (left.position.x + right.position.x) / 2,
      y: (left.position.y + right.position.y) / 2,
      z: (left.position.z + right.position.z) / 2,
    };
    const axis = {
      x: right.position.x - left.position.x,
      y: right.position.y - left.position.y,
      z: right.position.z - left.position.z,
    };
    const length = Math.hypot(axis.x, axis.y, axis.z) || 1;
    const half = requested / 2;
    const unit = { x: axis.x / length, y: axis.y / length, z: axis.z / length };
    setPosition(leftSocket, {
      x: midpoint.x - unit.x * half,
      y: midpoint.y - unit.y * half,
      z: midpoint.z - unit.z * half,
    });
    setPosition(rightSocket, {
      x: midpoint.x + unit.x * half,
      y: midpoint.y + unit.y * half,
      z: midpoint.z + unit.z * half,
    });
  }

  return {
    ...instance,
    socketOverrides:
      socketOverrides && Object.keys(socketOverrides).length > 0 ? socketOverrides : undefined,
  };
}
'''
write(p, s)


# --- true two-hand socket fit solver -------------------------------------
p = 'src/equipment/attach.ts'
s = read(p)
old = """  // Two-handed: the bar spans the two grips.
  const grip = attachment.gripOffset ?? { x: 0, y: 0.045, z: 0 };
  const left = evaluation.localToWorld('hand_l', grip, new Vector3());
  const right = evaluation.localToWorld('hand_r', grip, new Vector3());
  const axis = new Vector3().subVectors(right, left);
  if (axis.lengthSq() < 1e-8) return null;
  axis.normalize();

  // Keep the bar level: its local +Y stays as close to world up as the grip allows.
  const up = new Vector3(0, 1, 0).addScaledVector(axis, -axis.y);
  if (up.lengthSq() < 1e-8) up.set(0, 0, 1).addScaledVector(axis, -axis.z);
  up.normalize();
  const side = new Vector3().crossVectors(up, axis).normalize();

  const quaternion = new Quaternion().setFromRotationMatrix(
    new Matrix4().makeBasis(side, up, axis),
  );
  const centre = left.clone().add(right).multiplyScalar(0.5);
  const position = centre;
  return {
    id: instance.id,
    position,
    quaternion,
    matrix: new Matrix4().compose(position, quaternion, UNIT),
  };
"""
new = """  const matrix = twoHandAttachmentMatrix(
    evaluation.matrix('hand_l'),
    evaluation.matrix('hand_r'),
    instance,
  );
  return matrix ? decompose(instance.id, matrix) : null;
"""
s = replace_once(s, old, new, 'replace placeholder two-hand solver')

insert = r'''

/** Hand-local targets used by a rigid two-hand attachment. */
export function twoHandGripOffsets(instance: EquipmentInstance): {
  left: { x: number; y: number; z: number };
  right: { x: number; y: number; z: number };
} | null {
  if (instance.attachment.mode !== 'hands') return null;
  const fallback = instance.attachment.gripOffset ?? { x: 0, y: 0.045, z: 0 };
  return {
    left: instance.attachment.leftGripOffset ?? fallback,
    right: instance.attachment.rightGripOffset ?? fallback,
  };
}

/**
 * Fit one rigid two-hand equipment instance from its actual authored grip
 * sockets to the two hand-local grip targets. The midpoint and socket axis are
 * matched exactly; if socket separation differs from hand separation the
 * residual is reported by the grip diagnostics rather than being hidden by
 * wrist/arm compensation or non-rigid scaling.
 */
export function twoHandAttachmentMatrix(
  leftHand: Matrix4,
  rightHand: Matrix4,
  instance: EquipmentInstance,
): Matrix4 | null {
  if (instance.attachment.mode !== 'hands') return null;
  const offsets = twoHandGripOffsets(instance);
  if (!offsets) return null;
  const leftSocket = equipmentSocketForInstance(instance, instance.attachment.leftSocket);
  const rightSocket = equipmentSocketForInstance(instance, instance.attachment.rightSocket);
  if (!leftSocket || !rightSocket) return null;

  const leftTarget = new Vector3(offsets.left.x, offsets.left.y, offsets.left.z).applyMatrix4(leftHand);
  const rightTarget = new Vector3(offsets.right.x, offsets.right.y, offsets.right.z).applyMatrix4(rightHand);
  const worldAxis = new Vector3().subVectors(rightTarget, leftTarget);
  const localAxis = new Vector3(
    rightSocket.position.x - leftSocket.position.x,
    rightSocket.position.y - leftSocket.position.y,
    rightSocket.position.z - leftSocket.position.z,
  );
  if (worldAxis.lengthSq() < 1e-8 || localAxis.lengthSq() < 1e-8) return null;
  worldAxis.normalize();
  localAxis.normalize();

  const basisFor = (axis: Vector3, preferredUp: Vector3) => {
    const up = preferredUp.clone().addScaledVector(axis, -preferredUp.dot(axis));
    if (up.lengthSq() < 1e-8) {
      up.set(1, 0, 0).addScaledVector(axis, -axis.x);
    }
    up.normalize();
    const side = new Vector3().crossVectors(up, axis).normalize();
    return new Matrix4().makeBasis(side, up, axis);
  };

  const localBasis = basisFor(localAxis, Y_AXIS);
  const worldBasis = basisFor(worldAxis, Y_AXIS);
  const localQ = new Quaternion().setFromRotationMatrix(localBasis);
  const worldQ = new Quaternion().setFromRotationMatrix(worldBasis);
  const quaternion = worldQ.multiply(localQ.invert());
  const roll = instance.attachment.gripRoll ?? 0;
  if (Math.abs(roll) > 1e-9) {
    quaternion.premultiply(
      new Quaternion().setFromAxisAngle(worldAxis, toRad(roll)),
    );
  }

  const localMid = new Vector3(
    (leftSocket.position.x + rightSocket.position.x) / 2,
    (leftSocket.position.y + rightSocket.position.y) / 2,
    (leftSocket.position.z + rightSocket.position.z) / 2,
  );
  const worldMid = leftTarget.clone().add(rightTarget).multiplyScalar(0.5);
  const rotatedLocalMid = localMid.clone().applyQuaternion(quaternion);
  const position = worldMid.sub(rotatedLocalMid);
  return new Matrix4().compose(position, quaternion, UNIT);
}
'''
anchor = "\n/**\n * Centre of a cylindrical handle inside the curled fingers, in hand-local"
s = replace_once(s, anchor, insert + anchor, 'insert two-hand attachment helper')
write(p, s)


# --- imported preserved-skeleton preview uses the same two-hand fit -------
p = 'src/viewer/EquipmentView.tsx'
s = read(p)
s = replace_once(
    s,
    "import { handAttachmentMatrix } from '../export/clipBuilder';",
    "import { handAttachmentMatrix } from '../export/clipBuilder';\nimport { twoHandAttachmentMatrix } from '../equipment/attach';",
    'two hand view import',
)
needle = """      if (held && instance?.attachment.mode === 'hand') {
        const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
        const grip = instance.attachment.gripOffset ?? { x: 0, y: 0.045, z: 0 };
        scratch.local.copy(handAttachmentMatrix(
          grip,
          socket?.position ?? { x: 0, y: 0, z: 0 },
          { gripRotation: instance.attachment.gripRotation, socketRotation: socket?.rotation },
        ));
        group.visible = true;
        group.matrix.multiplyMatrices(held, scratch.local);
        group.matrixWorldNeedsUpdate = true;
        continue;
      }
"""
replacement = needle + """
      if (instance?.attachment.mode === 'hands' && character?.handMatrix) {
        const leftHand = character.handMatrix('l', new Matrix4());
        const rightHand = character.handMatrix('r', new Matrix4());
        const local = twoHandAttachmentMatrix(leftHand, rightHand, instance);
        if (local) {
          group.visible = true;
          group.matrix.copy(local);
          group.matrixWorldNeedsUpdate = true;
          continue;
        }
      }
"""
s = replace_once(s, needle, replacement, 'two hand imported preview')
write(p, s)


# --- two-hand diagnostics --------------------------------------------------
p = 'src/equipment/gripDiagnostics.ts'
s = read(p)
s = replace_once(
    s,
    "import type { EquipmentTransform } from './attach';",
    "import { twoHandGripOffsets, type EquipmentTransform } from './attach';\nimport type { EquipmentInstance } from './types';\nimport { equipmentSocketForInstance } from './library';",
    'diagnostic imports',
)
s += r'''

export interface TwoHandFitMeasurement {
  leftError: number;
  rightError: number;
  targetSeparation: number;
  socketSeparation: number;
  separationError: number;
  withinEnvelope: boolean;
}

/**
 * Measure positional fit of a rigid two-hand item at the current frame. A
 * spacing mismatch is deliberately visible: the solver never scales the bar or
 * moves the wrists to hide it.
 */
export function measureTwoHandFit(
  evaluation: PoseEvaluation,
  instance: EquipmentInstance,
  equipment: EquipmentTransform,
): TwoHandFitMeasurement | null {
  if (instance.attachment.mode !== 'hands') return null;
  const offsets = twoHandGripOffsets(instance);
  const leftSocket = equipmentSocketForInstance(instance, instance.attachment.leftSocket);
  const rightSocket = equipmentSocketForInstance(instance, instance.attachment.rightSocket);
  if (!offsets || !leftSocket || !rightSocket) return null;

  const leftTarget = evaluation.localToWorld('hand_l', offsets.left, new Vector3());
  const rightTarget = evaluation.localToWorld('hand_r', offsets.right, new Vector3());
  const leftActual = new Vector3(
    leftSocket.position.x,
    leftSocket.position.y,
    leftSocket.position.z,
  ).applyMatrix4(equipment.matrix);
  const rightActual = new Vector3(
    rightSocket.position.x,
    rightSocket.position.y,
    rightSocket.position.z,
  ).applyMatrix4(equipment.matrix);
  const targetSeparation = leftTarget.distanceTo(rightTarget);
  const socketSeparation = leftActual.distanceTo(rightActual);
  const leftError = leftActual.distanceTo(leftTarget);
  const rightError = rightActual.distanceTo(rightTarget);
  return {
    leftError,
    rightError,
    targetSeparation,
    socketSeparation,
    separationError: socketSeparation - targetSeparation,
    withinEnvelope: Math.max(leftError, rightError) <= 0.005,
  };
}
'''
write(p, s)


# --- store authoring -------------------------------------------------------
p = 'src/editor/store.ts'
s = read(p)
s = replace_once(
    s,
    "import { equipmentSocket } from '../equipment/library';",
    "import { equipmentSocket, withTwoHandGripWidth } from '../equipment/library';",
    'store width helper import',
)
s = replace_once(
    s,
    "  setEquipmentGripRotation: (instanceId: string, rotation: Vec3 | null) => void;",
    "  setEquipmentGripRotation: (instanceId: string, rotation: Vec3 | null) => void;\n  setTwoHandGripWidth: (instanceId: string, width: number | null) => void;\n  setTwoHandGripRoll: (instanceId: string, degrees: number | null) => void;",
    'store two hand interface',
)
insert = r'''

    setTwoHandGripWidth: (instanceId, width) =>
      commit((document) => {
        const instances = document.exercise.equipment.instances.map((instance) =>
          instance.id === instanceId ? withTwoHandGripWidth(instance, width) : instance,
        );
        const exercise = {
          ...document.exercise,
          equipment: { ...document.exercise.equipment, instances },
        };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),

    setTwoHandGripRoll: (instanceId, degrees) =>
      commit((document) => {
        const instances = document.exercise.equipment.instances.map((instance) => {
          if (instance.id !== instanceId || instance.attachment.mode !== 'hands') return instance;
          if (degrees === null || Math.abs(degrees) < 1e-9) {
            const { gripRoll: _gripRoll, ...attachment } = instance.attachment;
            return { ...instance, attachment };
          }
          return {
            ...instance,
            attachment: { ...instance.attachment, gripRoll: degrees },
          };
        });
        const exercise = {
          ...document.exercise,
          equipment: { ...document.exercise.equipment, instances },
        };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),
'''
s = replace_once(
    s,
    "\n    setEquipmentTransform: (instanceId, transform) => {",
    insert + "\n    setEquipmentTransform: (instanceId, transform) => {",
    'store two hand implementations',
)
write(p, s)


# --- Grip workspace UI -----------------------------------------------------
p = 'src/editor/panels/GripPanel.tsx'
s = read(p)
s = replace_once(
    s,
    "import { GRIP_CLOSURE_PRESETS, measureGripFit } from '../../equipment/gripDiagnostics';",
    "import { GRIP_CLOSURE_PRESETS, measureGripFit, measureTwoHandFit } from '../../equipment/gripDiagnostics';\nimport { equipmentSocketForInstance } from '../../equipment/library';",
    'GripPanel two hand imports',
)
s = replace_once(
    s,
    "  const setEquipmentGripRotation = useStudio((state) => state.setEquipmentGripRotation);",
    "  const setEquipmentGripRotation = useStudio((state) => state.setEquipmentGripRotation);\n  const setTwoHandGripWidth = useStudio((state) => state.setTwoHandGripWidth);\n  const setTwoHandGripRoll = useStudio((state) => state.setTwoHandGripRoll);",
    'GripPanel two hand setters',
)
needle = """  }, [clip, exercise.equipment.instances, time]);

  const updateOffset"""
replacement = """  }, [clip, exercise.equipment.instances, time]);

  const twoHandMeasurements = useMemo(() => {
    const evaluation = new PoseEvaluation(skeleton);
    const frame = resolveFrame(skeleton, evaluation, clip, time);
    evaluation.apply(frame.pose);
    return exercise.equipment.instances.flatMap((instance) => {
      if (instance.attachment.mode !== 'hands') return [];
      const transform = frame.equipment.get(instance.id);
      if (!transform) return [];
      const fit = measureTwoHandFit(evaluation, instance, transform);
      const left = equipmentSocketForInstance(instance, instance.attachment.leftSocket);
      const right = equipmentSocketForInstance(instance, instance.attachment.rightSocket);
      if (!fit || !left || !right) return [];
      return [{
        id: instance.id,
        label: instance.label ?? instance.id,
        fit,
        width: Math.hypot(
          right.position.x - left.position.x,
          right.position.y - left.position.y,
          right.position.z - left.position.z,
        ),
        roll: instance.attachment.gripRoll ?? 0,
        hasWidthOverride: Boolean(
          instance.socketOverrides?.[instance.attachment.leftSocket]?.position ||
          instance.socketOverrides?.[instance.attachment.rightSocket]?.position
        ),
      }];
    });
  }, [clip, exercise.equipment.instances, time]);

  const updateOffset"""
s = replace_once(s, needle, replacement, 'GripPanel two hand measurements')
needle = """      <p className=\"panel__hint\">
        Grip X/Y/Z is the handle centre in hand-local millimetres; orientation is a hand-local Euler calibration in degrees. “Within envelope” uses the same
        finger reach and wrap geometry as the Studio's grip regression. It is an animation-fit diagnostic,
        not a force or injury-safety score.
      </p>
"""
replacement = needle + r'''

      {twoHandMeasurements.length > 0 && (
        <>
          <h3>Two-hand rigid fit</h3>
          <div className="grip-fit-list">
            {twoHandMeasurements.map(({ id, label, fit, width, roll, hasWidthOverride }) => (
              <div className="grip-fit" key={`two-hand-${id}`}>
                <div className="grip-fit__head">
                  <strong>{label}</strong>
                  <span className={fit.withinEnvelope ? 'status-ok' : 'status-warn'}>
                    {fit.withinEnvelope ? 'Sockets aligned' : 'Calibrate spacing'}
                  </span>
                </div>
                <div className="grip-offset-grid">
                  <label className="field">
                    <span className="field__label">Grip width · cm</span>
                    <input
                      type="number"
                      step={1}
                      min={10}
                      max={200}
                      value={Number((width * 100).toFixed(1))}
                      onChange={(event) => setTwoHandGripWidth(id, Number(event.target.value) / 100)}
                    />
                  </label>
                  <label className="field">
                    <span className="field__label">Bar roll · °</span>
                    <input
                      type="number"
                      step={1}
                      value={Number(roll.toFixed(1))}
                      onChange={(event) => setTwoHandGripRoll(id, Number(event.target.value))}
                    />
                  </label>
                </div>
                <div className="button-row">
                  <button
                    type="button"
                    disabled={!hasWidthOverride}
                    onClick={() => setTwoHandGripWidth(id, null)}
                  >
                    Reset grip width
                  </button>
                  <button
                    type="button"
                    disabled={Math.abs(roll) < 1e-9}
                    onClick={() => setTwoHandGripRoll(id, null)}
                  >
                    Reset roll
                  </button>
                </div>
                <dl className="spec-list">
                  <dt>Left socket error</dt>
                  <dd>{(fit.leftError * 1000).toFixed(1)} mm</dd>
                  <dt>Right socket error</dt>
                  <dd>{(fit.rightError * 1000).toFixed(1)} mm</dd>
                  <dt>Hands separation</dt>
                  <dd>{(fit.targetSeparation * 100).toFixed(1)} cm</dd>
                  <dt>Socket separation</dt>
                  <dd>{(fit.socketSeparation * 100).toFixed(1)} cm</dd>
                </dl>
              </div>
            ))}
          </div>
          <p className="panel__hint">
            Two-hand equipment is always rigid. Grip width moves only the authored contact sockets
            along the item; the solver never scales the bar or moves wrists/shoulders to hide a mismatch.
          </p>
        </>
      )}
'''
s = replace_once(s, needle, replacement, 'GripPanel two hand UI')
write(p, s)


# --- tests ----------------------------------------------------------------
write('src/equipment/twoHandAttachment.test.ts', r'''import { describe, expect, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import { resolveEquipment, twoHandAttachmentMatrix, twoHandGripOffsets } from './attach';
import { measureTwoHandFit } from './gripDiagnostics';
import { withTwoHandGripWidth } from './library';
import type { EquipmentInstance } from './types';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { restPose } from '../rig/pose';

const base: EquipmentInstance = {
  id: 'test_bar',
  kind: 'barbell',
  position: { x: 0, y: 0, z: 0 },
  rotation: { x: 0, y: 0, z: 0 },
  attachment: {
    mode: 'hands',
    leftSocket: 'grip_l',
    rightSocket: 'grip_r',
  },
  visible: true,
};

const evaluation = () => {
  const result = new PoseEvaluation(canonicalSkeleton);
  result.apply(restPose(canonicalSkeleton));
  return result;
};

describe('rigid two-hand equipment attachment', () => {
  it('uses the authored equipment sockets and exposes a real spacing residual', () => {
    const pose = evaluation();
    const transform = resolveEquipment(pose, [base]).get(base.id)!;
    const fit = measureTwoHandFit(pose, base, transform)!;
    expect(fit.socketSeparation).toBeCloseTo(0.8, 8);
    expect(fit.leftError).toBeCloseTo(fit.rightError, 8);
    expect(fit.leftError).toBeCloseTo(Math.abs(fit.separationError) / 2, 8);
  });

  it('can calibrate socket width to the hands without scaling the rigid item', () => {
    const pose = evaluation();
    const first = resolveEquipment(pose, [base]).get(base.id)!;
    const target = measureTwoHandFit(pose, base, first)!.targetSeparation;
    const calibrated = withTwoHandGripWidth(base, target);
    const transform = resolveEquipment(pose, [calibrated]).get(base.id)!;
    const fit = measureTwoHandFit(pose, calibrated, transform)!;
    expect(fit.leftError).toBeLessThan(1e-8);
    expect(fit.rightError).toBeLessThan(1e-8);
    expect(fit.withinEnvelope).toBe(true);
    expect(transform.matrix.determinant()).toBeCloseTo(1, 8);
  });

  it('applies roll around the grip axis without changing either socket position', () => {
    const pose = evaluation();
    const first = resolveEquipment(pose, [base]).get(base.id)!;
    const target = measureTwoHandFit(pose, base, first)!.targetSeparation;
    const calibrated = withTwoHandGripWidth(base, target);
    const rolled: EquipmentInstance = {
      ...calibrated,
      attachment: { ...calibrated.attachment, gripRoll: 17 },
    };
    const before = resolveEquipment(pose, [calibrated]).get(base.id)!;
    const after = resolveEquipment(pose, [rolled]).get(base.id)!;
    const beforeFit = measureTwoHandFit(pose, calibrated, before)!;
    const afterFit = measureTwoHandFit(pose, rolled, after)!;
    expect(afterFit.leftError).toBeLessThan(1e-8);
    expect(afterFit.rightError).toBeLessThan(1e-8);
    expect(after.quaternion.angleTo(before.quaternion)).toBeGreaterThan(0.1);
  });

  it('works from arbitrary hand matrices for preserved-source imported characters', () => {
    const left = new Matrix4().makeTranslation(-0.31, 1.15, 0.22);
    const right = new Matrix4().makeTranslation(0.31, 1.15, 0.22);
    const calibrated = withTwoHandGripWidth(base, 0.62);
    const matrix = twoHandAttachmentMatrix(left, right, calibrated)!;
    const offsets = twoHandGripOffsets(calibrated)!;
    const centre = new Vector3().setFromMatrixPosition(matrix);
    expect(centre.y).toBeCloseTo(1.15 + offsets.left.y, 8);
    expect(centre.z).toBeCloseTo(0.22 + offsets.left.z, 8);
  });
});
''')


# --- docs/changelog -------------------------------------------------------
p = 'docs/STUDIO_CAPABILITY_ROADMAP.md'
s = read(p)
needle = '- Per-instance hand-local grip orientation calibration rotates one-hand equipment around the same socket/contact centre without twisting wrist/arm animation; position and orientation reset independently.'
s = replace_once(
    s,
    needle,
    needle + '\n- Two-hand rigid equipment now fits its actual left/right grip sockets to the two hand-local targets. Per-exercise grip-width calibration adjusts only those contact sockets, bar roll rotates around the bilateral grip axis, and live diagnostics expose left/right millimetre residuals instead of hiding spacing mismatch with wrist/shoulder compensation.',
    'roadmap two hand calibration',
)
write(p, s)

p = 'AI_CHANGELOG.md'
s = read(p)
entry = '''### ChatGPT — 2026-09-14 — rigid two-hand socket calibration\n\nReplaced the placeholder `hands` attachment (which merely drew equipment along the line between both hands) with a rigid socket-fit solver. Two-hand equipment now uses its actual authored `leftSocket`/`rightSocket` positions, maps their midpoint and axis onto the two hand-local grip targets, and never non-uniformly scales the item. Any difference between hand separation and socket separation remains a measurable symmetric residual rather than being hidden by wrist/elbow/shoulder compensation. Optional left/right grip offsets and a scalar `gripRoll` are now part of the two-hand attachment data.\n\nAdded `withTwoHandGripWidth()` for per-exercise contact-width authoring: it moves only the two grip socket positions symmetrically along their existing local axis and can reset those positions back to immutable library defaults without erasing unrelated socket-rotation overrides. The Grip workspace reports left/right socket error, hand separation and socket separation, and exposes undoable grip-width plus bar-roll controls. Preserved-source imported characters use the same `twoHandAttachmentMatrix()` from their live left/right hand matrices, so their preview no longer falls back to canonical two-hand placement.\n\nRegression coverage uses a synthetic barbell rather than changing any accepted exercise definition. It proves the raw 80 cm barbell sockets expose their real spacing residual, calibrated socket width lands both contacts within numerical tolerance with a rigid determinant of 1, roll changes orientation without moving either grip contact, and arbitrary imported-character hand matrices use the same solver.\n\n'''
s = replace_once(s, '## Unreleased\n\n', '## Unreleased\n\n\n' + entry, 'two hand changelog')
write(p, s)

print('Applied rigid two-hand socket calibration')
