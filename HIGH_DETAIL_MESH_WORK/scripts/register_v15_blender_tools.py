"""Register a lightweight V15 Hand helper panel in Blender.

Loaded by start_v15_hand.py after the prepared candidate opens. It only assists
selection/navigation/checkpointing; it does not alter geometry automatically.
"""
from __future__ import annotations

import re
from pathlib import Path

import bpy
from bpy.props import EnumProperty
from bpy.types import Operator, Panel

ROOT = Path(__file__).resolve().parents[1]
BODY_NAME = "Mike_Freeman"

DIGITS = [
    ("INDEX_L", "Index L", ""),
    ("INDEX_R", "Index R", ""),
    ("MIDDLE_L", "Middle L", ""),
    ("MIDDLE_R", "Middle R", ""),
    ("RING_L", "Ring L", ""),
    ("RING_R", "Ring R", ""),
    ("PINKY_L", "Pinky L", ""),
    ("PINKY_R", "Pinky R", ""),
]
ZONES = [
    ("CORE", "Core", "Safe rebuild interior"),
    ("ANCHOR", "Anchor", "Protected transition / do not move"),
    ("SHARP", "Sharp", "Inherited sharp/faceted surface"),
    ("PIP_ZONE", "PIP", "PIP longitudinal joint zone"),
    ("DIP_ZONE", "DIP", "DIP longitudinal joint zone"),
    ("DISTAL_ZONE", "Distal", "Distal shaft/tip transition"),
]

V15F_DIGITS = [
    ("RING", "Ring", ""),
    ("PINKY", "Pinky", ""),
]
V15F_SIDES = [
    ("L", "Left", ""),
    ("R", "Right", ""),
]
V15F_HOTSPOTS = [
    ("GT35", ">35°", "Edges above 35 degrees"),
    ("GT50", ">50°", "Edges above 50 degrees"),
    ("GT75", ">75°", "Edges above 75 degrees"),
    ("GT100", ">100°", "Severe fold edges"),
    ("PIP_HOT", "PIP hot", "PIP-local sharp region"),
    ("DIP_HOT", "DIP hot", "DIP-local sharp region"),
]

def body_object():
    return bpy.data.objects.get(BODY_NAME)

def candidate_version():
    body = body_object()
    if body and body.get("v15_candidate_version"):
        return str(body["v15_candidate_version"])
    stem = Path(bpy.data.filepath).stem
    prefix = "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_"
    return stem[len(prefix):] if stem.startswith(prefix) else stem

def ensure_body_active():
    body = body_object()
    if body is None:
        raise RuntimeError(f"Missing body object {BODY_NAME}")
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    return body

def select_group(group_name):
    body = ensure_body_active()
    group = body.vertex_groups.get(group_name)
    if group is None:
        raise RuntimeError(f"Missing V15 vertex group: {group_name}")
    for vertex in body.data.vertices:
        vertex.select = False
    indexed = set()
    for vertex in body.data.vertices:
        if any(g.group == group.index for g in vertex.groups):
            vertex.select = True
            indexed.add(vertex.index)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.context.view_layer.objects.active = body
    return len(indexed)

class V15_OT_select_zone(Operator):
    bl_idname = "v15.select_zone"
    bl_label = "Select V15 Zone"
    bl_options = {"REGISTER"}

    def execute(self, context):
        digit = context.scene.v15_digit
        zone = context.scene.v15_zone
        name = f"V15_{digit}_{zone}"
        try:
            count = select_group(name)
            self.report({"INFO"}, f"{name}: {count} vertices")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

class V15_OT_select_protected(Operator):
    bl_idname = "v15.select_protected"
    bl_label = "Protected Push-up"
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            count = select_group("V15_PROTECTED_PUSHUP")
            self.report({"INFO"}, f"Protected contacts: {count}")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

class V15_OT_select_all_sharp(Operator):
    bl_idname = "v15.select_all_sharp"
    bl_label = "All Sharp >35°"
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            count = select_group("V15_SHARP_FOLD_35")
            self.report({"INFO"}, f"Sharp diagnostic vertices: {count}")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

class V15_OT_isolate_selected(Operator):
    bl_idname = "v15.isolate_selected"
    bl_label = "Hide Unselected"
    bl_options = {"REGISTER"}

    def execute(self, context):
        body = body_object()
        if not body:
            return {"CANCELLED"}
        try:
            if body.mode != "EDIT":
                bpy.context.view_layer.objects.active = body
                body.select_set(True)
                bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.hide(unselected=True)
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

class V15_OT_reveal_all(Operator):
    bl_idname = "v15.reveal_all"
    bl_label = "Reveal All"
    bl_options = {"REGISTER"}

    def execute(self, context):
        body = body_object()
        if not body:
            return {"CANCELLED"}
        try:
            if body.mode != "EDIT":
                bpy.context.view_layer.objects.active = body
                body.select_set(True)
                bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.reveal()
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

class V15_OT_toggle_guides(Operator):
    bl_idname = "v15.toggle_guides"
    bl_label = "Toggle Guides"
    bl_options = {"REGISTER"}

    def execute(self, context):
        collection = bpy.data.collections.get("V15_GUIDES")
        if collection is None:
            self.report({"ERROR"}, "V15_GUIDES collection missing")
            return {"CANCELLED"}
        collection.hide_viewport = not collection.hide_viewport
        state = "hidden" if collection.hide_viewport else "visible"
        self.report({"INFO"}, f"V15 guides {state}")
        return {"FINISHED"}

class V15_OT_select_v15f_hotspot(Operator):
    bl_idname = "v15.select_v15f_hotspot"
    bl_label = "Select V15f Hotspot"
    bl_options = {"REGISTER"}

    def execute(self, context):
        digit = context.scene.v15f_digit
        side = context.scene.v15f_side
        hotspot = context.scene.v15f_hotspot
        name = f"V15F_{digit}_{side}_{hotspot}"
        try:
            count = select_group(name)
            self.report({"INFO"}, f"{name}: {count} vertices")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

class V15_OT_toggle_v15f_guides(Operator):
    bl_idname = "v15.toggle_v15f_guides"
    bl_label = "Toggle V15f Hotspot Guides"
    bl_options = {"REGISTER"}

    def execute(self, context):
        collection = bpy.data.collections.get("V15F_HOTSPOT_GUIDES")
        if collection is None:
            self.report({"ERROR"}, "V15F_HOTSPOT_GUIDES collection missing")
            return {"CANCELLED"}
        collection.hide_viewport = not collection.hide_viewport
        state = "hidden" if collection.hide_viewport else "visible"
        self.report({"INFO"}, f"V15f hotspot guides {state}")
        return {"FINISHED"}

class V15_OT_checkpoint(Operator):
    bl_idname = "v15.save_checkpoint"
    bl_label = "Save Checkpoint Copy"
    bl_options = {"REGISTER"}

    def execute(self, context):
        if not bpy.data.filepath:
            self.report({"ERROR"}, "Save the candidate Blend first")
            return {"CANCELLED"}
        version = candidate_version()
        folder = ROOT / "checkpoints" / "v15_manual"
        folder.mkdir(parents=True, exist_ok=True)
        used = []
        pattern = re.compile(re.escape(version) + r"_checkpoint_(\d{3})\.blend$")
        for path in folder.glob(f"{version}_checkpoint_*.blend"):
            m = pattern.match(path.name)
            if m:
                used.append(int(m.group(1)))
        number = max(used, default=0) + 1
        target = folder / f"{version}_checkpoint_{number:03d}.blend"
        try:
            bpy.ops.wm.save_as_mainfile(filepath=str(target), copy=True)
            self.report({"INFO"}, f"Checkpoint saved: {target.name}")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

class V15_PT_hand_tools(Panel):
    bl_label = "V15 Hand"
    bl_idname = "V15_PT_hand_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "V15 Hand"

    def draw(self, context):
        layout = self.layout
        layout.label(text=candidate_version())
        box = layout.box()
        box.label(text="Do not move protected contacts")
        box.operator("v15.select_protected", icon="LOCKED")
        box.operator("v15.select_all_sharp", icon="SHADING_RENDERED")

        layout.prop(context.scene, "v15_digit", text="Digit")
        layout.prop(context.scene, "v15_zone", text="Zone")
        layout.operator("v15.select_zone", icon="RESTRICT_SELECT_OFF")

        row = layout.row(align=True)
        row.operator("v15.isolate_selected", icon="HIDE_OFF")
        row.operator("v15.reveal_all", icon="HIDE_ON")

        layout.operator("v15.toggle_guides", icon="EMPTY_AXIS")

        if candidate_version().startswith("v15f"):
            layout.separator()
            box = layout.box()
            box.label(text="V15f ring/pinky proof")
            box.label(text="Start with Ring Left only")
            box.prop(context.scene, "v15f_digit", text="Digit")
            box.prop(context.scene, "v15f_side", text="Side")
            box.prop(context.scene, "v15f_hotspot", text="Hotspot")
            box.operator("v15.select_v15f_hotspot", icon="RESTRICT_SELECT_OFF")
            box.operator("v15.toggle_v15f_guides", icon="EMPTY_AXIS")

        layout.separator()
        layout.operator("v15.save_checkpoint", icon="FILE_TICK")

CLASSES = (
    V15_OT_select_zone,
    V15_OT_select_protected,
    V15_OT_select_all_sharp,
    V15_OT_isolate_selected,
    V15_OT_reveal_all,
    V15_OT_toggle_guides,
    V15_OT_select_v15f_hotspot,
    V15_OT_toggle_v15f_guides,
    V15_OT_checkpoint,
    V15_PT_hand_tools,
)

def register():
    for cls in CLASSES:
        try:
            bpy.utils.register_class(cls)
        except RuntimeError:
            pass
    if not hasattr(bpy.types.Scene, "v15_digit"):
        bpy.types.Scene.v15_digit = EnumProperty(
            name="V15 Digit", items=DIGITS, default="INDEX_L"
        )
    if not hasattr(bpy.types.Scene, "v15_zone"):
        bpy.types.Scene.v15_zone = EnumProperty(
            name="V15 Zone", items=ZONES, default="CORE"
        )
    if not hasattr(bpy.types.Scene, "v15f_digit"):
        bpy.types.Scene.v15f_digit = EnumProperty(
            name="V15f Digit", items=V15F_DIGITS, default="RING"
        )
    if not hasattr(bpy.types.Scene, "v15f_side"):
        bpy.types.Scene.v15f_side = EnumProperty(
            name="V15f Side", items=V15F_SIDES, default="L"
        )
    if not hasattr(bpy.types.Scene, "v15f_hotspot"):
        bpy.types.Scene.v15f_hotspot = EnumProperty(
            name="V15f Hotspot", items=V15F_HOTSPOTS, default="GT50"
        )

def unregister():
    if hasattr(bpy.types.Scene, "v15_digit"):
        del bpy.types.Scene.v15_digit
    if hasattr(bpy.types.Scene, "v15_zone"):
        del bpy.types.Scene.v15_zone
    if hasattr(bpy.types.Scene, "v15f_digit"):
        del bpy.types.Scene.v15f_digit
    if hasattr(bpy.types.Scene, "v15f_side"):
        del bpy.types.Scene.v15f_side
    if hasattr(bpy.types.Scene, "v15f_hotspot"):
        del bpy.types.Scene.v15f_hotspot
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

register()
print("V15_HAND_PANEL_READY", candidate_version(), flush=True)
