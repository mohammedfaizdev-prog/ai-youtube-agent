
from audio_generator import generate_scene_audio

test_scenes = [
    {
        "scene_number": 1,
        "narration": "They say no one lives here because the house eats those who enter."
    },
    {
        "scene_number": 2,
        "narration": "Inside, the air is freezing and something is watching me."
    },
    {
        "scene_number": 3,
        "narration": "Suddenly, the shadows begin moving on their own."
    },
    {
        "scene_number": 4,
        "narration": "I run towards the exit, but the door has disappeared."
    }
]

files = generate_scene_audio(test_scenes)

print("\nAll audio files generated successfully!")
print(files)
