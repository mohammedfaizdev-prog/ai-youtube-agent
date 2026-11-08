
import json
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen3.5:4b"


def generate_story(topic="A mysterious abandoned house"):

    prompt = f"""
You are a professional YouTube Shorts script writer.

Create an original mystery story about: {topic}

STRICT REQUIREMENTS:
- Total video duration: 30 seconds.
- Exactly 4 scenes.
- Each scene must have narration.
- Each scene must have a detailed visual prompt.
- Narration should be short and engaging.
- Scene durations must add up to exactly 30 seconds.
- Include a strong opening hook.
- End with an unexpected twist.

Return ONLY valid JSON using this exact structure:

{{
    "title": "Story title",
    "description": "YouTube video description",
    "duration": 30,
    "category": "Mystery",
    "scenes": [
        {{
            "scene_number": 1,
            "duration": 7,
            "narration": "Narration text",
            "visual_prompt": "Visual description"
        }}
    ]
}}

Do not include markdown or explanations.
Return exactly four scenes.
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "format": "json",
        "think": False,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 600
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=300
    )

    response.raise_for_status()

    result = response.json()

    story = json.loads(
        result["message"]["content"]
    )

    # Validate story structure
    required_fields = [
        "title",
        "description",
        "duration",
        "category",
        "scenes"
    ]

    for field in required_fields:
        if field not in story:
            raise ValueError(f"Missing field: {field}")

    scenes = story["scenes"]

    if len(scenes) != 4:
        raise ValueError("Story must contain exactly 4 scenes")

    for index, scene in enumerate(scenes, start=1):

        for field in [
            "scene_number",
            "duration",
            "narration",
            "visual_prompt"
        ]:
            if field not in scene:
                raise ValueError(
                    f"Scene {index} is missing {field}"
                )

        if scene["scene_number"] != index:
            raise ValueError("Scene numbers must be sequential")

    total_duration = sum(
        scene["duration"] for scene in scenes
    )

    if total_duration != 30:
        raise ValueError(
            f"Scene durations must total 30 seconds. Got {total_duration}"
        )

    return story
