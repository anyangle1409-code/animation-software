from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected one match, found {count}: {old[:140]!r}')
    file.write_text(text.replace(old, new, 1), encoding='utf-8')


# Store: static world equipment can be positioned/rotated through normal history.
replace_once(
    'src/editor/store.ts',
    "  setEquipmentGripOffset: (instanceId: string, offset: Vec3 | null) => void;\n  setLockEnabled: (lockId: string, enabled: boolean) => void;",
    "  setEquipmentGripOffset: (instanceId: string, offset: Vec3 | null) => void;\n  setEquipmentTransform: (instanceId: string, transform: { position?: Vec3; rotation?: Vec3 }) => void;\n  setLockEnabled: (lockId: string, enabled: boolean) => void;",
)
replace_once(
    'src/editor/store.ts',
    "    setLockEnabled: (lockId, enabled) =>\n      editClip((clip) => ({",
    "    setEquipmentTransform: (instanceId, transform) => {\n      const current = get().document.exercise.equipment.instances.find(\n        (instance) => instance.id === instanceId,\n      );\n      // Hand-driven equipment belongs to the grip/attachment system. A world\n      // transform edit would be overwritten by the next resolved frame, so do\n      // not create a misleading undo step for it.\n      if (!current || current.attachment.mode !== 'static') return;\n      commit((document) => {\n        const instances = document.exercise.equipment.instances.map((instance) =>\n          instance.id === instanceId\n            ? {\n                ...instance,\n                position: transform.position ? { ...transform.position } : { ...instance.position },\n                rotation: transform.rotation ? { ...transform.rotation } : { ...instance.rotation },\n              }\n            : instance,\n        );\n        const exercise = {\n          ...document.exercise,\n          equipment: { ...document.exercise.equipment, instances },\n        };\n        return { exercise, clip: generateClip(skeleton, exercise) };\n      });\n    },\n\n    setLockEnabled: (lockId, enabled) =>\n      editClip((clip) => ({",
)

# Dedicated equipment panel: object selection, exact transform and socket inventory.
Path('src/editor/panels/EquipmentPanel.tsx').write_text(r'''import { EQUIPMENT_LIBRARY } from '../../equipment/library';
import type { Vec3 } from '../../rig/types';
import { useStudio } from '../store';

const CM = 100;

export function EquipmentPanel() {
  const instances = useStudio((state) => state.document.exercise.equipment.instances);
  const selectedId = useStudio((state) => state.selection.equipmentId);
  const selectEquipment = useStudio((state) => state.selectEquipment);
  const setEquipmentTransform = useStudio((state) => state.setEquipmentTransform);

  const selected = instances.find((instance) => instance.id === selectedId) ?? null;
  const definition = selected ? EQUIPMENT_LIBRARY[selected.kind] : null;

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

  return (
    <section className="panel equipment-panel">
      <h2>Equipment</h2>
      <p className="panel__note">
        Select equipment here or in the viewport. Static objects use the normal Studio transform
        gizmo and undo history; hand-driven equipment stays owned by the Grip workspace.
      </p>

      {instances.length === 0 && <p className="panel__empty">This exercise uses no equipment.</p>}
      <div className="equipment-list">
        {instances.map((instance) => (
          <button
            key={instance.id}
            type="button"
            className={instance.id === selectedId ? 'is-active' : ''}
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
                Use Translate / Rotate in the toolbar for the viewport gizmo, or enter exact values
                below. Position is shown in centimetres; rotation is degrees.
              </p>
              <div className="equipment-transform-grid">
                <strong>Position</strong>
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
                <strong>Rotation</strong>
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
              World position/rotation is intentionally locked because the attachment solver owns it.
            </p>
          )}

          <h3>Sockets</h3>
          <div className="equipment-sockets">
            {definition.sockets.map((socket) => (
              <div key={socket.id} className="equipment-socket">
                <div>
                  <strong>{socket.label}</strong>
                  <span>{socket.kind}</span>
                </div>
                <code>
                  {socket.position.x.toFixed(2)}, {socket.position.y.toFixed(2)},{' '}
                  {socket.position.z.toFixed(2)} m
                </code>
              </div>
            ))}
          </div>
        </>
      )}

      {!selected && instances.length > 0 && (
        <p className="panel__empty">Select an equipment object to inspect its transform and sockets.</p>
      )}
    </section>
  );
}
''', encoding='utf-8')

# App tab.
replace_once(
    'src/editor/App.tsx',
    "import { ContactPanel } from './panels/ContactPanel';",
    "import { ContactPanel } from './panels/ContactPanel';\nimport { EquipmentPanel } from './panels/EquipmentPanel';",
)
replace_once(
    'src/editor/App.tsx',
    "type LeftTab = 'joint' | 'grip' | 'ik' | 'contacts' | 'character';",
    "type LeftTab = 'joint' | 'grip' | 'ik' | 'contacts' | 'equipment' | 'character';",
)
replace_once(
    'src/editor/App.tsx',
    "            <button\n              type=\"button\"\n              className={leftTab === 'character' ? 'is-active' : ''}\n              onClick={() => setLeftTab('character')}\n            >\n              Character\n            </button>",
    "            <button\n              type=\"button\"\n              className={leftTab === 'equipment' ? 'is-active' : ''}\n              onClick={() => setLeftTab('equipment')}\n            >\n              Equipment\n            </button>\n            <button\n              type=\"button\"\n              className={leftTab === 'character' ? 'is-active' : ''}\n              onClick={() => setLeftTab('character')}\n            >\n              Character\n            </button>",
)
replace_once(
    'src/editor/App.tsx',
    "            {leftTab === 'contacts' && <ContactPanel />}\n            {leftTab === 'character' && <CharacterPanel />}",
    "            {leftTab === 'contacts' && <ContactPanel />}\n            {leftTab === 'equipment' && <EquipmentPanel />}\n            {leftTab === 'character' && <CharacterPanel />}",
)

# Viewport gizmo: use selected static equipment as an alternate transform target.
replace_once(
    'src/viewer/Viewport.tsx',
    "import { clampRotation } from '../rig/pose';",
    "import { clampRotation } from '../rig/pose';\nimport { toDeg } from '../core/math';",
)
replace_once(
    'src/viewer/Viewport.tsx',
    "  const setBoneRotation = useStudio((state) => state.setBoneRotation);",
    "  const setBoneRotation = useStudio((state) => state.setBoneRotation);\n  const setEquipmentTransform = useStudio((state) => state.setEquipmentTransform);\n  const equipment = useStudio((state) => state.document.clip.equipment);",
)
replace_once(
    'src/viewer/Viewport.tsx',
    "  useFrame(() => {\n    if (dragging.current) return;\n    if (!selection.bone) return;\n    proxy.position.copy(scene.evaluation.head(selection.bone, new Vector3()));\n    proxy.quaternion.copy(scene.evaluation.quaternion(selection.bone));\n  });\n\n  const target = selection.bone ? proxy : null;",
    "  const selectedEquipment = selection.equipmentId\n    ? equipment.find((instance) => instance.id === selection.equipmentId) ?? null\n    : null;\n  const editableEquipment = selectedEquipment?.attachment.mode === 'static' ? selectedEquipment : null;\n\n  useFrame(() => {\n    if (dragging.current) return;\n    if (selection.bone) {\n      proxy.position.copy(scene.evaluation.head(selection.bone, new Vector3()));\n      proxy.quaternion.copy(scene.evaluation.quaternion(selection.bone));\n      return;\n    }\n    if (editableEquipment) {\n      const transform = scene.frame?.equipment.get(editableEquipment.id);\n      if (!transform) return;\n      proxy.position.copy(transform.position);\n      proxy.quaternion.copy(transform.quaternion);\n    }\n  });\n\n  const target = selection.bone || editableEquipment ? proxy : null;",
)
replace_once(
    'src/viewer/Viewport.tsx',
    "        const bone = useStudio.getState().selection.bone;\n        if (!bone) return;\n        if (gizmoMode === 'translate') {\n          // Translating a joint is meaningless on a fixed-length skeleton; the\n          // gizmo drives IK targets instead, handled below.\n          return;\n        }\n        const rest = restWorldQuaternion(skeleton, scene.evaluation, bone, new Quaternion());\n        const local = rest.clone().invert().multiply(proxy.quaternion);\n        const euler = new Euler().setFromQuaternion(local, EULER_ORDER);\n        setBoneRotation(\n          bone,\n          clampRotation(skeleton.bone(bone), { x: euler.x, y: euler.y, z: euler.z }),\n        );",
    "        const state = useStudio.getState();\n        const bone = state.selection.bone;\n        if (bone) {\n          if (gizmoMode === 'translate') {\n            // Translating a joint is meaningless on a fixed-length skeleton; the\n            // gizmo drives IK targets instead, handled below.\n            return;\n          }\n          const rest = restWorldQuaternion(skeleton, scene.evaluation, bone, new Quaternion());\n          const local = rest.clone().invert().multiply(proxy.quaternion);\n          const euler = new Euler().setFromQuaternion(local, EULER_ORDER);\n          setBoneRotation(\n            bone,\n            clampRotation(skeleton.bone(bone), { x: euler.x, y: euler.y, z: euler.z }),\n          );\n          return;\n        }\n\n        const equipmentId = state.selection.equipmentId;\n        if (!equipmentId || !editableEquipment || editableEquipment.id !== equipmentId) return;\n        if (gizmoMode === 'translate') {\n          setEquipmentTransform(equipmentId, {\n            position: { x: proxy.position.x, y: proxy.position.y, z: proxy.position.z },\n          });\n          return;\n        }\n        const euler = new Euler().setFromQuaternion(proxy.quaternion, EULER_ORDER);\n        setEquipmentTransform(equipmentId, {\n          rotation: { x: toDeg(euler.x), y: toDeg(euler.y), z: toDeg(euler.z) },\n        });",
)

# Store regressions.
store_test = Path('src/editor/store.test.ts')
text = store_test.read_text(encoding='utf-8')
text += r'''

describe('static equipment authoring', () => {
  it('moves static equipment through normal document history and undo', () => {
    useStudio.getState().loadExercise('pull_up');
    const before = useStudio.getState().document;
    const beforeRack = before.exercise.equipment.instances.find((instance) => instance.id === 'rack')!;

    useStudio.getState().setEquipmentTransform('rack', {
      position: { x: 0.12, y: 0.04, z: -0.08 },
      rotation: { x: 0, y: 7, z: 0 },
    });

    const edited = useStudio.getState();
    const rack = edited.document.exercise.equipment.instances.find((instance) => instance.id === 'rack')!;
    const clipRack = edited.document.clip.equipment.find((instance) => instance.id === 'rack')!;
    expect(rack.position).toEqual({ x: 0.12, y: 0.04, z: -0.08 });
    expect(rack.rotation).toEqual({ x: 0, y: 7, z: 0 });
    expect(clipRack.position).toEqual(rack.position);
    expect(clipRack.rotation).toEqual(rack.rotation);
    expect(edited.history.past.at(-1)).toBe(before);

    edited.undo();
    const restored = useStudio.getState().document.exercise.equipment.instances.find(
      (instance) => instance.id === 'rack',
    )!;
    expect(restored.position).toEqual(beforeRack.position);
    expect(restored.rotation).toEqual(beforeRack.rotation);
  });

  it('refuses misleading world-transform edits on hand-driven equipment', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    const before = useStudio.getState().document;
    const historyCount = useStudio.getState().history.past.length;

    useStudio.getState().setEquipmentTransform('dumbbell_l', {
      position: { x: 4, y: 4, z: 4 },
      rotation: { x: 45, y: 45, z: 45 },
    });

    expect(useStudio.getState().document).toBe(before);
    expect(useStudio.getState().history.past.length).toBe(historyCount);
  });
});
'''
store_test.write_text(text, encoding='utf-8')

# Styles.
styles = Path('src/editor/styles.css')
styles.write_text(styles.read_text(encoding='utf-8') + r'''

/* ---------- static equipment authoring ---------- */

.equipment-list {
  display: grid;
  gap: 6px;
  margin: 8px 0 12px;
}

.equipment-list button {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  text-align: left;
}

.equipment-list small {
  color: var(--muted);
}

.equipment-transform-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 7px;
}

.equipment-transform-grid > strong {
  grid-column: 1 / -1;
  margin-top: 3px;
  font-size: 11px;
}

.equipment-sockets {
  display: grid;
  gap: 6px;
}

.equipment-socket {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel-2);
  padding: 7px 8px;
  font-size: 11px;
}

.equipment-socket > div {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.equipment-socket span {
  color: var(--muted);
}

.equipment-socket code {
  display: block;
  margin-top: 4px;
  color: var(--muted);
}
''', encoding='utf-8')

# Roadmap and changelog.
roadmap = Path('docs/STUDIO_CAPABILITY_ROADMAP.md')
roadmap_text = roadmap.read_text(encoding='utf-8')
old = "- Contact inspection is non-destructive; lock enable/disable still uses normal undoable clip editing."
new = """- Contact inspection is non-destructive; lock enable/disable still uses normal undoable clip editing.
- Static equipment is selectable in the viewport/Equipment workspace and can be translated or rotated with exact numeric inputs or the existing transform gizmo; edits regenerate the deterministic clip through normal undo/redo history.
- Hand-driven equipment rejects world-transform authoring because its attachment solver owns that transform; hand placement remains in the Grip workspace. Equipment socket inventory is visible per selected object."""
if roadmap_text.count(old) != 1:
    raise SystemExit('roadmap equipment foundation marker missing')
roadmap.write_text(roadmap_text.replace(old, new, 1), encoding='utf-8')

changelog = Path('AI_CHANGELOG.md')
text = changelog.read_text(encoding='utf-8')
heading = '### ChatGPT — 2026-09-14 — static equipment transform authoring'
entry = r'''

### ChatGPT — 2026-09-14 — static equipment transform authoring

Added a dedicated Equipment workspace for selecting exercise equipment, inspecting its declared sockets and authoring **static** world transforms. Static objects such as the pull-up rack can now be translated/rotated either through exact numeric controls (position in centimetres, rotation in degrees) or through the Studio's existing Translate / Rotate gizmo. `setEquipmentTransform` edits the exercise definition, regenerates the deterministic clip and participates in normal undo/redo history, so moving a rack also moves the equipment sockets that contact locks resolve against.

Hand- and two-hand-driven objects are deliberately protected: a world-transform edit is ignored without creating an undo step because their final transform belongs to the attachment/grip solver and would otherwise be overwritten on the next frame. The Equipment panel directs those cases back to the Grip workspace instead. Regressions verify a static rack transform reaches both the exercise definition and generated clip and is restored by undo, while a dumbbell hand attachment cannot be misleadingly world-transformed. The roadmap now records static equipment transform authoring as implemented; direct socket-selection/gizmo authoring remains a later refinement.
'''
if heading not in text:
    marker = '## Unreleased\n'
    if marker not in text:
        raise SystemExit('AI_CHANGELOG.md: Unreleased marker missing')
    changelog.write_text(text.replace(marker, marker + entry, 1), encoding='utf-8')

print('Applied static equipment transform authoring')
