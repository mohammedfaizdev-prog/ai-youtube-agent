
from pathlib import Path
import wave

from faster_whisper import WhisperModel


# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

WORDS_PER_SUBTITLE = 5
PAUSE_THRESHOLD = 0.45
MAX_LINE_LENGTH = 30
MIN_WORDS_FOR_SENTENCE_BREAK = 3

# Cinematic subtitle appearance
FONT_NAME = "Arial"
FONT_SIZE = 62
OUTLINE_SIZE = 5
SHADOW_SIZE = 3
BOTTOM_MARGIN = 270

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

# ASS colors use &HAABBGGRR
# Primary = completed word color
# Secondary = upcoming/current karaoke fill color
ACTIVE_WORD_COLOR = "&H0000D7FF"
INACTIVE_WORD_COLOR = "&H00FFFFFF"
OUTLINE_COLOR = "&H00000000"
BACKGROUND_COLOR = "&H90000000"

# Animation settings
FADE_IN_MS = 130
FADE_OUT_MS = 120

# Pop animation scale
POP_START = 92
POP_END = 106


# --------------------------------------------------
# LOAD WHISPER MODEL
# --------------------------------------------------

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
    """Group words into natural cinematic phrases."""

    groups = []
    current_group = []

    for word in words:

        if not word["text"]:
            continue

        if current_group:

            previous_word = current_group[-1]

            pause = word["start"] - previous_word["end"]

            current_text = " ".join(
                item["text"] for item in current_group
            )

            sentence_ended = previous_word["text"].endswith(
                (".", "!", "?")
            )

            too_many_words = (
                len(current_group) >= WORDS_PER_SUBTITLE
            )

            too_long = (
                len(current_text) + len(word["text"]) + 1
                > MAX_LINE_LENGTH * 2
            )

            if (
                pause >= PAUSE_THRESHOLD
                or sentence_ended
                or too_many_words
                or too_long
            ):
                groups.append(current_group)
                current_group = []

        current_group.append(word)

        if (
            word["text"].endswith((".", "!", "?"))
            and len(current_group) >= MIN_WORDS_FOR_SENTENCE_BREAK
        ):
            groups.append(current_group)
            current_group = []

    if current_group:
        groups.append(current_group)

    return groups


# --------------------------------------------------
# SUBTITLE LINE WRAPPING
# --------------------------------------------------

def get_line_break_index(group):
    """Find the most balanced two-line split."""

    words = [word["text"] for word in group]

    full_text = " ".join(words)

    if len(full_text) <= MAX_LINE_LENGTH:
        return None

    best_split = None
    best_difference = float("inf")

    for index in range(1, len(words)):

        first_line = " ".join(words[:index])
        second_line = " ".join(words[index:])

        if (
            len(first_line) <= MAX_LINE_LENGTH
            and len(second_line) <= MAX_LINE_LENGTH
        ):
            difference = abs(
                len(first_line) - len(second_line)
            )

            if difference < best_difference:
                best_difference = difference
                best_split = index

    return best_split


def format_subtitle_text(group):
    """Create balanced two-line subtitle text."""

    words = [word["text"] for word in group]

    split_index = get_line_break_index(group)

    if split_index is None:
        return " ".join(words)

    first_line = " ".join(words[:split_index])
    second_line = " ".join(words[split_index:])

    return f"{first_line}\\N{second_line}"


# --------------------------------------------------
# WORD-BY-WORD KARAOKE HIGHLIGHTING
# --------------------------------------------------

def format_karaoke_text(group):
    """
    Generate word-synchronized ASS karaoke tags.

    Completed words are white.
    The currently spoken word is gold.
    """

    split_index = get_line_break_index(group)

    formatted_words = []

    for index, word in enumerate(group):

        word_start = word["start"]

        if index + 1 < len(group):
            next_start = group[index + 1]["start"]
            duration = next_start - word_start
        else:
            duration = word["end"] - word_start

        duration_cs = max(1, round(duration * 100))
        duration_cs = min(duration_cs, 1000)

        # \kf provides smooth karaoke fill.
        karaoke_tag = f"{{\\kf{duration_cs}}}"

        # Brief scale animation at the start of each word.
        pop_tag = (
            "{\\fscx92\\fscy92"
            "\\t(0,100,\\fscx106\\fscy106)"
            "\\t(100,170,\\fscx100\\fscy100)}"
        )

        formatted_words.append(
            karaoke_tag + pop_tag + word["text"]
        )

        if index < len(group) - 1:

            if split_index == index + 1:
                formatted_words.append("\\N")
            else:
                formatted_words.append(" ")

    return "".join(formatted_words)


# --------------------------------------------------
# ASS FILE GENERATOR
# --------------------------------------------------

def generate_ass_file(subtitle_groups):
    """Create animated cinematic ASS subtitles."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ass_path = OUTPUT_DIR / "subtitles.ass"

    lines = [
        "[Script Info]",
        "Title: AI YouTube Agent Animated Cinematic Subtitles",
        "ScriptType: v4.00+",
        "WrapStyle: 2",
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
            f"{INACTIVE_WORD_COLOR},{ACTIVE_WORD_COLOR},"
            f"{OUTLINE_COLOR},{BACKGROUND_COLOR},"
            "-1,0,0,0,100,100,1,0,1,"
            f"{OUTLINE_SIZE},{SHADOW_SIZE},2,90,90,"
            f"{BOTTOM_MARGIN},1"
        ),
        "",
        "[Events]",
        (
            "Format: Layer, Start, End, Style, Name, "
            "MarginL, MarginR, MarginV, Effect, Text"
        )
    ]

    for group in subtitle_groups:

        if not group:
            continue

        subtitle_text = format_karaoke_text(group)

        start_time = format_ass_time(group[0]["start"])
        end_time = format_ass_time(group[-1]["end"])

        # Fade the whole subtitle group in and out.
        animation = (
            f"{{\\fad({FADE_IN_MS},{FADE_OUT_MS})}}"
        )

        lines.append(
            f"Dialogue: 0,{start_time},{end_time},"
            f"Default,,0,0,0,,{animation}{subtitle_text}"
        )

    ass_path.write_text(
        "\n".join(lines),
        encoding="utf-8-sig"
    )

    print(f"\nAnimated ASS subtitles created: {ass_path}")

    return str(ass_path)


# --------------------------------------------------
# MAIN SUBTITLE GENERATOR
# --------------------------------------------------

def generate_word_subtitles(audio_files):
    """
    Generate word-timed animated subtitles
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

                word_text = word.word.strip()

                if not word_text:
                    continue

                words.append({
                    "text": word_text,
                    "start": time_offset + word.start,
                    "end": time_offset + word.end
                })

        groups = group_words(words)

        all_groups.extend(groups)

        time_offset += get_audio_duration(audio_file)

    subtitle_path = generate_ass_file(all_groups)

    print("\n" + "=" * 45)
    print("ANIMATED SUBTITLE GENERATION COMPLETED")
    print("=" * 45)

    print(f"Total subtitle entries: {len(all_groups)}")
    print(f"Total audio duration: {time_offset:.2f}s")
    print(f"Subtitle file: {subtitle_path}")

    return subtitle_path
