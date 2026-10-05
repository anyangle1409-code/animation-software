#!/usr/bin/env python3
"""Validate ORIGINAL-v1 read-only Blender skinning-mode audit."""
from __future__ import annotations
import json,re,sys
from pathlib import Path
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def validate(d):
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("status")!="READ_ONLY_SKINNING_MODE_AUDIT": raise ValueError("unexpected status")
    if d.get("source_saved_or_modified") is not False: raise ValueError("source must be read-only")
    if not SHA_RE.fullmatch(str(d.get("candidate_sha256",""))): raise ValueError("candidate_sha256 invalid")
    mods=d.get("armature_modifiers") or []
    if d.get("armature_modifier_count")!=len(mods): raise ValueError("armature modifier count differs")
    if not mods: raise ValueError("no armature modifier recorded")
    for m in mods:
        if m.get("target_object")!="HGPT_CANONICAL_V4_ORIGINAL": raise ValueError("armature target differs from canonical rig")
        if not isinstance(m.get("use_deform_preserve_volume"),bool): raise ValueError("preserve-volume flag missing")
        if not isinstance(m.get("use_vertex_groups"),bool): raise ValueError("vertex-group flag missing")
    return {
      "candidate":d.get("candidate"),
      "modifier_count":len(mods),
      "preserve_volume":[m["use_deform_preserve_volume"] for m in mods],
      "status":"PASS"
    }

def main():
    if len(sys.argv)!=2:
        print("Usage: validate_original_v1_skinning_mode.py <report.json>"); return 2
    try:
        out=validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
        print("SKINNING MODE EVIDENCE: PASS")
        print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
