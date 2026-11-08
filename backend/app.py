
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from story_generator import generate_story

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
        story = generate_story(request.topic)

        return {
            "status": "success",
            "data": story
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
