
from pathlib import Path
from faster_whisper import WhisperModel

BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_FILE = BASE_DIR / "assets" / "audio" / "scene_1.wav"

if not AUDIO_FILE.exists():
    raise FileNotFoundError(f"Audio file not found: {AUDIO_FILE}")

print("Loading Whisper base model...")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print("Transcribing audio with word-level timestamps...")

segments, info = model.transcribe(
    str(AUDIO_FILE),
    word_timestamps=True,
    vad_filter=False
)

print(f"\nDetected language: {info.language}")
print("\nWORD TIMESTAMPS")
print("-" * 45)

for segment in segments:
    for word in segment.words:
        print(
            f"{word.start:6.2f}s - {word.end:6.2f}s | "
            f"{word.word.strip()}"
        )

print("\nWhisper test completed!")
