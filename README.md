
# AI YouTube Agent

An AI-powered YouTube Shorts automation system that generates
short stories, creates video content and automates publishing
using open-source tools.

## Project Overview

The goal is to build an automated workflow that generates
approximately 30-second YouTube Shorts with minimal manual
intervention.

## Current Technology Stack

- Python 3.12
- FastAPI
- Ollama
- Qwen 3.5 4B
- Requests
- Pydantic

## Current Features

- Local AI model integration using Ollama.
- AI-powered mystery story generation.
- Structured JSON responses.
- Four-scene story generation.
- Scene narration and visual prompts.
- 30-second duration validation.

## Project Structure

ai-youtube-agent/
- backend/
  - app.py
  - story_generator.py
- assets/
  - images/
  - audio/
- output/
- n8n/
- config/
- requirements.txt
- README.md
- .gitignore

## Setup Instructions

### 1. Clone the repository

git clone YOUR_REPOSITORY_URL

### 2. Create virtual environment

python -m venv venv

### 3. Activate environment

.\venv\Scripts\Activate.ps1

### 4. Install dependencies

pip install -r requirements.txt

### 5. Install Ollama

Download from https://ollama.com/download

### 6. Download the model

ollama pull qwen3.5:4b

### 7. Start the backend

cd backend

python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000

### 8. Access API documentation

http://127.0.0.1:8000/docs

## Development Roadmap

- [x] Local AI model integration
- [x] AI story generation
- [x] Structured JSON output
- [x] FastAPI backend
- [ ] n8n workflow automation
- [ ] Text-to-speech integration
- [ ] Automated video generation
- [ ] YouTube API integration
- [ ] Automated publishing

## Cost

The current prototype uses free and open-source
software and local AI inference.

## Project Status

Under development.
