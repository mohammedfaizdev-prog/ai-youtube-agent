
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from story_generator import generate_story
from audio_generator import generate_scene_audio

app = FastAPI(
    title="AI YouTube Agent",
    description="Local AI-powered YouTube Shorts automation",
    version="1.0.0"
)


class StoryRequest(BaseModel):
    topic: str = "A mysterious abandoned house"


@app.get("/")
def home():
    return {
        "message": "AI YouTube Agent is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "story-generator"
    }


@app.post("/generate-story")
def create_story(request: StoryRequest):

    try:
        # Step 1: Generate story using Ollama
        story = generate_story(request.topic)

        # Step 2: Generate narration audio using Piper
        audio_files = generate_scene_audio(story["scenes"])

        # Step 3: Return story and audio details
        return {
            "status": "success",
            "message": "Story and audio generated successfully",
            "data": {
                "story": story,
                "audio_files": audio_files
            }
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
