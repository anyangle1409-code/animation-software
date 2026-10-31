"""Encode a PNG frame sequence as an H.264 MP4 with Blender's own FFmpeg (no external ffmpeg needed).

usage: python3.13 encode_mp4_blender.py -- <frames dir> <prefix> <out.mp4> [fps]
Frames are <frames dir>/<prefix>_0000.jpg (or .png) ... (every frame is a real rendered pose; nothing is interpolated here).
"""
import sys
from pathlib import Path

import bpy

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, prefix, out = Path(args[0]), args[1], Path(args[2])
fps = int(args[3]) if len(args) > 3 else 24
files = sorted(src.glob(f"{prefix}_[0-9][0-9][0-9][0-9].jpg")) or sorted(src.glob(f"{prefix}_[0-9][0-9][0-9][0-9].png"))
if not files:
    raise SystemExit(f"no frames {prefix}_NNNN.png in {src}")
sc = bpy.context.scene
ed = sc.sequence_editor_create()
strips = ed.strips if hasattr(ed, "strips") else ed.sequences
st = strips.new_image(name="frames", filepath=str(files[0]), channel=1, frame_start=1)
for f in files[1:]:
    st.elements.append(f.name)
_img = bpy.data.images.load(str(files[0])); w, h = _img.size; bpy.data.images.remove(_img)
r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
r.fps, r.fps_base = fps, 1.0
sc.frame_start, sc.frame_end = 1, len(files)
r.image_settings.media_type = "VIDEO" if hasattr(r.image_settings, "media_type") else r.image_settings.file_format
r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format = "MPEG4"; r.ffmpeg.codec = "H264"
r.ffmpeg.constant_rate_factor = "HIGH"; r.ffmpeg.ffmpeg_preset = "GOOD"; r.ffmpeg.gopsize = fps
r.use_sequencer = True; r.use_compositing = False
out.parent.mkdir(parents=True, exist_ok=True)
r.filepath = str(out)
bpy.ops.render.render(animation=True)
print("encoded", out, len(files), "frames", w, "x", h, fps, "fps")
