
import subprocess
import wave
import re
import textwrap
from pathlib import Path

from subtitle_generator import generate_word_subtitles


# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

IMAGE_DIR = BASE_DIR / "assets" / "images"
AUDIO_DIR = BASE_DIR / "assets" / "audio"
MUSIC_DIR = BASE_DIR / "assets" / "music"

OUTPUT_DIR = BASE_DIR / "output"
SCENE_OUTPUT_DIR = OUTPUT_DIR / "scenes"

WIDTH = 1080
HEIGHT = 1920
FPS = 30

ZOOM_FACTOR = 1.12
MUSIC_VOLUME = 0.12


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
        check=True,
        cwd=BASE_DIR
    )


# --------------------------------------------------
# CINEMATIC CAMERA EFFECT
# --------------------------------------------------

def create_camera_filter(scene_number):
    """Generate subtle cinematic zoom movement."""

    if scene_number % 2 == 1:
        zoom_expression = "min(1+0.00012*on,1.12)"
    else:
        zoom_expression = "max(1.12-0.00012*on,1.0)"

    return (
        f"scale={WIDTH}:{HEIGHT}:"
        "force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        "setsar=1,"
        f"zoompan=z='{zoom_expression}':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        f"d=1:s={WIDTH}x{HEIGHT}:fps={FPS},"
        "format=yuv420p"
    )


# --------------------------------------------------
# SCENE RENDERING
# --------------------------------------------------

def render_scene(scene_number, duration):
    """Render one vertical cinematic video scene."""

    image_path = IMAGE_DIR / f"scene_{scene_number}.jpg"
    audio_path = AUDIO_DIR / f"scene_{scene_number}.wav"

    segment_path = (
        SCENE_OUTPUT_DIR / f"scene_{scene_number}.mp4"
    )

    if not image_path.exists():
        raise FileNotFoundError(f"Missing image: {image_path}")

    if not audio_path.exists():
        raise FileNotFoundError(f"Missing audio: {audio_path}")

    video_filter = create_camera_filter(scene_number)

    command = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-framerate", str(FPS),
        "-i", str(image_path),
        "-i", str(audio_path),
        "-vf", video_filter,
        "-t", f"{duration:.6f}",
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

    print(
        f"Rendered cinematic scene {scene_number}: "
        f"{duration:.2f}s"
    )

    return segment_path


# --------------------------------------------------
# VIDEO CONCATENATION
# --------------------------------------------------

def combine_scenes(scene_files):
    """Combine all rendered scenes."""

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
# GENRE-BASED BACKGROUND MUSIC
# --------------------------------------------------

def add_background_music(video_path, genre, duration):
    """Mix genre-based background music with narration."""

    genre = str(genre or "").strip().lower()

    music_path = MUSIC_DIR / f"{genre}.mp3"

    if not music_path.exists():
        print(
            f"WARNING: No music found for genre '{genre}'. "
            "Continuing without background music."
        )
        return video_path

    music_output_path = OUTPUT_DIR / "music_mixed.mp4"

    print(f"\nSelected background music: {genre}")
    print(f"Music file: {music_path.name}")
    print(f"Music volume: {MUSIC_VOLUME * 100:.0f}%")

    audio_filter = (
        f"[1:a]volume={MUSIC_VOLUME}[music];"
        "[0:a][music]"
        "amix=inputs=2:"
        "duration=first:"
        "dropout_transition=2:"
        "normalize=0[aout]"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-stream_loop", "-1",
        "-i", str(music_path),
        "-filter_complex", audio_filter,
        "-map", "0:v:0",
        "-map", "[aout]",
        "-t", f"{duration:.6f}",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(music_output_path)
    ]

    run_ffmpeg(command)

    print("Background music mixed successfully!")

    return music_output_path


# --------------------------------------------------
# CINEMATIC TITLE OVERLAY
# --------------------------------------------------

def create_title_ass(subtitle_path, title, duration):
    """Add a cinematic title panel and small gold label."""

    subtitle_path = Path(subtitle_path)
    output_path = OUTPUT_DIR / "subtitles_with_title.ass"

    if not subtitle_path.exists():
        raise FileNotFoundError(
            f"Subtitle file not found: {subtitle_path}"
        )

    if duration <= 0:
        raise ValueError("Video duration must be positive.")

    content = subtitle_path.read_text(encoding="utf-8")

    if "[V4+ Styles]" not in content or "[Events]" not in content:
        raise ValueError("Invalid ASS subtitle file structure.")

    title_text = str(title or "Untitled Short").strip()
    title_text = re.sub(r"\s+", " ", title_text)

    # Escape ASS special characters.
    title_text = title_text.replace("{", r"\{").replace("}", r"\}")

    # Wrap long titles into a maximum of two lines.
    title_lines = textwrap.wrap(
        title_text,
        width=25,
        break_long_words=True,
        break_on_hyphens=False
    )

    if not title_lines:
        title_lines = ["Untitled Short"]

    title_lines = title_lines[:2]
    formatted_title = r"\N".join(title_lines)

    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = duration % 60

    end_time = f"{hours}:{minutes:02d}:{seconds:05.2f}"

    # Main title: bold white text inside a dark translucent panel.
    title_style = (
        "\nStyle: VideoTitle,Arial,62,"
        "&H00FFFFFF,&H00FFFFFF,&H00000000,&H88000000,"
        "-1,0,0,0,100,100,1.5,0,3,14,0,8,80,80,250\n"
    )

    # Small gold eyebrow label above the main title.
    kicker_style = (
        "Style: VideoKicker,Arial,25,"
        "&H0000D7FF,&H0000D7FF,&H00000000,&H80000000,"
        "-1,0,0,0,100,100,2,0,1,2,1,8,80,80,355\n"
    )

    title_dialogue = (
        f"Dialogue: 0,0:00:00.00,{end_time},"
        "VideoTitle,,0,0,0,,"
        f"{{\\fad(600,600)}}{formatted_title}\n"
    )

    kicker_dialogue = (
        f"Dialogue: 1,0:00:00.00,{end_time},"
        "VideoKicker,,0,0,0,,"
        "{\\fad(800,600)}A SHORT STORY\n"
    )

    # Insert both styles before the Events section.
    content = content.replace(
        "[Events]",
        title_style + kicker_style + "\n[Events]",
        1
    )

    # Append title events.
    content = content.rstrip() + "\n"
    content += kicker_dialogue
    content += title_dialogue

    output_path.write_text(content, encoding="utf-8")

    print(f"Cinematic title overlay created: {title_text}")

    return output_path


# --------------------------------------------------
# SUBTITLE BURNING
# --------------------------------------------------

def burn_subtitles(
    video_path,
    subtitle_path,
    title=None,
    duration=None
):
    """Burn title and styled ASS subtitles into the final video."""

    final_path = OUTPUT_DIR / "final_short.mp4"

    if title and duration:
        subtitle_path = create_title_ass(
            subtitle_path,
            title,
            duration
        )

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

    run_ffmpeg(command)

    print("Cinematic title and subtitles burned successfully!")

    return final_path


# --------------------------------------------------
# MAIN VIDEO GENERATOR
# --------------------------------------------------

def generate_video(
    scenes,
    genre="horror",
    title=""
):
    """Generate the final cinematic vertical YouTube Short."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCENE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    scene_files = []
    audio_files = []

    print("\nStarting cinematic video generation...\n")
    print(f"Story genre: {genre}")
    print(f"Video title: {title or 'Untitled Short'}")

    # Validate all files before rendering.
    for scene in scenes:

        number = scene["scene_number"]

        image_path = IMAGE_DIR / f"scene_{number}.jpg"
        audio_path = AUDIO_DIR / f"scene_{number}.wav"

        if not image_path.exists():
            raise FileNotFoundError(
                f"Missing image: {image_path}"
            )

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Missing audio: {audio_path}"
            )

        duration = get_audio_duration(audio_path)

        if duration <= 0:
            raise ValueError(
                f"Invalid audio duration: {audio_path}"
            )

        audio_files.append(audio_path)

    # Render cinematic scenes.
    for scene, audio_path in zip(scenes, audio_files):

        number = scene["scene_number"]
        duration = get_audio_duration(audio_path)

        segment_path = render_scene(
            number,
            duration
        )

        scene_files.append(segment_path)

    # Combine scenes.
    combined_path = combine_scenes(scene_files)

    total_duration = sum(
        get_audio_duration(audio)
        for audio in audio_files
    )

    # Add genre-based background music.
    music_video_path = add_background_music(
        combined_path,
        genre,
        total_duration
    )

    # Generate synchronized subtitles.
    print("\nGenerating synchronized subtitles...\n")

    subtitle_path = Path(
        generate_word_subtitles(audio_files)
    )

    # Burn title and subtitles.
    final_path = burn_subtitles(
        music_video_path,
        subtitle_path,
        title=title,
        duration=total_duration
    )

    result = {
        "video_path": str(final_path),
        "duration": round(total_duration, 2),
        "resolution": f"{WIDTH}x{HEIGHT}",
        "fps": FPS,
        "genre": genre,
        "title": title,
        "background_music": (
            str(MUSIC_DIR / f"{genre}.mp3")
            if (MUSIC_DIR / f"{genre}.mp3").exists()
            else None
        ),
        "subtitle_file": str(subtitle_path)
    }

    print("\n" + "=" * 45)
    print("CINEMATIC VIDEO GENERATION COMPLETED")
    print("=" * 45)

    print(f"Video: {final_path}")
    print(f"Duration: {total_duration:.2f}s")
    print(f"Resolution: {WIDTH}x{HEIGHT}")
    print("Camera movement: Slow cinematic zoom")
    print(f"Background music genre: {genre}")
    print("Title: Cinematic persistent overlay")
    print("Subtitles: Word-timed and grouped")

    return result
