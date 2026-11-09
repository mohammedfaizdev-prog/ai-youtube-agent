
import subprocess
import wave
from pathlib import Path

from subtitle_generator import generate_word_subtitles


# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

IMAGE_DIR = BASE_DIR / "assets" / "images"
AUDIO_DIR = BASE_DIR / "assets" / "audio"

OUTPUT_DIR = BASE_DIR / "output"
SCENE_OUTPUT_DIR = OUTPUT_DIR / "scenes"

WIDTH = 1080
HEIGHT = 1920
FPS = 30


# --------------------------------------------------
# AUDIO UTILITIES
# --------------------------------------------------

def get_audio_duration(audio_path):
    """Get WAV duration in seconds."""

    with wave.open(str(audio_path), "rb") as audio:
        return audio.getnframes() / audio.getframerate()


# --------------------------------------------------
# FFMPEG UTILITIES
# --------------------------------------------------

def run_ffmpeg(command):
    """Execute FFmpeg and raise an error if it fails."""

    subprocess.run(
        command,
        check=True
    )


def render_scene(scene_number, duration):
    """Render one vertical video scene."""

    image_path = IMAGE_DIR / f"scene_{scene_number}.jpg"
    audio_path = AUDIO_DIR / f"scene_{scene_number}.wav"

    segment_path = SCENE_OUTPUT_DIR / f"scene_{scene_number}.mp4"

    if not image_path.exists():
        raise FileNotFoundError(f"Missing image: {image_path}")

    if not audio_path.exists():
        raise FileNotFoundError(f"Missing audio: {audio_path}")

    command = [
        "ffmpeg",
        "-y",

        "-loop", "1",
        "-framerate", str(FPS),
        "-i", str(image_path),

        "-i", str(audio_path),

        "-t", f"{duration:.6f}",

        "-vf",
        (
            f"scale={WIDTH}:{HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            "setsar=1"
        ),

        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),

        "-c:a", "aac",
        "-b:a", "128k",

        "-shortest",
        "-movflags", "+faststart",

        str(segment_path)
    ]

    run_ffmpeg(command)

    print(f"Rendered scene {scene_number}: {duration:.2f}s")

    return segment_path


# --------------------------------------------------
# VIDEO CONCATENATION
# --------------------------------------------------

def combine_scenes(scene_files):
    """Combine all rendered scenes with timestamp-safe re-encoding."""

    concat_file = OUTPUT_DIR / "concat_list.txt"

    concat_file.write_text(
        "".join(
            f"file '{path.resolve().as_posix()}'\n"
            for path in scene_files
        ),
        encoding="utf-8"
    )

    combined_path = OUTPUT_DIR / "combined.mp4"

    command = [
        "ffmpeg",
        "-y",

        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),

        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",

        "-c:a", "aac",
        "-b:a", "128k",

        "-movflags", "+faststart",

        str(combined_path)
    ]

    run_ffmpeg(command)

    print("All scenes combined successfully!")

    return combined_path


# --------------------------------------------------
# SUBTITLE BURNING
# --------------------------------------------------


def burn_subtitles(video_path, subtitle_path):
    """Burn styled ASS subtitles into the final video."""

    final_path = OUTPUT_DIR / "final_short.mp4"

    # Resolve and escape the ASS file path for FFmpeg
    subtitle_filter_path = (
        str(Path(subtitle_path).resolve())
        .replace("\\", "/")
        .replace(":", r"\:")
        .replace("'", r"\'")
    )

    subtitle_filter = (
        f"subtitles=filename='{subtitle_filter_path}'"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i", str(video_path),

        "-vf", subtitle_filter,

        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",

        "-c:a", "copy",

        "-movflags", "+faststart",

        str(final_path)
    ]

    subprocess.run(
        command,
        check=True,
        cwd=BASE_DIR
    )

    print("ASS subtitles burned successfully!")

    return final_path

    """Burn subtitles into the final video."""

    final_path = OUTPUT_DIR / "final_short.mp4"

    # Use a project-relative path for FFmpeg
    relative_subtitle_path = (
        Path(subtitle_path)
        .resolve()
        .relative_to(BASE_DIR)
        .as_posix()
    )

    subtitle_filter = (
        f"subtitles=filename={relative_subtitle_path}:"
        "force_style='"
        "FontName=Arial,"
        "FontSize=14,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginL=80,"
        "MarginR=80,"
        "MarginV=300"
        "'"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vf", subtitle_filter,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(final_path)
    ]

    # Run FFmpeg from the project root
    subprocess.run(
        command,
        check=True,
        cwd=BASE_DIR
    )

    print("Subtitles burned successfully!")

    return final_path
    """Burn clean, lower-third subtitles into the final video."""

    final_path = OUTPUT_DIR / "final_short.mp4"

    subtitle_filter_path = (
        str(subtitle_path.resolve())
        .replace("\\", "/")
        .replace(":", r"\:")
        .replace("'", r"\'")
    )

    subtitle_filter = (
        f"subtitles=filename='{subtitle_filter_path}':"
        "force_style='"
        "FontName=Arial,"
        "FontSize=14,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginL=80,"
        "MarginR=80,"
        "MarginV=300"
        "'"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vf", subtitle_filter,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(final_path)
    ]

    run_ffmpeg(command)

    print("Subtitles burned successfully!")

    return final_path
    """Burn grouped subtitles into the final video."""

    final_path = OUTPUT_DIR / "final_short.mp4"

    # Use absolute path with FFmpeg filter escaping
    subtitle_filter_path = (
        str(subtitle_path.resolve())
        .replace("\\", "/")
        .replace(":", r"\:")
        .replace("'", r"\'")
    )

    subtitle_filter = (
        f"subtitles=filename='{subtitle_filter_path}':"
        "force_style='"
        "FontName=Arial,"
        "FontSize=20,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=3,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=180"
        "'"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i", str(video_path),

        "-vf", subtitle_filter,

        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",

        "-c:a", "copy",

        "-movflags", "+faststart",

        str(final_path)
    ]

    run_ffmpeg(command)

    print("Subtitles burned successfully!")

    return final_path


# --------------------------------------------------
# MAIN VIDEO GENERATOR
# --------------------------------------------------

def generate_video(scenes):
    """Generate the final vertical YouTube Short."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCENE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    scene_files = []
    audio_files = []

    print("\nStarting video generation...\n")

    # Validate all scenes before rendering
    for scene in scenes:

        number = scene["scene_number"]

        image_path = IMAGE_DIR / f"scene_{number}.jpg"
        audio_path = AUDIO_DIR / f"scene_{number}.wav"

        if not image_path.exists():
            raise FileNotFoundError(f"Missing image: {image_path}")

        if not audio_path.exists():
            raise FileNotFoundError(f"Missing audio: {audio_path}")

        duration = get_audio_duration(audio_path)

        if duration <= 0:
            raise ValueError(f"Invalid audio duration: {audio_path}")

        audio_files.append(audio_path)

    # Render individual scenes
    for scene, audio_path in zip(scenes, audio_files):

        number = scene["scene_number"]
        duration = get_audio_duration(audio_path)

        segment_path = render_scene(
            number,
            duration
        )

        scene_files.append(segment_path)

    # Combine scenes
    combined_path = combine_scenes(scene_files)

    # Generate word-timed grouped subtitles
    print("\nGenerating synchronized subtitles...\n")

    subtitle_path = Path(
        generate_word_subtitles(audio_files)
    )

    # Burn subtitles
    final_path = burn_subtitles(
        combined_path,
        subtitle_path
    )

    total_duration = sum(
        get_audio_duration(audio)
        for audio in audio_files
    )

    result = {
        "video_path": str(final_path),
        "duration": round(total_duration, 2),
        "resolution": f"{WIDTH}x{HEIGHT}",
        "fps": FPS,
        "subtitle_file": str(subtitle_path)
    }

    print("\n" + "=" * 45)
    print("VIDEO GENERATION COMPLETED")
    print("=" * 45)

    print(f"Video: {final_path}")
    print(f"Duration: {total_duration:.2f}s")
    print(f"Resolution: {WIDTH}x{HEIGHT}")
    print("Subtitles: Word-timed and grouped")

    return result
