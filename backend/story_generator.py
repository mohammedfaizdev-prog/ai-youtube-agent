
import json
import requests


# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen3.5:4b"

SUPPORTED_GENRES = [
    "horror",
    "mystery",
    "motivational",
    "documentary",
    "emotional",
    "action",
    "comedy",
    "educational",
    "fantasy",
    "sci-fi"
]

# A 30-second narration can work naturally with 50-76 words.
MIN_WORDS = 50
MAX_WORDS = 76

MIN_SCENE_WORDS = 12
MAX_SCENE_WORDS = 20

TARGET_MIN_SCENE_WORDS = 14
TARGET_MAX_SCENE_WORDS = 18

MAX_NARRATION_REPAIR_ATTEMPTS = 2

EXPECTED_SCENE_DURATIONS = [7, 8, 8, 7]

MAX_FINAL_PROMPT_WORDS = 30


# --------------------------------------------------
# OLLAMA REQUEST
# --------------------------------------------------

def call_ollama(messages, json_mode=False, num_predict=1200):

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.7,
            "num_gpu": 0,
            "num_ctx": 4096,
            "num_predict": num_predict
        }
    }

    if json_mode:
        payload["format"] = "json"

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=300
    )

    response.raise_for_status()

    result = response.json()
    content = result.get("message", {}).get("content", "")

    if not content.strip():
        raise ValueError("Ollama returned an empty response.")

    return content.strip()


# --------------------------------------------------
# WORD COUNT
# --------------------------------------------------

def count_words(text):
    return len(text.split())


def get_story_word_count(scenes):
    return sum(count_words(scene["narration"]) for scene in scenes)


# --------------------------------------------------
# TEXT CLEANING
# --------------------------------------------------

def clean_narration(text):

    text = text.strip()

    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()

    if text.lower().startswith("narration:"):
        text = text.split(":", 1)[1].strip()

    return text


def compact_text(text, max_words):

    if not isinstance(text, str):
        return ""

    return " ".join(
        text.strip().replace("\n", " ").split()[:max_words]
    )


# --------------------------------------------------
# NARRATION VALIDATION
# --------------------------------------------------

def validate_narration_length(story):

    scenes = story["scenes"]

    counts = [
        count_words(scene["narration"])
        for scene in scenes
    ]

    total = sum(counts)

    print("\nNarration word counts:")

    for index, count in enumerate(counts, start=1):
        print(f"Scene {index}: {count} words")

    print(f"Total narration: {total} words")

    invalid_scenes = [
        index
        for index, count in enumerate(counts, start=1)
        if not MIN_SCENE_WORDS <= count <= MAX_SCENE_WORDS
    ]

    if invalid_scenes:
        raise ValueError(
            f"Scenes {invalid_scenes} must contain "
            f"{MIN_SCENE_WORDS}-{MAX_SCENE_WORDS} words."
        )

    if not MIN_WORDS <= total <= MAX_WORDS:
        raise ValueError(
            f"Total narration contains {total} words. "
            f"Required: {MIN_WORDS}-{MAX_WORDS}."
        )

    print("Narration validation passed.")

    return story


# --------------------------------------------------
# AUTOMATIC NARRATION REPAIR
# --------------------------------------------------

def repair_story_narration(story):

    print("\nChecking narration length.")

    try:
        return validate_narration_length(story)

    except ValueError as initial_error:
        print("\nNarration is outside the required limits.")
        print(f"Reason: {initial_error}")
        print("Starting automatic narration repair...")

    for attempt in range(1, MAX_NARRATION_REPAIR_ATTEMPTS + 1):

        print(
            f"\nNarration repair attempt "
            f"{attempt}/{MAX_NARRATION_REPAIR_ATTEMPTS}"
        )

        current_scenes = [
            {
                "scene_number": scene["scene_number"],
                "narration": scene["narration"]
            }
            for scene in story["scenes"]
        ]

        repair_prompt = f"""
You are a professional YouTube Shorts narration editor.

Improve the narration of this four-scene story.

TITLE: {story["title"]}
DESCRIPTION: {story["description"]}
GENRE: {story["genre"]}

CURRENT SCENES:
{json.dumps(current_scenes, ensure_ascii=False)}

STRICT REQUIREMENTS:

- Return exactly four scenes.
- Each scene must contain 14-18 words.
- Total narration must contain 56-72 words.
- Count words separated by spaces.
- Preserve the original characters.
- Preserve the original events and scene order.
- Do not invent unrelated events.
- Do not change the story ending.
- Use natural conversational English.
- Every sentence must describe a clear event.
- Add meaningful visual details only when needed.
- Do not add filler or repetitive words.

IMPORTANT:
Check the word count of EACH scene.
If a scene is too short, expand its existing action naturally.
If a scene is too long, shorten it without removing its main event.

Return ONLY valid JSON:

{{
    "scenes": [
        {{"scene_number": 1, "narration": "Narration"}},
        {{"scene_number": 2, "narration": "Narration"}},
        {{"scene_number": 3, "narration": "Narration"}},
        {{"scene_number": 4, "narration": "Narration"}}
    ]
}}
"""

        try:

            content = call_ollama(
                messages=[
                    {"role": "user", "content": repair_prompt}
                ],
                json_mode=True,
                num_predict=1000
            )

            repaired = json.loads(content)

            if not isinstance(repaired, dict):
                raise ValueError(
                    "Repair response must be a JSON object."
                )

            repaired_scenes = repaired.get("scenes")

            if (
                not isinstance(repaired_scenes, list)
                or len(repaired_scenes) != 4
            ):
                raise ValueError(
                    "Repair must return exactly four scenes."
                )

            repaired_map = {}

            for item in repaired_scenes:

                if not isinstance(item, dict):
                    raise ValueError("Invalid repaired scene.")

                number = item.get("scene_number")
                narration = item.get("narration")

                if (
                    not isinstance(number, int)
                    or isinstance(number, bool)
                    or number not in [1, 2, 3, 4]
                ):
                    raise ValueError(
                        "Invalid repaired scene number."
                    )

                if number in repaired_map:
                    raise ValueError(
                        f"Duplicate scene number: {number}"
                    )

                if (
                    not isinstance(narration, str)
                    or not narration.strip()
                ):
                    raise ValueError(
                        f"Empty narration for scene {number}."
                    )

                repaired_map[number] = clean_narration(narration)

            if len(repaired_map) != 4:
                raise ValueError(
                    "Repair did not return all four scenes."
                )

            # Validate the repaired version before modifying
            # the original story.
            candidate_story = {
                **story,
                "scenes": [
                    {
                        **scene,
                        "narration": repaired_map[
                            scene["scene_number"]
                        ]
                    }
                    for scene in story["scenes"]
                ]
            }

            print("\nRepaired narration received.")

            validate_narration_length(candidate_story)

            story["scenes"] = candidate_story["scenes"]

            print("\nAutomatic narration repair successful!")

            return story

        except json.JSONDecodeError as error:
            print(
                f"Invalid narration repair JSON: {error}"
            )

        except ValueError as error:
            print(
                f"Narration repair validation failed: {error}"
            )

        except requests.RequestException:
            raise

    raise ValueError(
        "Narration could not meet the word count after "
        f"{MAX_NARRATION_REPAIR_ATTEMPTS} repair attempts. "
        "Try generating the story again."
    )


# --------------------------------------------------
# STORY STRUCTURE VALIDATION
# --------------------------------------------------

def validate_story_structure(story):

    if not isinstance(story, dict):
        raise ValueError(
            "Story response must be a JSON object."
        )

    required_fields = [
        "title",
        "description",
        "duration",
        "category",
        "genre",
        "scenes"
    ]

    for field in required_fields:
        if field not in story:
            raise ValueError(
                f"Missing story field: {field}"
            )

    genre = str(story["genre"]).strip().lower()

    if genre not in SUPPORTED_GENRES:
        raise ValueError(
            f"Unsupported genre: {genre}"
        )

    story["genre"] = genre

    scenes = story["scenes"]

    if not isinstance(scenes, list) or len(scenes) != 4:
        raise ValueError(
            "Story must contain exactly four scenes."
        )

    for index, scene in enumerate(scenes, start=1):

        if not isinstance(scene, dict):
            raise ValueError(
                f"Scene {index} must be a JSON object."
            )

        for field in [
            "scene_number",
            "duration",
            "narration"
        ]:
            if field not in scene:
                raise ValueError(
                    f"Scene {index} is missing {field}."
                )

        if scene["scene_number"] != index:
            raise ValueError(
                "Scene numbers must be sequential."
            )

        expected_duration = EXPECTED_SCENE_DURATIONS[index - 1]

        if scene["duration"] != expected_duration:
            raise ValueError(
                f"Scene {index} must have duration "
                f"{expected_duration} seconds."
            )

        if not isinstance(scene["narration"], str):
            raise ValueError(
                f"Scene {index} narration must be text."
            )

        scene["narration"] = clean_narration(
            scene["narration"]
        )

        if not scene["narration"]:
            raise ValueError(
                f"Scene {index} narration cannot be empty."
            )

    total_duration = sum(
        scene["duration"] for scene in scenes
    )

    if total_duration != 30 or story["duration"] != 30:
        raise ValueError(
            "Story duration must be exactly 30 seconds."
        )

    return story


# --------------------------------------------------
# GENERATE VISUAL PROMPTS
# --------------------------------------------------

def generate_visual_prompts(story):

    print("\nGenerating narration-based image prompts...")

    for scene in story["scenes"]:

        number = scene["scene_number"]
        narration = scene["narration"].strip()

        if not narration:
            raise ValueError(
                f"Scene {number} has empty narration."
            )

        visual_description = compact_text(
            narration,
            19
        )

        prompt_parts = [
            visual_description,
            "cinematic photorealistic horror film still",
            "detailed realistic environment",
            "dramatic cinematic lighting",
            "vertical portrait composition"
        ]

        final_prompt = ", ".join(prompt_parts)

        final_prompt = compact_text(
            final_prompt,
            MAX_FINAL_PROMPT_WORDS
        )

        scene["main_visual_action"] = visual_description
        scene["visual_prompt"] = final_prompt

        print(f"\nScene {number}")
        print(f"Narration: {narration}")
        print(f"Visual description: {visual_description}")
        print(f"Final image prompt: {final_prompt}")
        print(f"Prompt words: {count_words(final_prompt)}")

    print("\nImage prompts generated successfully.")

    return story


# --------------------------------------------------
# GENERATE STORY
# --------------------------------------------------

def generate_story(topic="A mysterious abandoned house"):

    base_prompt = f"""
You are a professional YouTube Shorts story writer.

Create an original, engaging story about:

{topic}

Choose one genre from:

{", ".join(SUPPORTED_GENRES)}

REQUIREMENTS:

- Exactly four scenes.
- Total duration: 30 seconds.
- Scene durations: 7, 8, 8 and 7 seconds.
- Each scene narration: 12-20 words.
- Total narration: 50-76 words.
- Prefer approximately 14-18 words per scene.
- Use natural conversational English.
- Avoid generic filler and repetition.
- Every sentence must advance the story.
- Every scene must contain a clear physical event.
- Make every scene visually representable.

STORY STRUCTURE:

Scene 1: Strong opening hook and introduction.
Scene 2: Meaningful discovery or development.
Scene 3: Significant escalation or revelation.
Scene 4: Satisfying conclusion or memorable twist.

CONTINUITY:

- Maintain consistent characters and locations.
- Make every scene follow logically.
- Do not introduce random events.
- Connect the ending to the opening.

VISUAL STORYTELLING:

- Describe concrete physical actions.
- Include important objects and locations.
- Make unusual events physically visible.
- Avoid abstract descriptions and vague metaphors.
- Avoid repetitive adjectives and unnecessary words.
- Do not use phrases such as "terrible fate"
  without showing what happens.
- Each scene should describe something an image
  model can actually depict.

Check all word counts before responding.

Return ONLY valid JSON:

{{
    "title": "Story title",
    "description": "YouTube video description",
    "duration": 30,
    "category": "YouTube category",
    "genre": "horror",
    "scenes": [
        {{
            "scene_number": 1,
            "duration": 7,
            "narration": "Scene narration"
        }},
        {{
            "scene_number": 2,
            "duration": 8,
            "narration": "Scene narration"
        }},
        {{
            "scene_number": 3,
            "duration": 8,
            "narration": "Scene narration"
        }},
        {{
            "scene_number": 4,
            "duration": 7,
            "narration": "Scene narration"
        }}
    ]
}}

The genre must be lowercase and supported.
Return exactly four scenes.
Do not include markdown or explanations.
"""

    print("\nGenerating story...")

    try:

        content = call_ollama(
            messages=[
                {"role": "user", "content": base_prompt}
            ],
            json_mode=True,
            num_predict=1600
        )

        story = json.loads(content)

        if not isinstance(story, dict):
            raise ValueError(
                "Story response must be a JSON object."
            )

        story.setdefault("duration", 30)

        if isinstance(story.get("scenes"), list):

            for index, scene in enumerate(story["scenes"]):

                if isinstance(scene, dict) and index < 4:

                    scene.setdefault(
                        "scene_number",
                        index + 1
                    )

                    scene.setdefault(
                        "duration",
                        EXPECTED_SCENE_DURATIONS[index]
                    )

        validate_story_structure(story)

        print(f"\nStory title: {story['title']}")
        print(f"Selected genre: {story['genre']}")

        repair_story_narration(story)

        print("\nStory generated successfully!")
        print(f"Title: {story['title']}")
        print(f"Genre: {story['genre']}")
        print(
            f"Total words: "
            f"{get_story_word_count(story['scenes'])}"
        )
        print("Planned duration: 30 seconds")

        generate_visual_prompts(story)

        return story

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Ollama returned invalid story JSON: {error}"
        ) from error

    except requests.RequestException as error:

        print(f"\nOllama request failed: {error}")
        raise

    except ValueError as error:

        print(
            f"\nStory generation or validation failed: {error}"
        )
        raise
