import { EQUIPMENT_LIBRARY, equipmentSocketForInstance } from '../../equipment/library';
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
