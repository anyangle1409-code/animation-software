"""Build a matched checkpoint-004 versus Route A ring_L proof board."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "renders_v15f_ring_proof"
NEW = ROOT / "renders_v15f_anchor_buffer_route_a"
OUT = NEW / "V15F_CHECKPOINT004_VS_ROUTE_A_RING_L.jpg"
VIEWS = (("yneg", "Y-"), ("ypos", "Y+"), ("xpos", "Side"), ("oblique", "Oblique"))


def font(size):
    for path in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


cell_w, cell_h, label_h, title_h = 720, 720, 54, 82
canvas = Image.new("RGB", (cell_w * 4, title_h + (cell_h + label_h) * 2), (25, 25, 25))
draw = ImageDraw.Draw(canvas)
draw.text((24, 20), "V15f ring_L — checkpoint 004 vs bounded Route A", font=font(32), fill=(240, 240, 240))
for row, (folder, label) in enumerate(((OLD, "Checkpoint 004"), (NEW, "Route A trial"))):
    for col, (key, view_label) in enumerate(VIEWS):
        image = Image.open(folder / f"V15f_ring_L_{key}.png").convert("RGB")
        image.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
        x = col * cell_w + (cell_w - image.width) // 2
        y0 = title_h + row * (cell_h + label_h)
        y = y0 + (cell_h - image.height) // 2
        canvas.paste(image, (x, y))
        draw.text((col * cell_w + 14, y0 + cell_h + 10), f"{label} — {view_label}", font=font(24), fill=(240, 240, 240))
OUT.parent.mkdir(parents=True, exist_ok=True)
canvas.save(OUT, quality=94, subsampling=0)
print(OUT)
