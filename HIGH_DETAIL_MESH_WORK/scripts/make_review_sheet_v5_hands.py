"""Assemble labeled technical render comparisons for the candidate handoff."""

from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
renders = root / "renders_v5_hands_curved"


def sheet(name, images, columns, cell_size):
    rows = (len(images) + columns - 1) // columns
    width, height = cell_size
    output = Image.new("RGB", (columns * width, rows * height), "white")
    draw = ImageDraw.Draw(output)
    for index, (label, path) in enumerate(images):
        picture = Image.open(path)
        picture.thumbnail((width - 12, height - 42))
        x = (index % columns) * width
        y = (index // columns) * height
        output.paste(picture, (x + (width - picture.width) // 2, y + 30))
        draw.text((x + 8, y + 8), label, fill="black")
    output.save(renders / name, quality=90)


sheet(
    "V5_HANDS_ANATOMY_AND_EXERCISES.jpg",
    [
        ("Curl Bottom — front", renders / "dumbbell_bicep_curl_bottom_candidate_front.png"),
        ("Curl Bottom — side", renders / "dumbbell_bicep_curl_bottom_candidate_side.png"),
        ("Curl Bottom — three-quarter", renders / "dumbbell_bicep_curl_bottom_candidate_three_quarter.png"),
        ("Curl Bottom — back", renders / "dumbbell_bicep_curl_bottom_candidate_back.png"),
    ]
    + [
        (label, renders / f"{exercise}_peak_candidate_three_quarter.png")
        for label, exercise in (
            ("Squat peak", "air_squat"),
            ("Curl peak", "dumbbell_bicep_curl"),
            ("Shoulder press peak", "dumbbell_shoulder_press"),
            ("Pull-up peak", "pull_up"),
            ("Push-up peak", "push_up"),
        )
    ],
    columns=3,
    cell_size=(420, 490),
)

sheet(
    "V5_HANDS_GRIP_AND_FLOOR_COMPARISON.jpg",
    [
        (f"{exercise} {who} - hand",
         (root / ('renders_v4b' if who == 'V4B' else 'renders_v5_hands_curved') /
          f"{prefix}_{phase}_candidate_hand.png"))
        for exercise, prefix, phase in (("Curl", "dumbbell_bicep_curl", "bottom"), ("Push-up", "push_up", "bottom"), ("Pull-up", "pull_up", "peak"))
        for who in ("V4B", "V5")
    ],
    columns=2,
    cell_size=(460, 510),
)
