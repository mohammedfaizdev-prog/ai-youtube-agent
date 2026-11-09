
from pathlib import Path
import wave

from faster_whisper import WhisperModel


# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

WORDS_PER_SUBTITLE = 4
PAUSE_THRESHOLD = 0.35

# Subtitle appearance
FONT_NAME = "Arial"
FONT_SIZE = 42
OUTLINE_SIZE = 3
BOTTOM_MARGIN = 250

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920


# Load Whisper model once
print("Loading Whisper model...")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)


# --------------------------------------------------
# TIMESTAMP UTILITIES
# --------------------------------------------------

def format_ass_time(seconds):
    """Convert seconds into ASS timestamp format."""

    centiseconds = round(seconds * 100)

    hours = centiseconds // 360000
    centiseconds %= 360000

    minutes = centiseconds // 6000
    centiseconds %= 6000

    secs = centiseconds // 100
    centiseconds %= 100

    return (
        f"{hours}:{minutes:02}:{secs:02}."
        f"{centiseconds:02}"
    )


def get_audio_duration(audio_file):
    """Get actual WAV duration."""

    with wave.open(str(audio_file), "rb") as audio:
        return audio.getnframes() / audio.getframerate()


# --------------------------------------------------
# SUBTITLE GROUPING
# --------------------------------------------------

def group_words(words):
    """Group words into readable subtitle phrases."""

    groups = []
    current_group = []

    for word in words:

        if current_group:

            previous_word = current_group[-1]

            pause = word["start"] - previous_word["end"]
            previous_text = previous_word["text"]

            sentence_ended = previous_text.endswith(
                (".", "!", "?")
            )

            if (
                pause >= PAUSE_THRESHOLD
                or sentence_ended
                or len(current_group) >= WORDS_PER_SUBTITLE
            ):
                groups.append(current_group)
                current_group = []

        current_group.append(word)

        if word["text"].endswith((".", "!", "?")):
            groups.append(current_group)
            current_group = []

    if current_group:
        groups.append(current_group)

    return groups


# --------------------------------------------------
# ASS FILE GENERATOR
# --------------------------------------------------

def generate_ass_file(subtitle_groups):
    """Create styled ASS subtitles."""

    ass_path = OUTPUT_DIR / "subtitles.ass"

    lines = [
        "[Script Info]",
        "Title: AI YouTube Agent Subtitles",
        "ScriptType: v4.00+",
        f"PlayResX: {VIDEO_WIDTH}",
        f"PlayResY: {VIDEO_HEIGHT}",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        (
            "Format: Name, Fontname, Fontsize, PrimaryColour, "
            "SecondaryColour, OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, ScaleX, ScaleY, "
            "Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding"
        ),
        (
            f"Style: Default,{FONT_NAME},{FONT_SIZE},"
            "&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
            "-1,0,0,0,100,100,0,0,1,"
            f"{OUTLINE_SIZE},0,2,80,80,{BOTTOM_MARGIN},1"
        ),
        "",
        "[Events]",
        (
            "Format: Layer, Start, End, Style, Name, "
            "MarginL, MarginR, MarginV, Effect, Text"
        )
    ]

    for group in subtitle_groups:

        text = " ".join(
            word["text"] for word in group
        )

        start_time = format_ass_time(group[0]["start"])
        end_time = format_ass_time(group[-1]["end"])

        lines.append(
            f"Dialogue: 0,{start_time},{end_time},"
            f"Default,,0,0,0,,{text}"
        )

    ass_path.write_text(
        "\n".join(lines),
        encoding="utf-8-sig"
    )

    print(f"\nASS subtitles created: {ass_path}")

    return str(ass_path)


# --------------------------------------------------
# MAIN SUBTITLE GENERATOR
# --------------------------------------------------

def generate_word_subtitles(audio_files):
    """
    Generate word-timed, grouped ASS subtitles
    from multiple scene audio files.
    """

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_groups = []
    time_offset = 0.0

    for audio_file in audio_files:

        audio_file = Path(audio_file)

        if not audio_file.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_file}"
            )

        print(f"\nTranscribing: {audio_file.name}")

        segments, info = model.transcribe(
            str(audio_file),
            word_timestamps=True,
            vad_filter=False
        )

        print(f"Detected language: {info.language}")

        words = []

        for segment in segments:

            for word in segment.words:

                words.append({
                    "text": word.word.strip(),
                    "start": time_offset + word.start,
                    "end": time_offset + word.end
                })

        groups = group_words(words)

        all_groups.extend(groups)

        time_offset += get_audio_duration(audio_file)

    # Create final ASS subtitle file
    subtitle_path = generate_ass_file(all_groups)

    print("\n" + "=" * 45)
    print("SUBTITLE GENERATION COMPLETED")
    print("=" * 45)

    print(f"Total subtitle entries: {len(all_groups)}")
    print(f"Total audio duration: {time_offset:.2f}s")
    print(f"Subtitle file: {subtitle_path}")

    return subtitle_path
