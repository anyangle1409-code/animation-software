from pathlib import Path

def read(path): return Path(path).read_text()
def write(path,text): Path(path).write_text(text)
def replace_once(text,old,new,label):
    if old not in text: raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old,new,1)

# One-hand attachments can calibrate equipment orientation in the hand frame.
p='src/equipment/types.ts'
s=read(p)
s=replace_once(s, "      /** Offset of the grip within the hand, in the hand bone's local frame. */\n      gripOffset?: Vec3;", "      /** Offset of the grip within the hand, in the hand bone's local frame. */\n      gripOffset?: Vec3;\n      /** Equipment orientation relative to the hand grip frame, Euler degrees. */\n      gripRotation?: Vec3;", 'grip rotation type')
write(p,s)

# Production one-hand resolver: hand * grip transform * inverse(equipment socket transform).
p='src/equipment/attach.ts'
s=read(p)
old='''    const matrix = new Matrix4()
      .copy(evaluation.matrix(hand))
      .multiply(new Matrix4().makeTranslation(grip.x, grip.y, grip.z));
    // The socket sits at the grip, so the item's own origin is offset back by it.
    const socketLocal = equipmentSocketForInstance(instance, attachment.socket);
    if (socketLocal) {
      matrix.multiply(
        new Matrix4().makeTranslation(
          -socketLocal.position.x,
          -socketLocal.position.y,
          -socketLocal.position.z,
        ),
      );
    }
    return decompose(instance.id, matrix);'''
new='''    const gripQuaternion = new Quaternion().setFromEuler(
      new Euler(
        toRad(attachment.gripRotation?.x ?? 0),
        toRad(attachment.gripRotation?.y ?? 0),
        toRad(attachment.gripRotation?.z ?? 0),
        EULER_ORDER,
      ),
    );
    const gripMatrix = new Matrix4().compose(
      new Vector3(grip.x, grip.y, grip.z),
      gripQuaternion,
      UNIT,
    );
    const matrix = new Matrix4().copy(evaluation.matrix(hand)).multiply(gripMatrix);
    // The equipment socket itself — position and orientation — is what meets
    // the calibrated hand frame. Inverting the full socket transform keeps the
    // contact point fixed while allowing the handle to rotate in the palm.
    const socketLocal = equipmentSocketForInstance(instance, attachment.socket);
    if (socketLocal) {
      const socketMatrix = new Matrix4().compose(
        new Vector3(socketLocal.position.x, socketLocal.position.y, socketLocal.position.z),
        new Quaternion().setFromEuler(
          new Euler(
            toRad(socketLocal.rotation?.x ?? 0),
            toRad(socketLocal.rotation?.y ?? 0),
            toRad(socketLocal.rotation?.z ?? 0),
            EULER_ORDER,
          ),
        ),
        UNIT,
      );
      matrix.multiply(socketMatrix.invert());
    }
    return decompose(instance.id, matrix);'''
s=replace_once(s,old,new,'one hand grip orientation resolve')
write(p,s)

# Export/imported-character helper supports the same transform without breaking existing callers.
p='src/export/clipBuilder.ts'
s=read(p)
s=replace_once(s, "import type { StudioClip } from '../animation/clip';", "import type { StudioClip } from '../animation/clip';\nimport type { Vec3 } from '../rig/types';\nimport { toRad } from '../core/math';", 'clipBuilder grip orientation imports')
old='''export function handAttachmentMatrix(
  grip: { x: number; y: number; z: number },
  socket: { x: number; y: number; z: number },
): Matrix4 {
  return new Matrix4()
    .makeTranslation(grip.x, grip.y, grip.z)
    .multiply(new Matrix4().makeTranslation(-socket.x, -socket.y, -socket.z));
}'''
new='''export function handAttachmentMatrix(
  grip: { x: number; y: number; z: number },
  socket: { x: number; y: number; z: number },
  options: { gripRotation?: Vec3; socketRotation?: Vec3 } = {},
): Matrix4 {
  const gripRotation = options.gripRotation ?? { x: 0, y: 0, z: 0 };
  const socketRotation = options.socketRotation ?? { x: 0, y: 0, z: 0 };
  const gripMatrix = new Matrix4().compose(
    new Vector3(grip.x, grip.y, grip.z),
    new Quaternion().setFromEuler(
      new Euler(toRad(gripRotation.x), toRad(gripRotation.y), toRad(gripRotation.z), EULER_ORDER),
    ),
    new Vector3(1, 1, 1),
  );
  const socketMatrix = new Matrix4().compose(
    new Vector3(socket.x, socket.y, socket.z),
    new Quaternion().setFromEuler(
      new Euler(toRad(socketRotation.x), toRad(socketRotation.y), toRad(socketRotation.z), EULER_ORDER),
    ),
    new Vector3(1, 1, 1),
  );
  return gripMatrix.multiply(socketMatrix.invert());
}'''
s=replace_once(s,old,new,'hand attachment helper orientation')
write(p,s)

# Imported preserved-skeleton viewport uses identical local calibration.
p='src/viewer/EquipmentView.tsx'
s=read(p)
old="scratch.local.copy(handAttachmentMatrix(grip, socket?.position ?? { x: 0, y: 0, z: 0 }));"
new="scratch.local.copy(handAttachmentMatrix(\n          grip,\n          socket?.position ?? { x: 0, y: 0, z: 0 },\n          { gripRotation: instance.attachment.gripRotation, socketRotation: socket?.rotation },\n        ));"
s=replace_once(s,old,new,'imported equipment grip orientation')
write(p,s)

# Store authoring.
p='src/editor/store.ts'
s=read(p)
s=replace_once(s, "  setEquipmentGripOffset: (instanceId: string, offset: Vec3 | null) => void;", "  setEquipmentGripOffset: (instanceId: string, offset: Vec3 | null) => void;\n  setEquipmentGripRotation: (instanceId: string, rotation: Vec3 | null) => void;", 'grip rotation store interface')
insert='''

    setEquipmentGripRotation: (instanceId, rotation) =>
      commit((document) => {
        const instances = document.exercise.equipment.instances.map((instance) => {
          if (instance.id !== instanceId || instance.attachment.mode !== 'hand') return instance;
          if (rotation) {
            return {
              ...instance,
              attachment: { ...instance.attachment, gripRotation: { ...rotation } },
            };
          }
          const { gripRotation: _gripRotation, ...attachment } = instance.attachment;
          return { ...instance, attachment };
        });
        const exercise = {
          ...document.exercise,
          equipment: { ...document.exercise.equipment, instances },
        };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),
'''
s=replace_once(s, "\n    setEquipmentTransform: (instanceId, transform) =>", insert+"\n    setEquipmentTransform: (instanceId, transform) =>", 'grip rotation store implementation')
write(p,s)

# Grip panel exact orientation controls.
p='src/editor/panels/GripPanel.tsx'
s=read(p)
s=replace_once(s, "  const setEquipmentGripOffset = useStudio((state) => state.setEquipmentGripOffset);", "  const setEquipmentGripOffset = useStudio((state) => state.setEquipmentGripOffset);\n  const setEquipmentGripRotation = useStudio((state) => state.setEquipmentGripRotation);", 'GripPanel rotation setter')
s=s.replace("        isCustomOffset: Boolean(instance.attachment.gripOffset),", "        isCustomOffset: Boolean(instance.attachment.gripOffset),\n        rotation: instance.attachment.gripRotation ?? { x: 0, y: 0, z: 0 },\n        isCustomRotation: Boolean(instance.attachment.gripRotation),")
s=replace_once(s, "  const updateOffset = (id: string, current: Vec3, axis: keyof Vec3, millimetres: number) => {\n    setEquipmentGripOffset(id, { ...current, [axis]: millimetres / 1000 });\n  };", "  const updateOffset = (id: string, current: Vec3, axis: keyof Vec3, millimetres: number) => {\n    setEquipmentGripOffset(id, { ...current, [axis]: millimetres / 1000 });\n  };\n\n  const updateRotation = (id: string, current: Vec3, axis: keyof Vec3, degrees: number) => {\n    setEquipmentGripRotation(id, { ...current, [axis]: degrees });\n  };", 'GripPanel rotation helper')
s=s.replace("{measurements.map(({ id, label, offset, isCustomOffset, fit }) => (", "{measurements.map(({ id, label, offset, isCustomOffset, rotation, isCustomRotation, fit }) => (")
needle='''              <div className="button-row">
                <button
                  type="button"
                  disabled={!isCustomOffset}
                  onClick={() => setEquipmentGripOffset(id, null)}
                >
                  Reset anatomical centre
                </button>
              </div>'''
replacement='''              <h4>Handle orientation</h4>
              <div className="grip-offset-grid">
                {(['x', 'y', 'z'] as const).map((axis) => (
                  <label className="field" key={`rotation-${axis}`}>
                    <span className="field__label">Grip {axis.toUpperCase()} · °</span>
                    <input
                      type="number"
                      step={1}
                      value={Number(rotation[axis].toFixed(1))}
                      onChange={(event) => updateRotation(id, rotation, axis, Number(event.target.value))}
                    />
                  </label>
                ))}
              </div>
              <div className="button-row">
                <button
                  type="button"
                  disabled={!isCustomOffset}
                  onClick={() => setEquipmentGripOffset(id, null)}
                >
                  Reset anatomical centre
                </button>
                <button
                  type="button"
                  disabled={!isCustomRotation}
                  onClick={() => setEquipmentGripRotation(id, null)}
                >
                  Reset orientation
                </button>
              </div>'''
s=replace_once(s,needle,replacement,'GripPanel orientation UI')
s=s.replace("Grip X/Y/Z is the handle centre in hand-local millimetres.", "Grip X/Y/Z is the handle centre in hand-local millimetres; orientation is a hand-local Euler calibration in degrees.")
write(p,s)

# Store + production geometry tests.
p='src/editor/store.test.ts'
s=read(p)
s += r'''


describe('hand-local grip orientation calibration', () => {
  it('rotates a dumbbell in the hand without moving its grip centre and is undoable', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    const before = useStudio.getState().document;
    const custom = { x: 8, y: -4, z: 12 };
    useStudio.getState().setEquipmentGripRotation('dumbbell_l', custom);
    const state = useStudio.getState();
    const instance = state.document.exercise.equipment.instances.find((entry) => entry.id === 'dumbbell_l')!;
    if (instance.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(instance.attachment.gripRotation).toEqual(custom);

    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const frame = resolveFrame(canonicalSkeleton, evaluation, state.document.clip, 0);
    evaluation.apply(frame.pose);
    const expected = evaluation.localToWorld('hand_l', { x: -0.025, y: 0.085, z: 0 }, new Vector3());
    expect(frame.equipment.get('dumbbell_l')!.position.distanceTo(expected)).toBeLessThan(1e-9);

    state.undo();
    expect(useStudio.getState().document).toBe(before);
  });

  it('can reset orientation independently of the calibrated grip centre', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    useStudio.getState().setEquipmentGripOffset('dumbbell_l', { x: -0.02, y: 0.08, z: 0.004 });
    useStudio.getState().setEquipmentGripRotation('dumbbell_l', { x: 0, y: 10, z: 0 });
    useStudio.getState().setEquipmentGripRotation('dumbbell_l', null);
    const instance = useStudio.getState().document.exercise.equipment.instances.find((entry) => entry.id === 'dumbbell_l')!;
    if (instance.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(instance.attachment.gripRotation).toBeUndefined();
    expect(instance.attachment.gripOffset).toEqual({ x: -0.02, y: 0.08, z: 0.004 });
  });
});
'''
write(p,s)

p='docs/STUDIO_CAPABILITY_ROADMAP.md'
s=read(p)
needle='- Per-instance hand-local grip-centre calibration edits handle X/Y/Z in millimetres, updates diagnostics live, and can reset to the anatomical default.'
s=replace_once(s,needle,needle+'\n- Per-instance hand-local grip orientation calibration rotates one-hand equipment around the same socket/contact centre without twisting wrist/arm animation; position and orientation reset independently.', 'roadmap grip orientation')
write(p,s)

p='AI_CHANGELOG.md'
s=read(p)
entry='''### ChatGPT — 2026-09-14 — hand-local grip orientation calibration\n\nExtended one-hand equipment attachments with optional `gripRotation` Euler degrees. Production placement is now `hand frame × calibrated grip transform × inverse equipment socket transform`, so the equipment socket remains pinned to the exact same hand-local grip centre while the handle can rotate inside the palm. The full socket transform includes socket orientation as well as position, improving future non-zero-angle handles while preserving the current zero-rotation dumbbell baseline. The preserved-source-skeleton `EquipmentView` uses the same transform through the extended `handAttachmentMatrix`, so imported-character preview and export/runtime placement agree.\n\nThe Grip workspace now exposes exact X/Y/Z orientation degrees per one-hand equipment instance plus independent `Reset orientation`; centre calibration and orientation reset do not erase each other. `setEquipmentGripRotation` regenerates through normal document history and is undoable. Regressions verify a rotated dumbbell keeps its socket/grip centre exactly fixed in world space, undo restores the original document, and resetting orientation leaves a custom grip centre intact. This calibration changes equipment placement only; it never twists the wrist, elbow, shoulder or finger animation to compensate.\n\n'''
s=replace_once(s,'## Unreleased\n\n','## Unreleased\n\n\n'+entry,'grip orientation changelog')
write(p,s)

print('Applied hand-local grip orientation calibration')
