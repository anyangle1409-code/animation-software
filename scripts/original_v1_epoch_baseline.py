#!/usr/bin/env python3
"""Print 'NAME PATH' of the pinned baseline for a candidate's stress-pose epoch (used by the evidence .bat files)."""
import sys
from pathlib import Path
from original_v1_production_control import epoch_baseline, ROOT

if __name__ == '__main__':
    name, path = epoch_baseline(ROOT, sys.argv[1])
    print(name, path.replace('/', '\\'))
