"""Disable every enabled add-on for this Blender session only (never saved).

Blender 5.2 --factory-startup still enables bundled add-ons (FBX/glTF/BVH/SVG
importers, Cycles, pose library, extensions). The O2 authoring guard treats any
enabled add-on as a blocker, so this runs *before* the guard to satisfy it by
being stricter, not by weakening the check.
"""
import addon_utils
import bpy

for module in [addon.module for addon in bpy.context.preferences.addons]:
    addon_utils.disable(module, default_set=True)
remaining = [addon.module for addon in bpy.context.preferences.addons]
if remaining:
    raise RuntimeError(f"Add-ons still enabled: {remaining}")
print("HGPT: all add-ons disabled for this guarded session")
