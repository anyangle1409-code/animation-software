import sys, os, json, subprocess, shutil
SP = os.environ["SP"]; sys.path.insert(0, SP + "/pil"); sys.path.insert(0, SP + "/vid")
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
src, outmp4 = sys.argv[1], sys.argv[2]
rows = json.load(open(f"{src}/frames.json"))
B = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
bg = (28, 28, 30)
def xray(n, v):
    skin = Image.open(f"{src}/f{n:03d}_{v}_skin.png").convert("RGBA"); sk = Image.open(f"{src}/f{n:03d}_{v}_skel.png").convert("RGBA")
    b = Image.new("RGBA", skin.size, bg + (255,)); s2 = skin.copy(); s2.putalpha(skin.getchannel("A").point(lambda x: int(x * 0.33)))
    if os.environ.get("MODE") == "skin":
        b.alpha_composite(skin); return b.convert("RGB").crop((0, 0, 700, 600))
    b.alpha_composite(sk); b.alpha_composite(s2); return b.convert("RGB").crop((0, 0, 700, 600))
REST_CE, REST_CR = 4.3, 12.2
cache = {}
def frame(n, up):
    if (n, up) in cache: return cache[(n, up)]
    r = rows[n]; ims = [xray(n, v) for v in ("back", "three_quarter", "side")]
    W = sum(i.width for i in ims); g = Image.new("RGB", (W, 600 + 150), bg); x = 0
    for i, lab in zip(ims, ("back", "three-quarter", "side")):
        g.paste(i, (x, 0)); ImageDraw.Draw(g).text((x + 10, 8), lab, fill=(220, 220, 220), font=F); x += i.width
    d = ImageDraw.Draw(g); y = 612
    isb = r.get("scapula_isb_deg") or [0, 0, 0]
    d.text((14, y), f"arm elevation {r['state']['humerothoracic_elevation']:.0f}°   elbow {r['state']['elbow_flexion']:.0f}°   {'▲ up' if up else '▼ down'}", fill="white", font=B)
    d.text((14, y + 40), f"collarbone (orange): up {r['clavicle_elevation_deg'] - REST_CE:+.0f}°, back {r['clavicle_retraction_deg'] - REST_CR:+.0f}°      "
                         f"shoulder blade (red): upward rotation {isb[1]:.0f}°, tilt back {isb[2]:.0f}°", fill=(255, 200, 120), font=F)
    gap = r["arm_vs_scapular_spine_deg"]
    d.text((14, y + 76), f"upper arm vs shoulder-blade spine: {gap:.0f}°   (0° = arm continues the line of the shoulder blade: the Y)", fill=(140, 200, 255), font=F)
    if os.environ.get("MODE") == "skin": d.text((14, y + 110), os.environ.get("CAPTION", "mesh on the corrected skeleton - raw skinning, old corrective shapes off, new ones not yet rebuilt"), fill=(170, 170, 170), font=F)
    else: d.text((14, y + 110), "orange = collarbone   red = shoulder blade (yellow = its corners)   blue = upper arm   white = spine/ribs   green = skin helpers (not bones)", fill=(170, 170, 170), font=F)
    g = g.resize((1440, int(1440 * g.height / g.width) // 2 * 2)); cache[(n, up)] = g; return g
N = len(rows) - 1
seq = [(0, True)] * 12 + [(i, True) for i in range(N + 1)] + [(N, True)] * 16 + [(i, False) for i in range(N - 1, 0, -1)]
tmp = SP + "/skvidtmp"; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
for k, (n, up) in enumerate(seq * 2):
    frame(n, up).save(f"{tmp}/f{k:05d}.png")
subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", "12", "-i", f"{tmp}/f%05d.png", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", outmp4], check=True)
frame(N, True).save(outmp4.replace(".mp4", "_lockout.jpg"), quality=90); frame(0, True).save(outmp4.replace(".mp4", "_start.jpg"), quality=90)
print("VID", len(seq) * 2)
