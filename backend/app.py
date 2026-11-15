
import subprocess
import time
from pathlib import Path
from threading import Lock

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from story_generator import generate_story
from audio_generator import generate_scene_audio
from image_generator import generate_scene_images


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

app = FastAPI(
    title="AI YouTube Agent",
    description="Local AI-powered YouTube Shorts automation",
    version="1.3.1"
)

pipeline_lock = Lock()

BASE_DIR = Path(__file__).resolve().parent.parent

# Ollama configuration
OLLAMA_EXE = Path(r"D:\tools\Ollama\ollama.exe")
OLLAMA_MODEL = "qwen3.5:4b"

# ComfyUI configuration
COMFY_ROOT = Path(r"D:\AI-YouTube-Agent (1)")

COMFY_PYTHON = (
    COMFY_ROOT / "ComfyUI" / ".venv" / "Scripts" / "python.exe"
)

COMFY_CONFIG = (
    Path.home()
    / "AppData" / "Roaming" / "Comfy Desktop"
    / "instance-model-paths"
    / "inst-1794561734179.yaml"
)

COMFY_SHARED = (
    Path.home()
    / "AppData" / "Local" / "Comfy-Desktop"
    / "ComfyUI-Shared"
)

COMFY_API = "http://127.0.0.1:8188"

LOG_DIR = BASE_DIR / "logs"


# --------------------------------------------------
# PERFORMANCE TRACKING
# --------------------------------------------------

def log_step_time(step_name, start_time, step_timings):
    elapsed = time.perf_counter() - start_time
    step_timings[step_name] = round(elapsed, 2)

    print(
        f"\n[PERFORMANCE] {step_name}: "
        f"{elapsed:.2f} seconds "
        f"({elapsed / 60:.2f} minutes)"
    )

    return time.perf_counter()


# --------------------------------------------------
# REQUEST MODEL
# --------------------------------------------------

class StoryRequest(BaseModel):
    topic: str = "A mysterious abandoned house"


# --------------------------------------------------
# COMFYUI UTILITIES
# --------------------------------------------------

def comfyui_is_running():
    """Check whether the ComfyUI API is available."""

    try:
        response = requests.get(
            f"{COMFY_API}/system_stats",
            timeout=3
        )

        return response.status_code == 200

    except requests.RequestException:
        return False


def start_comfyui():
    """
    Start ComfyUI using the tested low-VRAM
    and CPU-VAE configuration.
    """

    if comfyui_is_running():
        print("ComfyUI is already running.")
        return None

    if not COMFY_PYTHON.exists():
        raise FileNotFoundError(
            f"ComfyUI Python not found: {COMFY_PYTHON}"
        )

    if not COMFY_CONFIG.exists():
        raise FileNotFoundError(
            f"ComfyUI model configuration not found: {COMFY_CONFIG}"
        )

    comfy_main = COMFY_ROOT / "ComfyUI" / "main.py"

    if not comfy_main.exists():
        raise FileNotFoundError(
            f"ComfyUI main.py not found: {comfy_main}"
        )

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    stdout_log = LOG_DIR / "comfyui_stdout.log"
    stderr_log = LOG_DIR / "comfyui_stderr.log"

    command = [
        str(COMFY_PYTHON),
        "-s",
        "ComfyUI\\main.py",

        "--lowvram",
        "--cpu-vae",

        "--listen",
        "127.0.0.1",

        "--port",
        "8188",

        "--extra-model-paths-config",
        str(COMFY_CONFIG),

        "--input-directory",
        str(COMFY_SHARED / "input"),

        "--output-directory",
        str(COMFY_SHARED / "output")
    ]

    print(
        "Starting ComfyUI with low-VRAM "
        "and CPU-VAE settings..."
    )

    with open(stdout_log, "w", encoding="utf-8") as out, \
         open(stderr_log, "w", encoding="utf-8") as err:

        process = subprocess.Popen(
            command,
            cwd=str(COMFY_ROOT),
            stdout=out,
            stderr=err,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )

    # Wait up to 90 seconds for ComfyUI.
    for attempt in range(45):

        if comfyui_is_running():
            print("ComfyUI API is ready.")
            return process

        if process.poll() is not None:
            raise RuntimeError(
                "ComfyUI exited unexpectedly. "
                f"Check error log: {stderr_log}"
            )

        time.sleep(2)

    stop_comfyui(process)

    raise TimeoutError(
        "ComfyUI did not become ready within 90 seconds."
    )


def stop_comfyui(process):
    """
    Stop only the ComfyUI process started by this application.
    """

    if process is None:
        return

    if process.poll() is not None:
        return

    print("Stopping ComfyUI process tree...")

    subprocess.run(
        [
            "taskkill",
            "/PID",
            str(process.pid),
            "/T",
            "/F"
        ],
        capture_output=True,
        text=True,
        timeout=30
    )

    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        print("WARNING: ComfyUI process did not exit in time.")

    print("ComfyUI stopped.")


# --------------------------------------------------
# OLLAMA UTILITIES
# --------------------------------------------------

def stop_ollama_model():
    """Stop the configured Ollama model to release memory."""

    if not OLLAMA_EXE.exists():
        raise FileNotFoundError(
            f"Ollama executable not found: {OLLAMA_EXE}"
        )

    result = subprocess.run(
        [
            str(OLLAMA_EXE),
            "stop",
            OLLAMA_MODEL
        ],
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Could not stop Ollama model: {result.stderr}"
        )

    print(f"Ollama model stopped: {OLLAMA_MODEL}")


# --------------------------------------------------
# BASIC API ENDPOINTS
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "AI YouTube Agent is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "ai-youtube-agent",
        "comfyui": comfyui_is_running()
    }


# --------------------------------------------------
# STORY GENERATION ENDPOINT
# --------------------------------------------------

@app.post("/generate-story")
def create_story(request: StoryRequest):

    try:
        story = generate_story(request.topic)

        audio_files = generate_scene_audio(
            story["scenes"]
        )

        return {
            "status": "success",
            "message": "Story and audio generated successfully",
            "data": {
                "story": story,
                "audio_files": audio_files
            }
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# COMPLETE VIDEO GENERATION PIPELINE
# --------------------------------------------------

@app.post("/generate-video")
def create_video(request: StoryRequest):

    if not pipeline_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail=(
                "Another video generation process "
                "is already running."
            )
        )

    comfy_process = None
    step_timings = {}

    try:

        pipeline_start = time.perf_counter()
        step_start = pipeline_start

        # STEP 1: GENERATE STORY

        print("\nStep 1: Generating story...\n")

        story = generate_story(request.topic)

        step_start = log_step_time(
            "Story generation",
            step_start,
            step_timings
        )

        # STEP 2: RELEASE OLLAMA MEMORY

        print("\nStep 2: Stopping Ollama model...\n")

        stop_ollama_model()

        step_start = log_step_time(
            "Ollama memory cleanup",
            step_start,
            step_timings
        )

        # STEP 3: GENERATE AUDIO

        print("\nStep 3: Generating audio...\n")

        audio_files = generate_scene_audio(
            story["scenes"]
        )

        step_start = log_step_time(
            "Audio generation",
            step_start,
            step_timings
        )

        # STEP 4: START COMFYUI

        print("\nStep 4: Starting ComfyUI...\n")

        comfy_process = start_comfyui()

        step_start = log_step_time(
            "ComfyUI startup",
            step_start,
            step_timings
        )

        # STEP 5: GENERATE SCENE IMAGES

        print("\nStep 5: Generating scene images...\n")

        image_files = generate_scene_images(
            story["scenes"]
        )

        step_start = log_step_time(
            "Scene image generation",
            step_start,
            step_timings
        )

        # STEP 6: RELEASE COMFYUI MEMORY

        print("\nStep 6: Stopping ComfyUI...\n")

        stop_comfyui(comfy_process)
        comfy_process = None

        step_start = log_step_time(
            "ComfyUI cleanup",
            step_start,
            step_timings
        )

        # STEP 7: RENDER FINAL VIDEO

        print("\nStep 7: Rendering final video...\n")

        from video_generator import generate_video

        video_result = generate_video(
             story["scenes"],
             genre=story["genre"],
            title=story.get("title", "Untitled Short")
        )

        step_start = log_step_time(
            "FFmpeg video rendering",
            step_start,
            step_timings
        )

        # STEP 8: GENERATE YOUTUBE SHORTS METADATA

        print("\nStep 8: Generating YouTube Shorts metadata...\n")

        metadata_result = {
            "status": "error",
            "message": "Metadata generation was not completed."
        }

        try:
            from metadata_generator import generate_metadata

            metadata = generate_metadata(story)

            metadata_result = {
                "status": "success",
                "data": metadata
            }

            print(
                "\nYouTube Shorts metadata generated successfully."
            )

        except Exception as error:

            print(f"\nMetadata generation failed: {error}")

            metadata_result = {
                "status": "error",
                "message": str(error)
            }

        finally:

            # Release Ollama memory after metadata generation.
            try:
                stop_ollama_model()
            except Exception as cleanup_error:
                print(
                    f"Ollama cleanup warning: {cleanup_error}"
                )

        step_start = log_step_time(
            "Metadata generation and Ollama cleanup",
            step_start,
            step_timings
        )

        # STEP 9: RETURN RESULTS

        total_time = time.perf_counter() - pipeline_start

        step_timings["total_pipeline"] = round(total_time, 2)

        print("\n=============================================")
        print("GENERATION PERFORMANCE REPORT")
        print("=============================================")

        for step_name, elapsed in step_timings.items():
            print(
                f"{step_name}: "
                f"{elapsed:.2f} seconds "
                f"({elapsed / 60:.2f} minutes)"
            )

        print("---------------------------------------------")
        print(
            f"TOTAL GENERATION TIME: "
            f"{total_time:.2f} seconds "
            f"({total_time / 60:.2f} minutes)"
        )
        print("=============================================\n")

        print("\nAll generation steps completed successfully.")

        return {
            "status": "success",
            "message": "YouTube Short generated successfully",
            "data": {
                "story": story,
                "audio_files": audio_files,
                "image_files": image_files,
                "video": video_result,
                "metadata": metadata_result,
                "performance": step_timings
            }
        }

    except Exception as error:

        print(f"\nVideo generation failed: {error}")

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:

        # Ensure ComfyUI is stopped if this pipeline started it.
        if comfy_process is not None:

            try:
                stop_comfyui(comfy_process)

            except Exception as cleanup_error:
                print(
                    f"ComfyUI cleanup warning: {cleanup_error}"
                )

        pipeline_lock.release()
