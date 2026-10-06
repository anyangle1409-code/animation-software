"""Shoulder movement-matrix posing, rendering and measurement for ORIGINAL-v1 candidates (bpy module).

Posing follows the project's P3 pose construction (scripts/pose_test_original_v1_o4_candidate_blender.py): world-direction
aiming, interval-dependent scapulohumeral rhythm (girdle_for_elevation), and explicit humeral axial rotation. Shape keys are
held at zero for weights-only evidence unless `correctives=True`.
"""
from __future__ import annotations

import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

F = Vector((0, -1, 0))   # character forward (-Y)
B = -F
U = Vector((0, 0, 1))
D = -U
RIG_NAME = "HGPT_CANONICAL_V4_ORIGINAL"


def lat(s):
    return Vector((1.0 if s == "r" else -1.0, 0, 0))


class Poser:
    def __init__(self):
        self.rig = bpy.data.objects[RIG_NAME]
        self.body = next(o for o in bpy.data.objects if o.type == "MESH" and o.find_armature() == self.rig)
        self.rest3 = {b.name: b.matrix_local.to_3x3() for b in self.rig.data.bones}
        self.er_coupling = True

    # ------------------------------------------------------------------ primitives
    def upd(self):
        self.drive_twist_helpers()
        bpy.context.view_layer.update()

    def drive_twist_helpers(self):
        pose = self.rig.pose.bones
        for s in "lr":
            for st, f in (("tw0", 0.0), ("tw1", 0.5)):
                name, parent = f"forearm_{st}_{s}", f"forearm_{s}"
                if name not in pose:
                    continue
                q = pose[parent].matrix_basis.to_quaternion()
                twist = (2.0 * math.atan2(q.y, q.w) + math.pi) % (2.0 * math.pi) - math.pi
                pose[name].matrix_basis = Matrix.Rotation(-(1.0 - f) * twist, 4, "Y")

    def pb(self, n):
        return self.rig.pose.bones[n]

    def bdir(self, n):
        p = self.pb(n)
        return (p.tail - p.head).normalized()

    def rot(self, name, axis, deg):
        p = self.pb(name)
        self.upd()
        axis = Vector(axis)
        if axis.length < 1e-9 or abs(deg) < 1e-9:
            return
        M = p.matrix.copy()
        head = M.translation.copy()
        R = Matrix.Rotation(math.radians(deg), 4, axis.normalized())
        p.matrix = Matrix.Translation(head) @ R @ Matrix.Translation(-head) @ M
        self.upd()

    def aim(self, name, target):
        t = Vector(target).normalized()
        c = self.bdir(name)
        ang = math.degrees(c.angle(t))
        if ang < 1e-4:
            return
        axis = c.cross(t)
        if axis.length < 1e-9:
            axis = c.orthogonal()
        self.rot(name, axis, ang)

    def rot_toward(self, name, axis, deg, want):
        before = self.pb(name).tail.copy()
        self.rot(name, axis, deg)
        if (self.pb(name).tail - before).dot(Vector(want)) < 0:
            self.rot(name, axis, -2 * deg)

    def reset(self):
        for p in self.rig.pose.bones:
            p.matrix_basis = Matrix.Identity(4)
        self.upd()

    def swing_of(self, name):
        self.upd()
        return self.pb(name).matrix.to_3x3() @ self.rest3[name].inverted()

    # ------------------------------------------------------------------ girdle
    @staticmethod
    def scapular_upward_rotation(theta):
        if theta <= 30.0:
            return 0.025 * theta
        if theta <= 90.0:
            return 0.75 + 0.30 * (theta - 30.0)
        if theta <= 120.0:
            return 18.75 + 0.53 * (theta - 90.0)
        return 34.65 + 0.55 * (theta - 120.0)

    def girdle_for_elevation(self, s, target, share=1.0):
        theta = math.degrees(Vector(target).angle(D))
        self.rot_toward(f"clavicle_{s}", F, min(15.0, 0.09 * theta) * share, U)
        self.rot_toward(f"scapula_{s}", F, self.scapular_upward_rotation(theta) * share, lat(s))

    def girdle_protraction(self, s, deg):
        """Scapular protraction (+) / retraction (-): clavicle swings about the vertical axis, tip forward for protraction."""
        if abs(deg) < 1e-6:
            return
        self.rot_toward(f"clavicle_{s}", U, abs(deg), F if deg > 0 else B)

    # ------------------------------------------------------------------ humerus axial rotation
    def neutral_axial(self, s):
        """Remove axial twist of the humerus relative to the minimal swing from rest (anatomical neutral at that direction)."""
        name = f"upperarm_{s}"
        h = self.bdir(name)
        rest_dir = (self.rest3[name] @ Vector((0, 1, 0))).normalized()
        # parent (scapula) carries the rest frame; neutral = minimal rotation from parent-carried rest direction to h
        par = self.pb(f"scapula_{s}")
        Rp = par.matrix.to_3x3() @ self.rest3[f"scapula_{s}"].inverted()
        d0 = (Rp @ rest_dir).normalized()
        axis = d0.cross(h)
        Rs = Matrix.Rotation(d0.angle(h), 3, axis.normalized()) if axis.length > 1e-9 else Matrix.Identity(3)
        want_lat = Rs @ Rp @ (self.rest3[name] @ Vector((1, 0, 0)))
        now_lat = self.swing_of(name) @ Vector((1, 0, 0))
        a = (now_lat - h * now_lat.dot(h)).normalized()
        w = (want_lat - h * want_lat.dot(h)).normalized()
        ang = math.degrees(math.atan2(h.dot(a.cross(w)), a.dot(w)))
        self.rot(name, h, ang)

    def axial_rotate(self, s, deg):
        """External (+) / internal (-) humeral rotation about the humerus long axis. External rotation turns the anterior
        surface of the arm laterally; sign found numerically from the arm's anterior direction."""
        if abs(deg) < 1e-6:
            return
        name = f"upperarm_{s}"
        h = self.bdir(name)
        ant = self.swing_of(name) @ F                       # rest-anterior direction carried by the humerus
        ant = (ant - h * ant.dot(h)).normalized()
        # external rotation moves the anterior surface toward lateral
        trial = Matrix.Rotation(math.radians(10), 3, h) @ ant
        sign = 1.0 if trial.dot(lat(s)) > ant.dot(lat(s)) else -1.0
        if abs(ant.dot(lat(s))) < 1e-3 and abs(trial.dot(lat(s)) - ant.dot(lat(s))) < 1e-4:
            # arm pointing laterally: use anterior->up as external
            sign = 1.0 if (Matrix.Rotation(math.radians(10), 3, h) @ ant).dot(U) > ant.dot(U) else -1.0
        self.rot(name, h, sign * deg)

    # ------------------------------------------------------------------ composite poses
    def elevate(self, s, plane, theta, axial=0.0, elbow=0.0, share=1.0, horizontal=0.0):
        """plane: 'flexion' (sagittal, forward) | 'abduction' (frontal) | 'scaption' (30 deg anterior to frontal).
        theta: humerothoracic elevation from arm-at-side, degrees. axial: external(+)/internal(-) humeral rotation.
        horizontal: extra horizontal adduction(+)/abduction(-) at the current elevation, degrees."""
        az = {"flexion": 90.0, "abduction": 0.0, "scaption": 30.0}[plane] if isinstance(plane, str) else float(plane)
        az += horizontal
        horiz = lat(s) * math.cos(math.radians(az)) + F * math.sin(math.radians(az))
        t = math.radians(theta)
        target = (D * math.cos(t) + horiz * math.sin(t)).normalized()
        if theta > 1e-3:
            self.girdle_for_elevation(s, target, share)
        # protraction with flexion/horizontal adduction, retraction with horizontal abduction (scapula follows the humerus plane)
        prot = 0.12 * theta * max(0.0, math.sin(math.radians(az))) + 0.25 * horizontal
        self.girdle_protraction(s, max(-15.0, min(20.0, prot)))
        if theta > 1e-3:
            self.aim(f"upperarm_{s}", target)
        self.neutral_axial(s)
        # project rule (pose_test P2/P3): an elevated arm couples obligatory external rotation to elevation
        # (about half the elevation above 30 deg, at most 80 deg); `axial` is an offset around that anatomical neutral
        er = min(80.0, 0.5 * max(0.0, theta - 30.0)) if self.er_coupling else 0.0
        if er or axial:
            self.axial_rotate(s, er + axial)
        if elbow:
            h = self.bdir(f"upperarm_{s}")
            # flex the forearm about the humerus lateral axis (hinge), toward the arm's anterior side
            latax = self.swing_of(f"upperarm_{s}") @ Vector((1, 0, 0))
            self.rot_toward(f"forearm_{s}", latax, elbow, self.swing_of(f"upperarm_{s}") @ F)
        return target

    # ------------------------------------------------------------------ evaluation
    def evaluated(self):
        dg = bpy.context.evaluated_depsgraph_get()
        ev = self.body.evaluated_get(dg)
        me = ev.to_mesh()
        n = len(me.vertices)
        co = np.empty(n * 3)
        me.vertices.foreach_get("co", co)
        ev.to_mesh_clear()
        co = co.reshape(-1, 3)
        Mw = np.array(self.body.matrix_world)
        return co @ Mw[:3, :3].T + Mw[:3, 3]

    def set_correctives(self, value):
        keys = self.body.data.shape_keys
        if keys:
            for kb in keys.key_blocks[1:]:
                kb.value = value


# ---------------------------------------------------------------------- rendering
def setup_render(res=900):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "SINGLE"
    sc.display.shading.single_color = (0.62, 0.58, 0.55)
    sc.display.shading.show_cavity = True
    sc.display.shading.cavity_type = "WORLD"
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.display.shading.background_type = "VIEWPORT"
    sc.display.shading.background_color = (0.22, 0.22, 0.23)
    if "REVIEW_CAM" not in bpy.data.objects:
        cam = bpy.data.objects.new("REVIEW_CAM", bpy.data.cameras.new("REVIEW_CAM"))
        sc.collection.objects.link(cam)
    cam = bpy.data.objects["REVIEW_CAM"]
    sc.camera = cam
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith("Icosphere"):
            o.hide_render = True
    return cam


VIEWS = {
    "front": (0.0, 8.0), "front_three_quarter": (40.0, 10.0), "side": (90.0, 5.0),
    "rear_three_quarter": (140.0, 10.0), "rear": (180.0, 8.0),
}


def look(cam, target, az_deg, el_deg, dist, lens=50):
    """Azimuth 0 = in front of the character (character faces -Y), +az moves toward the character's left (+X is right side)."""
    az, el = math.radians(az_deg), math.radians(el_deg)
    off = Vector((-math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist
    cam.location = Vector(target) + off
    cam.rotation_euler = (-off).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens


def render(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
