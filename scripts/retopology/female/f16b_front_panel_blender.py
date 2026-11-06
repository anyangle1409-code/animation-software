"""Fit a smooth front-panel surface to the F15b shorts."""
import sys
from pathlib import Path
import bpy

output = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
if output.exists():
    raise FileExistsError(output)

def smoothstep(value, start, end):
    t = min(1.0, max(0.0, (value - start) / (end - start)))
    return t * t * (3 - 2 * t)

shorts = bpy.data.objects["HGPT_Female_Shorts"]
for vertex in shorts.data.vertices:
    x, y, z = vertex.co
    # Loft the panel across the anatomical indentation, then blend the loft
    # into the thigh, the upper front, and the existing crotch bridge.
    height = smoothstep(z, .692, .800) * (1 - smoothstep(z, .863, .934))
    width = 1 - smoothstep(abs(x), .061, .138)
    front = smoothstep(-y, .006, .039)
    surface_y = -.113 - .14 * (z - .83) + .48 * x * x
    vertex.co.y += height * width * front * min(0, surface_y - y)
shorts.data.update()
bpy.ops.wm.save_as_mainfile(filepath=str(output), relative_remap=False)
