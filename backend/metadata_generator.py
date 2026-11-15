
import json
import re
import requests


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen3.5:4b"


# --------------------------------------------------
# OLLAMA REQUEST
# --------------------------------------------------

def call_ollama(messages):

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "think": False,
        "format": "json",
        "options": {
            "temperature": 0.4,
            "num_gpu": 0,
            "num_ctx": 2048,
            "num_predict": 700
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=300
    )

    response.raise_for_status()

    result = response.json()

    return result["message"]["content"].strip()


# --------------------------------------------------
# METADATA VALIDATION
# --------------------------------------------------

def validate_metadata(metadata):

    required_fields = [
        "title",
        "description",
        "tags",
        "hashtags",
        "category"
    ]

    for field in required_fields:
        if field not in metadata:
            raise ValueError(f"Missing metadata field: {field}")

    if not isinstance(metadata["title"], str):
        raise ValueError("Title must be a string.")

    if not isinstance(metadata["description"], str):
        raise ValueError("Description must be a string.")

    if not isinstance(metadata["tags"], list):
        raise ValueError("Tags must be a list.")

    if not isinstance(metadata["hashtags"], list):
        raise ValueError("Hashtags must be a list.")

    if not isinstance(metadata["category"], str):
        raise ValueError("Category must be a string.")

    metadata["title"] = metadata["title"].strip()
    metadata["description"] = metadata["description"].strip()

    # Keep the title within YouTube's 100-character limit.
    if not metadata["title"] or len(metadata["title"]) > 100:
        raise ValueError("Title must contain 1-100 characters.")

    # Remove duplicate tags and limit their number.
    metadata["tags"] = list(dict.fromkeys(
        tag.strip() for tag in metadata["tags"]
        if isinstance(tag, str) and tag.strip()
    ))[:15]

    # Normalize hashtags.
    clean_hashtags = []

    for hashtag in metadata["hashtags"]:
        if not isinstance(hashtag, str):
            continue

        hashtag = re.sub(r"[^a-zA-Z0-9_]", "", hashtag.lstrip("#"))

        if hashtag and hashtag.lower() not in [
            item.lower() for item in clean_hashtags
        ]:
            clean_hashtags.append(hashtag)

    if "shorts" not in [item.lower() for item in clean_hashtags]:
        clean_hashtags.insert(0, "Shorts")

    metadata["hashtags"] = clean_hashtags[:5]

    # Use an appropriate category for the story genre.
    valid_categories = {
        "horror": "Entertainment",
        "mystery": "Entertainment",
        "motivational": "People & Blogs",
        "documentary": "Education",
        "emotional": "People & Blogs",
        "action": "Entertainment",
        "comedy": "Comedy",
        "educational": "Education",
        "fantasy": "Entertainment",
        "sci-fi": "Entertainment"
    }

    genre = metadata.get("genre", "").lower().strip()

    metadata["category"] = valid_categories.get(
        genre,
        "Entertainment"
    )

    return metadata


# --------------------------------------------------
# YOUTUBE SHORTS METADATA GENERATOR
# --------------------------------------------------

def generate_metadata(story):

    if not isinstance(story, dict):
        raise ValueError("Story must be a dictionary.")

    title = story.get("title", "Untitled Story")
    description = story.get("description", "")
    genre = story.get("genre", "entertainment")

    scenes = story.get("scenes", [])

    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Story must contain at least one scene.")

    narration = " ".join(
        scene.get("narration", "")
        for scene in scenes
        if isinstance(scene, dict)
    )

    if not narration.strip():
        raise ValueError("Story narration is empty.")

    story_context = {
        "story_title": title,
        "story_description": description,
        "genre": genre,
        "narration": narration
    }

    system_prompt = """
You are an expert YouTube Shorts SEO strategist.

Generate metadata for a vertical short-form YouTube video.

Rules:
1. Create an engaging and accurate title.
2. Keep the title below 90 characters when possible.
3. Make the description concise and interesting.
4. Include relevant search keywords naturally.
5. Generate 10-15 relevant YouTube tags.
6. Generate 3-5 relevant hashtags.
7. Do not invent events that are not in the story.
8. Avoid misleading clickbait.
9. Include the Shorts hashtag.
10. Return valid JSON only.

Return exactly this structure:

{
    "title": "YouTube Shorts title",
    "description": "Short video description",
    "tags": ["tag1", "tag2"],
    "hashtags": ["Shorts", "Horror"],
    "category": "Entertainment"
}
"""

    user_prompt = f"""
Generate YouTube Shorts metadata for this story:

{json.dumps(story_context, indent=2)}
"""

    content = call_ollama([
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ])

    try:
        metadata = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Ollama returned invalid metadata JSON: {error}"
        )

    metadata["genre"] = genre

    return validate_metadata(metadata)


# --------------------------------------------------
# LOCAL TEST
# --------------------------------------------------

if __name__ == "__main__":

    sample_story = {
        "title": "The Hollow House",
        "description": "One last look inside the house before it's demolished.",
        "genre": "horror",
        "scenes": [
            {
                "narration": "No one lives here, yet something is watching."
            },
            {
                "narration": "I rushed to the rotting door."
            },
            {
                "narration": "The handle turned on its own."
            },
            {
                "narration": "I realized I was the only ghost left."
            }
        ]
    }

    print("\nGenerating YouTube Shorts metadata...\n")

    result = generate_metadata(sample_story)

    print(json.dumps(result, indent=4))

    print("\nMetadata generation completed successfully.")
