#!/usr/bin/env python3
"""Print SHA-256 for an ORIGINAL-v1 artifact without modifying it."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path

def main():
    if len(sys.argv)!=2:
        print("Usage: sha256_file.py <file>"); return 2
    p=Path(sys.argv[1])
    if not p.is_file():
        print("STOP — file not found:",p); return 2
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    out={"path":str(p.resolve()),"sha256":h.hexdigest(),"bytes":p.stat().st_size}
    print(json.dumps(out,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
