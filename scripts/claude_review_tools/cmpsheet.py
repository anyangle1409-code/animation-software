# rows = (label, frame dir), cols = frame numbers x views; crop of the right arm (image left side in back view)
import sys, os; sys.path.insert(0, os.environ["SP"] + "/pil")
from PIL import Image, ImageDraw
out_path = sys.argv[1]; rows = [a.split("=") for a in sys.argv[2:]]
frames = [int(x) for x in os.environ.get("FR", "16,24,28").split(",")]; views = os.environ.get("VIEWS", "back,three_quarter").split(",")
crop = [float(x) for x in os.environ.get("CROP", "0.0,0.0,0.6,0.7").split(",")]
W = int(os.environ.get("W", 300))
cols = [(n, v) for n in frames for v in views]
out = Image.new("RGB", (len(cols) * W + 60, len(rows) * (W + 18)), "white"); d = ImageDraw.Draw(out)
for r, (lab, D) in enumerate(rows):
    d.text((4, r * (W + 18) + W // 2), lab, fill="black")
    for c, (n, v) in enumerate(cols):
        p = f"{D}/f{n:03d}_{v}_skin.png"
        if not os.path.exists(p): continue
        a = Image.open(p).convert("RGBA"); b = Image.new("RGBA", a.size, (28, 28, 30, 255)); b.alpha_composite(a)
        im = b.convert("RGB"); w, h = im.size
        im = im.crop((int(w * crop[0]), int(h * crop[1]), int(w * crop[2]), int(h * crop[3]))).resize((W, W))
        x = 60 + c * W; y = r * (W + 18); out.paste(im, (x, y + 16)); d.text((x + 4, y + 2), f"t={n/40:.2f} {v}", fill="black")
out.save(out_path, quality=88)
