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

# Store selection + undoable socket authoring.
p='src/editor/store.ts'
s=read(p)
s=replace_once(s, "  equipmentId: string | null;\n}", "  equipmentId: string | null;\n  socketId: string | null;\n}", 'selection socket id')
s=replace_once(s, "  selectEquipment: (id: string | null) => void;\n  setViewMode", "  selectEquipment: (id: string | null) => void;\n  selectSocket: (equipmentId: string, socketId: string | null) => void;\n  setViewMode", 'select socket interface')
s=replace_once(s, "  setEquipmentTransform: (instanceId: string, transform: { position?: Vec3; rotation?: Vec3 }) => void;\n  setLockEnabled", "  setEquipmentTransform: (instanceId: string, transform: { position?: Vec3; rotation?: Vec3 }) => void;\n  setEquipmentSocketTransform: (instanceId: string, socketId: string, transform: { position?: Vec3; rotation?: Vec3 } | null) => void;\n  setLockEnabled", 'socket edit interface')
s=s.replace("selection: { bone: null, handle: null, equipmentId: null },", "selection: { bone: null, handle: null, equipmentId: null, socketId: null },")
s=s.replace("set({ selection: { bone, handle: null, equipmentId: null } })", "set({ selection: { bone, handle: null, equipmentId: null, socketId: null } })")
s=s.replace("set({ selection: { bone: null, handle, equipmentId: null } })", "set({ selection: { bone: null, handle, equipmentId: null, socketId: null } })")
s=s.replace("set({ selection: { bone: null, handle: null, equipmentId } })", "set({ selection: { bone: null, handle: null, equipmentId, socketId: null } })")ns = s
