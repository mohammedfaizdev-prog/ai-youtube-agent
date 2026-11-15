
import subprocess
from pathlib import Path

# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "en_US-lessac-medium.onnx"
OUTPUT_DIR = BASE_DIR / "assets" / "audio"

# Piper voice settings
LENGTH_SCALE = 1.4
VOLUME = 1.0


# --------------------------------------------------
# AUDIO GENERATION
# --------------------------------------------------

def generate_scene_audio(scenes):

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Piper model not found: {MODEL_PATH}"
        )

    generated_files = []

    for scene in scenes:

        scene_number = scene["scene_number"]
        narration = scene["narration"]

        output_file = OUTPUT_DIR / f"scene_{scene_number}.wav"

        command = [
            "piper",
            "--model", str(MODEL_PATH),
            "--output_file", str(output_file),
            "--length_scale", str(LENGTH_SCALE),
            "--volume", str(VOLUME)
        ]

        print(
            f"\nGenerating audio for scene {scene_number}..."
        )

        subprocess.run(
            command,
            input=narration,
            text=True,
            check=True,
            capture_output=True
        )

        generated_files.append(str(output_file))

        print(
            f"Generated audio: {output_file.name}"
        )

    print("\nAll scene audio files generated successfully.")

    return generated_files
