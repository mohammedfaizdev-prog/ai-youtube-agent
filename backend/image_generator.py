
import io
import json
import secrets
import time
from pathlib import Path

import requests
from PIL import Image


# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

COMFYUI_URL = "http://127.0.0.1:8188"
WORKFLOW_PATH = BASE_DIR / "comfyui_workflow.json"

IMAGE_DIR = BASE_DIR / "assets" / "images"

TIMEOUT = 300
POLL_INTERVAL = 2

STYLE_SUFFIX = (
    "cinematic photorealistic film still, "
    "realistic textures, natural detailed lighting, "
    "professional cinematography, "
    "vertical composition, realistic perspective"
)

NEGATIVE_PROMPT = (
    "blurry, low quality, low resolution, "
    "distorted, deformed, bad anatomy, "
    "extra limbs, duplicate people, "
    "duplicate objects, unrealistic proportions, "
    "cartoon, anime, illustration, painting, "
    "watermark, text, logo, oversaturated colors, "
    "unnatural objects, confusing composition, "
    "excessive visual clutter"
)


# --------------------------------------------------
# WORKFLOW CREATION
# --------------------------------------------------

def create_workflow(prompt, seed):
    """
    Load the tested ComfyUI API workflow and
    dynamically update its prompt and seed.
    """

    if not WORKFLOW_PATH.exists():
        raise FileNotFoundError(
            f"ComfyUI workflow not found: {WORKFLOW_PATH}"
        )

    with open(WORKFLOW_PATH, "r", encoding="utf-8") as file:
        workflow = json.load(file)

    required_nodes = ["2", "3", "5", "7", "8"]

    for node_id in required_nodes:
        if node_id not in workflow:
            raise ValueError(
                f"Required node {node_id} is missing "
                "from comfyui_workflow.json"
            )

    # Positive prompt
    workflow["2"]["inputs"]["text"] = (
        f"{prompt}, {STYLE_SUFFIX}"
    )

    # Negative prompt
    workflow["3"]["inputs"]["text"] = NEGATIVE_PROMPT

    # Random seed for each generated image
    workflow["5"]["inputs"]["seed"] = seed

    # Separate output filenames for each scene
    workflow["7"]["inputs"]["filename_prefix"] = (
        "ai_youtube"
    )

    return workflow


# --------------------------------------------------
# IMAGE CONVERSION
# --------------------------------------------------

def convert_png_to_jpg(image_bytes, output_path):
    """Convert ComfyUI PNG output into a JPG image."""

    with Image.open(io.BytesIO(image_bytes)) as image:
        image.convert("RGB").save(
            output_path,
            format="JPEG",
            quality=95,
            optimize=True
        )


# --------------------------------------------------
# GENERATE ONE SCENE IMAGE
# --------------------------------------------------

def generate_scene_image(scene_number, visual_prompt):
    """Generate one scene image using the ComfyUI API."""

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    if not visual_prompt or not visual_prompt.strip():
        raise ValueError(
            f"Visual prompt is empty for scene {scene_number}."
        )

    seed = secrets.randbelow(2**32)

    workflow = create_workflow(
        visual_prompt,
        seed
    )

    print(f"\nGenerating image for scene {scene_number}...")
    print(f"Prompt: {visual_prompt}")
    print(f"Seed: {seed}")

    # Submit workflow to ComfyUI
    response = requests.post(
        f"{COMFYUI_URL}/prompt",
        json={"prompt": workflow},
        timeout=30
    )

    response.raise_for_status()

    result = response.json()
    prompt_id = result.get("prompt_id")

    if not prompt_id:
        raise RuntimeError(
            f"ComfyUI did not return a prompt ID: {result}"
        )

    print(f"ComfyUI prompt ID: {prompt_id}")

    deadline = time.time() + TIMEOUT

    # Wait for generation to finish
    while time.time() < deadline:

        history_response = requests.get(
            f"{COMFYUI_URL}/history/{prompt_id}",
            timeout=30
        )

        history_response.raise_for_status()

        history = history_response.json()

        if prompt_id in history:

            prompt_history = history[prompt_id]
            outputs = prompt_history.get("outputs", {})

            image_outputs = outputs.get("7", {}).get(
                "images", []
            )

            if not image_outputs:
                raise RuntimeError(
                    "ComfyUI finished but returned no image. "
                    f"Generation details: {prompt_history}"
                )

            image_info = image_outputs[0]

            # Download generated PNG from ComfyUI
            image_response = requests.get(
                f"{COMFYUI_URL}/view",
                params={
                    "filename": image_info["filename"],
                    "subfolder": image_info.get("subfolder", ""),
                    "type": image_info.get("type", "output")
                },
                timeout=60
            )

            image_response.raise_for_status()

            # Convert PNG to JPG for video_generator.py
            final_path = IMAGE_DIR / f"scene_{scene_number}.jpg"

            convert_png_to_jpg(
                image_response.content,
                final_path
            )

            print(
                f"Scene {scene_number} image saved: {final_path}"
            )

            return str(final_path)

        time.sleep(POLL_INTERVAL)

    raise TimeoutError(
        f"Image generation timed out for scene {scene_number}."
    )


# --------------------------------------------------
# GENERATE ALL SCENE IMAGES
# --------------------------------------------------

def generate_scene_images(scenes):
    """Generate images for every scene in the storyboard."""

    generated_images = []

    for scene in scenes:

        scene_number = scene["scene_number"]

        visual_prompt = scene.get(
            "visual_prompt",
            ""
        )

        image_path = generate_scene_image(
            scene_number,
            visual_prompt
        )

        generated_images.append(image_path)

    print("\nAll scene images generated successfully.")

    return generated_images
