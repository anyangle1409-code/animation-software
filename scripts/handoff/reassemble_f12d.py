#!/usr/bin/env python3
"""Rebuild HGPT_Female_F12d_ChestShorts_WIP.blend from the HGPT_F12d_blend_partNNof07.zip files and verify every hash.

Put this script, MANIFEST.json and all 7 part ZIPs in one folder (the ZIPs may stay zipped), then run:
    python3 reassemble_f12d.py            (or: python3 reassemble_f12d.py <folder with the zips>)
Exit code 0 only if every part ZIP, every chunk and the rebuilt .blend match MANIFEST.json.
"""
import hashlib, json, os, sys, zipfile

here = os.path.dirname(os.path.abspath(__file__)); src = sys.argv[1] if len(sys.argv) > 1 else here
m = json.load(open(os.path.join(here, "MANIFEST.json")))["f12d_blend"]
out = os.path.join(src, m["file"]); ok = True
if os.path.exists(out):
    sys.exit(f"STOP: {out} already exists - not overwriting. Move it away or verify it with: sha256sum")
full = hashlib.sha256()
with open(out + ".partial", "wb") as w:
    for p in m["parts"]:
        zp = os.path.join(src, p["zip"])
        if not os.path.exists(zp):
            sys.exit(f"MISSING part {p['zip']}")
        zh = hashlib.sha256(open(zp, "rb").read()).hexdigest()
        if zh != p["zip_sha256"]:
            print(f"BAD zip hash {p['zip']}: {zh}"); ok = False
        data = zipfile.ZipFile(zp).read(p["member"])
        if hashlib.sha256(data).hexdigest() != p["member_sha256"] or len(data) != p["member_bytes"]:
            print(f"BAD chunk {p['member']}"); ok = False
        w.write(data); full.update(data); print("ok", p["zip"])
h = full.hexdigest(); size = os.path.getsize(out + ".partial")
if not ok or h != m["sha256"] or size != m["bytes"]:
    sys.exit(f"FAILED: rebuilt sha256 {h} ({size} bytes); expected {m['sha256']} ({m['bytes']} bytes). Partial file kept as {out}.partial")
os.rename(out + ".partial", out)
print(f"VERIFIED {m['file']}  {size} bytes  sha256 {h}")
