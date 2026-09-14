from pathlib import Path


def read(path):
    return Path(path).read_text()


def write(path, text):
    Path(path).write_text(text)


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)

# Equipment instances own per-exercise socket overrides; library defaults remain immutable.
p='src/equipment/types.ts'
s=read(p)
s=replace_once(s, "  rotation: Vec3;\n  /**\n   * How the item is bound into the scene.", "  rotation: Vec3;\n  /** Per-exercise local socket calibration. Library defaults remain unchanged. */\n  socketOverrides?: Partial<Record<string, { position?: Vec3; rotation?: Vec3 }>>;\n  /**\n   * How the item is bound into the scene.", 'equipment instance socket overrides')
write(p,s)

p='src/equipment/library.ts'
s=read(p)
s=s.replace("import type { EquipmentDefinition, EquipmentKind, EquipmentSocket } from './types';", "import type { EquipmentDefinition, EquipmentInstance, EquipmentKind, EquipmentSocket } from './types';")
s += """

/** Effective socket for one exercise equipment instance, including local overrides. */
export function equipmentSocketForInstance(
  instance: EquipmentInstance,
  socketId: string,
): EquipmentSocket | null {
  const base = equipmentSocket(instance.kind, socketId);
  if (!base) return null;
  const override = instance.socketOverrides?.[socketId];
  return {
    ...base,
    position: override?.position ? { ...override.position } : { ...base.position },
    ...(override?.rotation
      ? { rotation: { ...override.rotation } }
      : base.rotation
        ? { rotation: { ...base.rotation } }
        : {}),
  };
}
"""
write(p,s)

# Production attachment/socket resolution must consume the instance override.
p='src/equipment/attach.ts'
s=read(p)
s=s.replace("import { equipmentSocket } from './library';", "import { equipmentSocketForInstance } from './library';")
s=s.replace("const socketLocal = equipmentSocket(instance.kind, attachment.socket);", "const socketLocal = equipmentSocketForInstance(instance, attachment.socket);")
s=s.replace("const local = equipmentSocket(instance.kind, socketId);", "const local = equipmentSocketForInstance(instance, socketId);")
write(p,s)

# Imported-character equipment view must use the same effective socket.
p='src/viewer/EquipmentView.tsx'
s=read(p)
s=s.replace("import { equipmentSocket } from '../equipment/library';", "import { equipmentSocketForInstance } from '../equipment/library';")
s=s.replace("const socket = equipmentSocket(instance.kind, instance.attachment.socket);", "const socket = equipmentSocketForInstance(instance, instance.attachment.socket);")
write(p,s)

# Store selection + undoable per-instance socket authoring.
p='src/editor/store.ts'
s=read(p)
s=replace_once(s, "import type { PoseSnapshot } from './comparison';", "import type { PoseSnapshot } from './comparison';\nimport { equipmentSocket } from '../equipment/library';", 'store equipment socket import')
s=replace_once(s, "  equipmentId: string | null;\n}", "  equipmentId: string | null;\n  socketId: string | null;\n}", 'selection socket id')
s=replace_once(s, "  selectEquipment: (id: string | null) => void;\n  setViewMode", "  selectEquipment: (id: string | null) => void;\n  selectSocket: (equipmentId: string, socketId: string | null) => void;\n  setViewMode", 'select socket interface')
s=replace_once(s, "  setEquipmentTransform: (instanceId: string, transform: { position?: Vec3; rotation?: Vec3 }) => void;\n  setLockEnabled", "  setEquipmentTransform: (instanceId: string, transform: { position?: Vec3; rotation?: Vec3 }) => void;\n  setEquipmentSocketTransform: (instanceId: string, socketId: string, transform: { position?: Vec3; rotation?: Vec3 } | null) => void;\n  setLockEnabled", 'socket edit interface')
s=s.replace("selection: { bone: null, handle: null, equipmentId: null },", "selection: { bone: null, handle: null, equipmentId: null, socketId: null },")
s=s.replace("set({ selection: { bone, handle: null, equipmentId: null } })", "set({ selection: { bone, handle: null, equipmentId: null, socketId: null } })")
s=s.replace("set({ selection: { bone: null, handle, equipmentId: null } })", "set({ selection: { bone: null, handle, equipmentId: null, socketId: null } })")
s=s.replace("set({ selection: { bone: null, handle: null, equipmentId } })", "set({ selection: { bone: null, handle: null, equipmentId, socketId: null } })")
s=replace_once(s, "    setViewMode: (viewMode) => set({ viewMode }),", "    selectSocket: (equipmentId, socketId) =>\n      set({ selection: { bone: null, handle: null, equipmentId, socketId } }),\n    setViewMode: (viewMode) => set({ viewMode }),", 'select socket implementation')
insert = """

    setEquipmentSocketTransform: (instanceId, socketId, transform) => {
      const current = get().document.exercise.equipment.instances.find(
        (instance) => instance.id === instanceId,
      );
      // Socket calibration is currently for static equipment. Hand-driven
      // handles remain owned by the Grip workspace to avoid two competing
      // ways of moving the same contact point.
      if (!current || current.attachment.mode !== 'static' || !equipmentSocket(current.kind, socketId)) return;
      commit((document) => {
        const instances = document.exercise.equipment.instances.map((instance) => {
          if (instance.id !== instanceId) return instance;
          const socketOverrides: Partial<Record<string, { position?: Vec3; rotation?: Vec3 }>> = {
            ...(instance.socketOverrides ?? {}),
          };
          if (!transform) {
            delete socketOverrides[socketId];
          } else {
            const previous = socketOverrides[socketId] ?? {};
            socketOverrides[socketId] = {
              ...(transform.position
                ? { position: { ...transform.position } }
                : previous.position
                  ? { position: { ...previous.position } }
                  : {}),
              ...(transform.rotation
                ? { rotation: { ...transform.rotation } }
                : previous.rotation
                  ? { rotation: { ...previous.rotation } }
                  : {}),
            };
          }
          return {
            ...instance,
            socketOverrides: Object.keys(socketOverrides).length > 0 ? socketOverrides : undefined,
          };
        });
        const exercise = {
          ...document.exercise,
          equipment: { ...document.exercise.equipment, instances },
        };
        return { exercise, clip: generateClip(skeleton, exercise) };
      });
    },
"""
s=replace_once(s, "\n    setLockEnabled: (lockId, enabled) =>", insert + "\n    setLockEnabled: (lockId, enabled) =>", 'socket edit implementation')
write(p,s)

# Replace Equipment panel with object + socket authoring UI.
p='src/editor/panels/EquipmentPanel.tsx'
write(p, r'''import { EQUIPMENT_LIBRARY, equipmentSocketForInstance } from '../../equipment/library';
import type { Vec3 } from '../../rig/types';
import { useStudio } from '../store';

const CM = 100;

export function EquipmentPanel() {
  const instances = useStudio((state) => state.document.exercise.equipment.instances);
  const selection = useStudio((state) => state.selection);
  const selectEquipment = useStudio((state) => state.selectEquipment);
  const selectSocket = useStudio((state) => state.selectSocket);
  const setEquipmentTransform = useStudio((state) => state.setEquipmentTransform);
  const setEquipmentSocketTransform = useStudio((state) => state.setEquipmentSocketTransform);

  const selected = instances.find((instance) => instance.id === selection.equipmentId) ?? null;
  const definition = selected ? EQUIPMENT_LIBRARY[selected.kind] : null;
  const selectedSocket =
    selected && selection.socketId ? equipmentSocketForInstance(selected, selection.socketId) : null;

  const setPositionAxis = (axis: keyof Vec3, centimetres: number) => {
    if (!selected) return;
    setEquipmentTransform(selected.id, {
      position: { ...selected.position, [axis]: centimetres / CM },
    });
  };

  const setRotationAxis = (axis: keyof Vec3, degrees: number) => {
    if (!selected) return;
    setEquipmentTransform(selected.id, {
      rotation: { ...selected.rotation, [axis]: degrees },
    });
  };

  const setSocketPositionAxis = (axis: keyof Vec3, centimetres: number) => {
    if (!selected || !selectedSocket) return;
    setEquipmentSocketTransform(selected.id, selectedSocket.id, {
      position: { ...selectedSocket.position, [axis]: centimetres / CM },
    });
  };

  const setSocketRotationAxis = (axis: keyof Vec3, degrees: number) => {
    if (!selected || !selectedSocket) return;
    setEquipmentSocketTransform(selected.id, selectedSocket.id, {
      rotation: { ...(selectedSocket.rotation ?? { x: 0, y: 0, z: 0 }), [axis]: degrees },
    });
  };

  return (
    <section className="panel equipment-panel">
      <h2>Equipment</h2>
      <p className="panel__note">
        Select equipment here or in the viewport. Static equipment and its sockets use the normal
        Studio gizmo and undo history. Hand-driven handle placement stays in Grip.
      </p>

      {instances.length === 0 && <p className="panel__empty">This exercise uses no equipment.</p>}
      <div className="equipment-list">
        {instances.map((instance) => (
          <button
            key={instance.id}
            type="button"
            className={instance.id === selection.equipmentId ? 'is-active' : ''}
            onClick={() => selectEquipment(instance.id)}
          >
            <span>{instance.label ?? EQUIPMENT_LIBRARY[instance.kind].label}</span>
            <small>{instance.attachment.mode}</small>
          </button>
        ))}
      </div>

      {selected && definition && (
        <>
          <h3>{selected.label ?? definition.label}</h3>
          {selected.attachment.mode === 'static' ? (
            <>
              <p className="panel__hint">
                Use Translate / Rotate in the toolbar for the selected object or socket, or enter
                exact values below.
              </p>
              <div className="equipment-transform-grid">
                <strong>Object position</strong>
                {(['x', 'y', 'z'] as const).map((axis) => (
                  <label key={`position-${axis}`} className="field">
                    <span className="field__label">{axis.toUpperCase()} · cm</span>
                    <input
                      type="number"
                      step={1}
                      value={Number((selected.position[axis] * CM).toFixed(1))}
                      onChange={(event) => setPositionAxis(axis, Number(event.target.value))}
                    />
                  </label>
                ))}
                <strong>Object rotation</strong>
                {(['x', 'y', 'z'] as const).map((axis) => (
                  <label key={`rotation-${axis}`} className="field">
                    <span className="field__label">{axis.toUpperCase()} · °</span>
                    <input
                      type="number"
                      step={1}
                      value={Number(selected.rotation[axis].toFixed(1))}
                      onChange={(event) => setRotationAxis(axis, Number(event.target.value))}
                    />
                  </label>
                ))}
              </div>
            </>
          ) : (
            <p className="panel__note">
              This object is driven by {selected.attachment.mode === 'hand' ? 'one hand' : 'both hands'}.
              World position/rotation and socket calibration are intentionally owned by Grip/attachment.
            </p>
          )}

          <h3>Sockets</h3>
          <div className="equipment-sockets">
            {definition.sockets.map((base) => {
              const socket = equipmentSocketForInstance(selected, base.id)!;
              const active = selection.socketId === socket.id;
              return (
                <button
                  key={socket.id}
                  type="button"
                  className={`equipment-socket ${active ? 'is-active' : ''}`}
                  onClick={() =>
                    selected.attachment.mode === 'static'
                      ? selectSocket(selected.id, active ? null : socket.id)
                      : undefined
                  }
                >
                  <div>
                    <strong>{socket.label}</strong>
                    <span>{socket.kind}</span>
                  </div>
                  <code>
                    {(socket.position.x * CM).toFixed(1)}, {(socket.position.y * CM).toFixed(1)},{' '}
                    {(socket.position.z * CM).toFixed(1)} cm
                  </code>
                </button>
              );
            })}
          </div>

          {selected.attachment.mode === 'static' && selectedSocket && (
            <div className="socket-editor">
              <div className="socket-editor__head">
                <strong>{selectedSocket.label}</strong>
                <button
                  type="button"
                  onClick={() => setEquipmentSocketTransform(selected.id, selectedSocket.id, null)}
                >
                  Reset socket
                </button>
              </div>
              <div className="equipment-transform-grid">
                <strong>Socket local position</strong>
                {(['x', 'y', 'z'] as const).map((axis) => (
                  <label key={`socket-position-${axis}`} className="field">
                    <span className="field__label">{axis.toUpperCase()} · cm</span>
                    <input
                      type="number"
                      step={0.5}
                      value={Number((selectedSocket.position[axis] * CM).toFixed(1))}
                      onChange={(event) => setSocketPositionAxis(axis, Number(event.target.value))}
                    />
                  </label>
                ))}
                <strong>Socket local rotation</strong>
                {(['x', 'y', 'z'] as const).map((axis) => (
                  <label key={`socket-rotation-${axis}`} className="field">
                    <span className="field__label">{axis.toUpperCase()} · °</span>
                    <input
                      type="number"
                      step={1}
                      value={Number((selectedSocket.rotation?.[axis] ?? 0).toFixed(1))}
                      onChange={(event) => setSocketRotationAxis(axis, Number(event.target.value))}
                    />
                  </label>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {!selected && instances.length > 0 && (
        <p className="panel__empty">Select an equipment object to inspect its transform and sockets.</p>
      )}
    </section>
  );
}
''')

# Extend the existing transform gizmo to selected static sockets.
p='src/viewer/Viewport.tsx'
s=read(p)
s=s.replace("import { Euler, Object3D, Quaternion, Vector3 } from 'three';", "import { Euler, Matrix4, Object3D, Quaternion, Vector3 } from 'three';")
s=replace_once(s, "import { advancePlaybackTime } from '../editor/playback';", "import { advancePlaybackTime } from '../editor/playback';\nimport { equipmentSocketForInstance } from '../equipment/library';", 'viewport socket import')
s=replace_once(s, "  const setEquipmentTransform = useStudio((state) => state.setEquipmentTransform);", "  const setEquipmentTransform = useStudio((state) => state.setEquipmentTransform);\n  const setEquipmentSocketTransform = useStudio((state) => state.setEquipmentSocketTransform);", 'viewport socket setter')
s=replace_once(s, "  const [proxy] = useState(() => new Object3D());\n  const dragging", "  const [proxy] = useState(() => new Object3D());\n  const socketScratch = useMemo(() => ({\n    local: new Matrix4(),\n    world: new Matrix4(),\n    inverse: new Matrix4(),\n    position: new Vector3(),\n    quaternion: new Quaternion(),\n    scale: new Vector3(),\n  }), []);\n  const dragging", 'socket gizmo scratch')
s=replace_once(s, "  const editableEquipment = selectedEquipment?.attachment.mode === 'static' ? selectedEquipment : null;", "  const editableEquipment = selectedEquipment?.attachment.mode === 'static' ? selectedEquipment : null;\n  const selectedSocket =\n    editableEquipment && selection.socketId\n      ? equipmentSocketForInstance(editableEquipment, selection.socketId)\n      : null;", 'selected socket')
s=replace_once(s, "    if (editableEquipment) {\n      const transform = scene.frame?.equipment.get(editableEquipment.id);\n      if (!transform) return;\n      proxy.position.copy(transform.position);\n      proxy.quaternion.copy(transform.quaternion);\n    }", "    if (editableEquipment) {\n      const transform = scene.frame?.equipment.get(editableEquipment.id);\n      if (!transform) return;\n      if (selectedSocket) {\n        socketScratch.local.compose(\n          socketScratch.position.set(selectedSocket.position.x, selectedSocket.position.y, selectedSocket.position.z),\n          socketScratch.quaternion.setFromEuler(\n            new Euler(\n              (selectedSocket.rotation?.x ?? 0) * Math.PI / 180,\n              (selectedSocket.rotation?.y ?? 0) * Math.PI / 180,\n              (selectedSocket.rotation?.z ?? 0) * Math.PI / 180,\n              EULER_ORDER,\n            ),\n          ),\n          socketScratch.scale.set(1, 1, 1),\n        );\n        socketScratch.world.multiplyMatrices(transform.matrix, socketScratch.local);\n        socketScratch.world.decompose(proxy.position, proxy.quaternion, socketScratch.scale);\n        return;\n      }\n      proxy.position.copy(transform.position);\n      proxy.quaternion.copy(transform.quaternion);\n    }", 'socket gizmo placement')
s=s.replace("const target = selection.bone || editableEquipment ? proxy : null;", "const target = selection.bone || editableEquipment ? proxy : null;")
old = """        const equipmentId = state.selection.equipmentId;
        if (!equipmentId || !editableEquipment || editableEquipment.id !== equipmentId) return;
        if (gizmoMode === 'translate') {
          setEquipmentTransform(equipmentId, {
            position: { x: proxy.position.x, y: proxy.position.y, z: proxy.position.z },
          });
          return;
        }
        const euler = new Euler().setFromQuaternion(proxy.quaternion, EULER_ORDER);
        setEquipmentTransform(equipmentId, {
          rotation: { x: toDeg(euler.x), y: toDeg(euler.y), z: toDeg(euler.z) },
        });
"""
new = """        const equipmentId = state.selection.equipmentId;
        if (!equipmentId || !editableEquipment || editableEquipment.id !== equipmentId) return;
        const socketId = state.selection.socketId;
        if (socketId && selectedSocket) {
          const transform = scene.frame?.equipment.get(equipmentId);
          if (!transform) return;
          proxy.updateMatrix();
          socketScratch.inverse.copy(transform.matrix).invert();
          socketScratch.local.multiplyMatrices(socketScratch.inverse, proxy.matrix);
          socketScratch.local.decompose(
            socketScratch.position,
            socketScratch.quaternion,
            socketScratch.scale,
          );
          const euler = new Euler().setFromQuaternion(socketScratch.quaternion, EULER_ORDER);
          setEquipmentSocketTransform(equipmentId, socketId, {
            position: {
              x: socketScratch.position.x,
              y: socketScratch.position.y,
              z: socketScratch.position.z,
            },
            rotation: { x: toDeg(euler.x), y: toDeg(euler.y), z: toDeg(euler.z) },
          });
          return;
        }
        if (gizmoMode === 'translate') {
          setEquipmentTransform(equipmentId, {
            position: { x: proxy.position.x, y: proxy.position.y, z: proxy.position.z },
          });
          return;
        }
        const euler = new Euler().setFromQuaternion(proxy.quaternion, EULER_ORDER);
        setEquipmentTransform(equipmentId, {
          rotation: { x: toDeg(euler.x), y: toDeg(euler.y), z: toDeg(euler.z) },
        });
"""
s=replace_once(s, old, new, 'socket gizmo edit')
write(p,s)

# Tests: instance-local override changes real pull-up contact; reset/undo; hand-driven reject.
p='src/editor/store.test.ts'
s=read(p)
s += r'''


describe('equipment socket authoring', () => {
  it('moves a static rack socket through the production contact resolver and undo', () => {
    useStudio.getState().loadExercise('pull_up');
    const before = useStudio.getState().document;
    const originalClip = before.clip;
    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const originalFrame = resolveFrame(canonicalSkeleton, evaluation, originalClip, 0);
    const originalTarget = originalFrame.contacts.find((contact) => contact.chain === 'arm_l')!.target.x;

    useStudio.getState().setEquipmentSocketTransform('rack', 'pullup_l', {
      position: { x: -0.30, y: 1.97, z: 0 },
      rotation: { x: 0, y: 90, z: 0 },
    });

    const edited = useStudio.getState();
    const rack = edited.document.exercise.equipment.instances.find((instance) => instance.id === 'rack')!;
    expect(rack.socketOverrides?.pullup_l?.position).toEqual({ x: -0.30, y: 1.97, z: 0 });
    const frame = resolveFrame(canonicalSkeleton, new PoseEvaluation(canonicalSkeleton), edited.document.clip, 0);
    const target = frame.contacts.find((contact) => contact.chain === 'arm_l')!.target.x;
    expect(target).toBeCloseTo(-0.30, 8);
    expect(target).not.toBeCloseTo(originalTarget, 4);

    edited.undo();
    const restored = useStudio.getState().document.exercise.equipment.instances.find(
      (instance) => instance.id === 'rack',
    )!;
    expect(restored.socketOverrides).toBeUndefined();
  });

  it('resets an instance socket to its library default without touching the global definition', () => {
    useStudio.getState().loadExercise('pull_up');
    useStudio.getState().setEquipmentSocketTransform('rack', 'pullup_l', {
      position: { x: -0.31, y: 1.96, z: 0.01 },
    });
    useStudio.getState().setEquipmentSocketTransform('rack', 'pullup_l', null);
    const rack = useStudio.getState().document.exercise.equipment.instances.find(
      (instance) => instance.id === 'rack',
    )!;
    expect(rack.socketOverrides).toBeUndefined();
  });

  it('keeps hand-driven handle calibration owned by the Grip workspace', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    const before = useStudio.getState().document;
    const historyCount = useStudio.getState().history.past.length;
    useStudio.getState().setEquipmentSocketTransform('dumbbell_l', 'grip', {
      position: { x: 1, y: 1, z: 1 },
    });
    expect(useStudio.getState().document).toBe(before);
    expect(useStudio.getState().history.past.length).toBe(historyCount);
  });
});
'''
write(p,s)

# Styling for selectable sockets and local editor.
p='src/editor/styles.css'
s=read(p)
s += r'''

.equipment-socket {
  width: 100%;
  text-align: left;
}

.equipment-socket.is-active {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent) inset;
}

.socket-editor {
  margin-top: 9px;
  padding-top: 9px;
  border-top: 1px solid var(--line);
}

.socket-editor__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 7px;
}
'''
write(p,s)

# Roadmap + Claude handoff.
p='docs/STUDIO_CAPABILITY_ROADMAP.md'
s=read(p)
s=replace_once(s, "- Hand-driven equipment rejects world-transform authoring because its attachment solver owns that transform; hand placement remains in the Grip workspace. Equipment socket inventory is visible per selected object.", "- Hand-driven equipment rejects world-transform authoring because its attachment solver owns that transform; hand placement remains in the Grip workspace.\n- Static equipment sockets are individually selectable and can be translated/rotated in equipment-local space through exact controls or the viewport gizmo. Overrides are per exercise instance and reset cleanly to immutable library defaults.", 'roadmap socket authoring')
write(p,s)

p='AI_CHANGELOG.md'
s=read(p)
entry='''### ChatGPT — 2026-09-14 — per-instance equipment socket authoring\n\nAdded direct socket-level authoring for **static equipment**. Equipment instances can now carry local `socketOverrides` without mutating `EQUIPMENT_LIBRARY`; `equipmentSocketForInstance` resolves the effective socket and the production attachment/contact resolver uses that effective value. Selecting a static socket in the Equipment workspace moves the existing Studio transform gizmo onto the socket. Translate/Rotate edits are converted back into equipment-local position/rotation, regenerate the deterministic clip, and participate in normal undo/redo history. Exact local position/rotation inputs and `Reset socket` are available alongside the gizmo.\n\nThe scope is deliberately guarded: hand- and two-hand-driven equipment reject socket authoring so handle placement continues to have one owner, the Grip/attachment workspace. This prevents competing edits between a moving hand socket and grip-centre calibration. Regressions verify that moving the pull-up rack's left grip socket changes the real production contact target, undo restores the original socket, reset removes the per-instance override, and a dumbbell socket edit creates no document/history change.\n\n'''
s=replace_once(s, '## Unreleased\n\n', '## Unreleased\n\n\n'+entry, 'changelog entry')
write(p,s)

print('Applied per-instance static equipment socket authoring')
