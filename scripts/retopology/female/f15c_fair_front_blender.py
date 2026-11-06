"""Give the female shorts front panel fabric ease over the central crease."""
import math
import sys
from pathlib import Path

import bpy

output = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
if output.exists():
    raise FileExistsError(output)
shorts = bpy.data.objects["HGPT_Female_Shorts"]
for vertex in shorts.data.vertices:
    x, y, z = vertex.co
    # Fade to zero on the inner leg and seat. The panel spans across the
    # depression in front, while the crotch bridge and hems retain their cut.
    front = max(0, min(1, (-y - .024) / .032))
    front = front * front * (3 - 2 * front)
    ease = .020 * math.exp(-((x / .059) ** 2 + ((z - .796) / .037) ** 2))
    vertex.co.y -= front * ease
shorts.data.update()
bpy.ops.wm.save_as_mainfile(filepath=str(output), relative_remap=False)
