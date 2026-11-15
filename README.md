# AI YouTube Agent

An AI-powered YouTube Shorts generation and publishing system built with local AI models and open-source tools.

The project automates the process of turning a topic into a short-form video, from AI story generation to narration, scene creation, video rendering, and YouTube publishing through n8n.

## Project Overview

AI YouTube Agent generates approximately 30-second YouTube Shorts with minimal manual intervention.

The system combines a Python FastAPI backend, locally hosted AI models, image generation, text-to-speech, FFmpeg video processing, and n8n workflow automation.

## Features

- **AI Story Generation:** Generates short stories from user-provided topics using a local LLM.
- **Structured Story Output:** Produces structured JSON containing story titles, scenes, narration, and visual prompts.
- **Scene Generation:** Creates visual scenes using ComfyUI.
- **Text-to-Speech:** Converts scene narration into audio using Piper TTS.
- **Automated Video Creation:** Combines generated images and narration into a vertical video using FFmpeg.
- **Animated Subtitles:** Generates word-level subtitles with highlighting and animation.
- **Background Music:** Mixes background music with narration.
- **Video Metadata:** Generates YouTube Shorts titles, descriptions, and related metadata.
- **Workflow Automation:** Uses n8n to connect the generation API with file handling and YouTube publishing.
- **Local AI Processing:** Uses locally running models to reduce dependence on paid AI APIs.

## Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python 3.12, FastAPI |
| AI / LLM | Ollama, Qwen 3.5 4B |
| Image Generation | ComfyUI |
| Text-to-Speech | Piper TTS |
| Speech Recognition | Whisper |
| Video Processing | FFmpeg |
| Workflow Automation | n8n |
| API / Data Handling | Requests, Pydantic |
| Publishing | YouTube Data API |

## Architecture

```text
                User Topic
                    |
                    v
             n8n Workflow
                    |
                    v
              FastAPI Backend
                    |
                    v
           AI Story Generation
              (Ollama + Qwen)
                    |
                    v
             Story and Scenes
                    |
          +---------+---------+
          |                   |
          v                   v
    Scene Image           Narration
    Generation           Generation
    (ComfyUI)             (Piper)
          |                   |
          +---------+---------+
                    |
                    v
             Video Rendering
                 (FFmpeg)
                    |
          +---------+---------+
          |         |         |
          v         v         v
       Images    Subtitles  Music
                    |
                    v
              Final Video
                    |
                    v
            YouTube Metadata
                    |
                    v
               n8n Workflow
                    |
                    v
             YouTube Upload
```

## Project Structure

```text
ai-youtube-agent/
│
├── backend/
│   ├── app.py
│   ├── story_generator.py
│   ├── audio_generator.py
│   ├── image_generator.py
│   ├── subtitle_generator.py
│   ├── video_generator.py
│   └── metadata_generator.py
│
├── assets/
│   ├── audio/
│   ├── images/
│   └── music/
│
├── output/
│
├── comfyui_workflow.json
├── requirements.txt
├── README.md
└── .gitignore
```

Generated audio, images, and videos are stored locally and are not intended to be committed to the Git repository.

## Prerequisites

Install the following software before running the project:

- Python 3.12
- Git
- Ollama
- ComfyUI
- FFmpeg
- n8n
- NVIDIA GPU recommended for image generation

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/mohammedfaizdev-prog/ai-youtube-agent.git
cd ai-youtube-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Install and configure Ollama

Download Ollama:

https://ollama.com/download

Pull the required model:

```bash
ollama pull qwen3.5:4b
```

Make sure Ollama is running locally.

### 6. Configure ComfyUI

Install ComfyUI and configure the required image-generation model and workflow.

The project uses `comfyui_workflow.json` for scene image generation.

Make sure ComfyUI is available to the backend before generating videos.

### 7. Configure Piper TTS

Install and configure Piper TTS.

Download the required voice model and place the model files in the location expected by the audio generator.

### 8. Install FFmpeg

Download FFmpeg:

https://ffmpeg.org/download.html

Add FFmpeg to your Windows PATH and verify:

```powershell
ffmpeg -version
```

### 9. Start the FastAPI backend

From the project root:

```powershell
python -m uvicorn app:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

### 10. Access API documentation

Open:

http://127.0.0.1:8000/docs

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Backend information |
| `/health` | GET | Health check |
| `/generate-story` | POST | Generate a structured AI story |
| `/generate-video` | POST | Run the video generation pipeline |

## n8n Workflow Automation

The project uses n8n to automate the publishing workflow.

The workflow connects the FastAPI backend to file handling and YouTube upload.

Typical workflow:

1. Trigger the workflow.
2. Send a topic to the FastAPI generation endpoint.
3. Wait for the video generation process to complete.
4. Read the generated MP4 file.
5. Upload the video using the YouTube node.

### YouTube API Setup

YouTube publishing requires:

- A Google Cloud project.
- YouTube Data API v3 enabled.
- OAuth 2.0 credentials.
- A connected YouTube account in n8n.

Publishing is performed through the official YouTube Data API integration in n8n.

## Video Output

The project is designed for YouTube Shorts:

- Vertical 9:16 format.
- Approximately 30-second duration.
- Generated scene visuals.
- AI-generated narration.
- Animated subtitles.
- Background music.
- YouTube metadata.

## Cost

The project is designed around free and open-source software.

Local AI inference, narration, image generation, and video processing run on the user's machine. YouTube publishing uses the official YouTube API.

Hardware resources and internet connectivity are still required.

## Current Project Status

- [x] Local LLM integration using Ollama
- [x] AI story generation
- [x] Structured JSON output
- [x] FastAPI backend
- [x] Four-scene story generation
- [x] Piper text-to-speech integration
- [x] ComfyUI scene image generation
- [x] FFmpeg video rendering
- [x] Background music integration
- [x] Word-level animated subtitles
- [x] YouTube metadata generation
- [x] n8n workflow integration
- [x] YouTube API upload integration
- [ ] User-configurable publishing schedules
- [ ] Final UI and workflow improvements

## Future Improvements

- User-friendly web interface.
- Custom topic and genre selection.
- More subtitle styles and visual effects.
- User-configurable publishing schedules.
- Better generation performance and resource management.
- Improved error handling and workflow monitoring.

## Project Repository

GitHub: https://github.com/mohammedfaizdev-prog/ai-youtube-agent

**Project Status:** Actively under development.
