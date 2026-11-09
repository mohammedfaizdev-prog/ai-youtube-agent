
from pathlib import Path
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_DIR = BASE_DIR / "assets" / "images"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)

scenes = [
    ("SCENE 1", "The Abandoned House"),
    ("SCENE 2", "Something Is Watching"),
    ("SCENE 3", "Shadows Come Alive"),
    ("SCENE 4", "The Missing Door")
]

for index, (heading, description) in enumerate(scenes, start=1):
    image = Image.new("RGB", (1080, 1920), color=(15, 18, 30))
    draw = ImageDraw.Draw(image)

    draw.rectangle(
        (70, 600, 1010, 1300),
        outline=(110, 120, 150),
        width=5
    )

    draw.text(
        (100, 800),
        heading,
        fill="white",
        stroke_width=1
    )

    draw.text(
        (100, 900),
        description,
        fill=(180, 190, 210)
    )

    image.save(IMAGE_DIR / f"scene_{index}.jpg", quality=90)

    print(f"Created scene_{index}.jpg")

print("Sample images created successfully!")
