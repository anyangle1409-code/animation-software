import { EQUIPMENT_LIBRARY } from '../../equipment/library';
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
