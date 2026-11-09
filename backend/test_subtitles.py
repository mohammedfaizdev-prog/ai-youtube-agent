from pathlib import Path
from subtitle_generator import generate_word_subtitles

BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_DIR = BASE_DIR / "assets" / "audio"

audio_files = [
    AUDIO_DIR / f"scene_{i}.wav"
    for i in range(1, 5)
]

result = generate_word_subtitles(audio_files)

print("\nSubtitle file:", result)