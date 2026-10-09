#!/usr/bin/env python3
"""Read-only evaluator of an OpenSim 4 .osim model at its default pose, plus a VTK XML PolyData (.vtp) reader.

Used to extract source-defined bone geometry (body origins, joint centres, mesh vertices) from published, openly licensed
musculoskeletal models. It never writes into the project skeleton. Supported: Ground, Body, PhysicalOffsetFrame (body
components and joint frames), WeldJoint / PinJoint / CustomJoint SpatialTransform with Constant, LinearFunction,
SimmSpline / NaturalCubicSpline / PiecewiseLinearFunction and MultiplierFunction, Coordinate default values, Mesh geometry
with scale factors. OpenSim orientations are body-fixed X-Y-Z rotations (radians). Unsupported constructs raise.
"""
import base64, struct, xml.etree.ElementTree as ET, zlib
from pathlib import Path

import numpy as np


def rot(axis, ang):
    a = np.asarray(axis, float); a = a / np.linalg.norm(a)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K


def xyz_body_fixed(o):
    return rot([1, 0, 0], o[0]) @ rot([0, 1, 0], o[1]) @ rot([0, 0, 1], o[2])


def T(R=None, p=None):
    M = np.eye(4)
    if R is not None:
        M[:3, :3] = R
    if p is not None:
        M[:3, 3] = p
    return M


def vec(el, tag, default=None):
    x = el.find(tag)
    if x is None or x.text is None or not x.text.strip():
        return default
    return np.array([float(v) for v in x.text.split()])


def evaluate(fn, q):
    tag = fn.tag
    if tag == 'Constant':
        return float(fn.find('value').text)
    if tag == 'LinearFunction':
        a, b = [float(v) for v in fn.find('coefficients').text.split()]
        return a * q + b
    if tag in ('SimmSpline', 'NaturalCubicSpline', 'PiecewiseLinearFunction', 'GCVSpline'):
        x = np.array([float(v) for v in fn.find('x').text.split()]); y = np.array([float(v) for v in fn.find('y').text.split()])
        return float(np.interp(q, x, y))                 # default-pose evaluation only; spline curvature ignored between knots
    if tag == 'MultiplierFunction':
        inner = [c for c in fn.find('function')] if fn.find('function') is not None else []
        return float(fn.find('scale').text) * evaluate(inner[0], q)
    raise NotImplementedError(tag)


class Model:
    def __init__(self, path, geometry_dir=None):
        self.path = Path(path)
        self.root = ET.parse(self.path).getroot().find('Model')
        self.geom = Path(geometry_dir) if geometry_dir else None
        self.coords = {}
        for c in self.root.iter('Coordinate'):
            dv = c.find('default_value')
            self.coords[c.get('name')] = float(dv.text) if dv is not None else 0.0
        self.bodies = {b.get('name'): b for b in self.root.find('BodySet').find('objects')}
        self.parent_of, self.joint_of = {}, {}
        for j in self.root.find('JointSet').find('objects'):
            frames = {f.get('name'): f for f in j.find('frames')}
            pf, cf = frames[j.find('socket_parent_frame').text], frames[j.find('socket_child_frame').text]
            parent = pf.find('socket_parent').text.split('/')[-1]
            child = cf.find('socket_parent').text.split('/')[-1]
            self.parent_of[child] = parent
            self.joint_of[child] = (j, pf, cf)
        self.world = {'ground': np.eye(4)}

    def offset(self, f):
        return T(xyz_body_fixed(vec(f, 'orientation', np.zeros(3))), vec(f, 'translation', np.zeros(3)))

    def joint_motion(self, j):
        if j.tag == 'WeldJoint':
            return np.eye(4)
        if j.tag == 'PinJoint':
            q = self.coords.get(j.find('coordinates').find('Coordinate').get('name'), 0.0)
            return T(rot([0, 0, 1], q))
        if j.tag != 'CustomJoint':
            raise NotImplementedError(j.tag)
        M = np.eye(4); trans = np.zeros(3)
        for ta in j.find('SpatialTransform'):
            names = (ta.find('coordinates').text or '').split()
            q = self.coords.get(names[0], 0.0) if names else 0.0
            fn = [c for c in ta if c.tag not in ('coordinates', 'axis')][0]
            v = evaluate(fn, q); axis = vec(ta, 'axis')
            if ta.get('name').startswith('rotation'):
                M = M @ T(rot(axis, v))
            else:
                trans = trans + v * axis / np.linalg.norm(axis)
        return T(None, trans) @ M        # OpenSim: translations expressed in the parent offset frame, rotation then applied

    def body_world(self, b):
        if b in self.world:
            return self.world[b]
        j, pf, cf = self.joint_of[b]
        P = self.body_world(self.parent_of[b])
        W = P @ self.offset(pf) @ self.joint_motion(j) @ np.linalg.inv(self.offset(cf))
        self.world[b] = W
        return W

    def meshes(self, b):
        """[(mesh_file, 4x4 world transform of the geometry frame, scale factors)] for body b (body frame and its offset frames)."""
        out = []
        el = self.bodies[b]
        W = self.body_world(b)
        for g in el.find('attached_geometry') or []:
            if g.tag == 'Mesh':
                out.append((g.find('mesh_file').text, W, vec(g, 'scale_factors', np.ones(3))))
        comps = el.find('components')
        for f in (comps if comps is not None else []):
            if f.tag == 'PhysicalOffsetFrame':
                Wf = W @ self.offset(f)
                for g in f.find('attached_geometry') or []:
                    if g.tag == 'Mesh':
                        out.append((g.find('mesh_file').text, Wf, vec(g, 'scale_factors', np.ones(3))))
        return out

    def mesh_points_world(self, b):
        pts = []
        for fname, W, s in self.meshes(b):
            V = read_vtp(self.geom / fname) * s
            pts.append((W[:3, :3] @ V.T).T + W[:3, 3])
        return np.vstack(pts) if pts else np.zeros((0, 3))


def _decode(text, header_type, compressed):
    raw = base64.b64decode(''.join(text.split())) if not compressed else None
    hsize = 8 if header_type == 'UInt64' else 4
    fmt = '<Q' if hsize == 8 else '<I'
    if not compressed:
        n = struct.unpack(fmt, raw[:hsize])[0]
        return raw[hsize:hsize + n]
    s = ''.join(text.split())
    # header: [nblocks, blocksize, lastsize, csize...]; base64-encoded separately from the data
    nblocks = struct.unpack(fmt, base64.b64decode(s[:((hsize * 3 + 2) // 3) * 4])[:hsize])[0]
    hlen = hsize * (3 + nblocks)
    henc = ((hlen + 2) // 3) * 4
    header = base64.b64decode(s[:henc])[:hlen]
    vals = struct.unpack('<' + ('Q' if hsize == 8 else 'I') * (3 + nblocks), header)
    csizes = vals[3:]
    data = base64.b64decode(s[henc:])
    out, pos = b'', 0
    for c in csizes:
        out += zlib.decompress(data[pos:pos + c]); pos += c
    return out


def read_vtp(path):
    root = ET.parse(path).getroot()
    compressed = root.get('compressor') is not None
    ht = root.get('header_type', 'UInt32')
    da = root.find('.//Points/DataArray')
    if da.get('format') == 'ascii':
        return np.array([float(v) for v in da.text.split()]).reshape(-1, 3)
    if da.get('format') != 'binary':
        raise NotImplementedError('appended vtp data')
    raw = _decode(da.text, ht, compressed)
    dt = {'Float32': '<f4', 'Float64': '<f8'}[da.get('type')]
    return np.frombuffer(raw, dtype=dt).reshape(-1, 3).astype(float)
