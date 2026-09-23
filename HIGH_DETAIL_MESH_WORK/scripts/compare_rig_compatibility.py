"""Compare two GLB rig/skin structures by node name before a mesh migration.

This is a read-only planning tool. It does not edit either GLB.

Usage:
    python scripts/compare_rig_compatibility.py OLD.glb NEW.glb
    python scripts/compare_rig_compatibility.py OLD.glb NEW.glb --json reports/rig_compatibility.json
"""

from __future__ import annotations

import argparse
import json
import struct
from collections import defaultdict
from pathlib import Path


def load_glb(path: Path):
    data = path.read_bytes()
    if len(data) < 28 or struct.unpack_from("<I", data, 0)[0] != 0x46546C67:
        raise ValueError(f"Not a GLB: {path}")
    version = struct.unpack_from("<I", data, 4)[0]
    if version != 2:
        raise ValueError(f"Unsupported GLB version {version}: {path}")
    json_len, json_type = struct.unpack_from("<II", data, 12)
    if json_type != 0x4E4F534A:
        raise ValueError("First GLB chunk is not JSON")
    return json.loads(data[20:20 + json_len])


def node_names(doc):
    out = {}
    duplicates = defaultdict(list)
    for i, node in enumerate(doc.get("nodes", [])):
        name = node.get("name")
        if not name:
            continue
        if name in out:
            duplicates[name].append(i)
        else:
            out[name] = i
    return out, duplicates


def parent_map(doc):
    parents = {}
    for parent, node in enumerate(doc.get("nodes", [])):
        for child in node.get("children", []):
            parents[child] = parent
    return parents


def skin_joint_names(doc, names):
    result = []
    for skin_i, skin in enumerate(doc.get("skins", [])):
        joints = []
        for index in skin.get("joints", []):
            name = doc["nodes"][index].get("name", f"<unnamed:{index}>")
            joints.append(name)
        result.append({
            "skin_index": skin_i,
            "name": skin.get("name"),
            "joint_count": len(joints),
            "joints": joints,
        })
    return result


def parent_name(doc, index, parents):
    p = parents.get(index)
    if p is None:
        return None
    return doc["nodes"][p].get("name", f"<unnamed:{p}>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old", type=Path)
    ap.add_argument("new", type=Path)
    ap.add_argument("--json", dest="json_out", type=Path)
    args = ap.parse_args()

    old = load_glb(args.old)
    new = load_glb(args.new)
    old_names, old_dupes = node_names(old)
    new_names, new_dupes = node_names(new)
    old_parents = parent_map(old)
    new_parents = parent_map(new)

    shared = sorted(set(old_names) & set(new_names))
    added = sorted(set(new_names) - set(old_names))
    removed = sorted(set(old_names) - set(new_names))

    reparented = []
    for name in shared:
        op = parent_name(old, old_names[name], old_parents)
        np = parent_name(new, new_names[name], new_parents)
        if op != np:
            reparented.append({"name": name, "old_parent": op, "new_parent": np})

    old_skins = skin_joint_names(old, old_names)
    new_skins = skin_joint_names(new, new_names)
    old_joint_union = set(j for s in old_skins for j in s["joints"])
    new_joint_union = set(j for s in new_skins for j in s["joints"])

    report = {
        "old": str(args.old),
        "new": str(args.new),
        "old_node_count": len(old.get("nodes", [])),
        "new_node_count": len(new.get("nodes", [])),
        "shared_named_nodes": len(shared),
        "added_named_nodes": added,
        "removed_named_nodes": removed,
        "reparented_named_nodes": reparented,
        "old_skin_count": len(old_skins),
        "new_skin_count": len(new_skins),
        "old_skin_joint_count": len(old_joint_union),
        "new_skin_joint_count": len(new_joint_union),
        "added_skin_joints": sorted(new_joint_union - old_joint_union),
        "removed_skin_joints": sorted(old_joint_union - new_joint_union),
        "duplicate_names_old": dict(old_dupes),
        "duplicate_names_new": dict(new_dupes),
        "migration_attention": bool(
            added or removed or reparented or
            (new_joint_union - old_joint_union) or
            (old_joint_union - new_joint_union) or
            old_dupes or new_dupes
        ),
        "note": (
            "Map by bone/node name, never by positional index. "
            "If migration_attention is true, inspect hierarchy and skin-joint changes "
            "before transferring weights or assuming inverse-bind compatibility."
        ),
    }

    print(json.dumps(report, indent=2))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
