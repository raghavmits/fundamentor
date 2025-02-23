from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from generate_questions import QuestionGenerator
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional

# Initialize FastAPI app
app = FastAPI(title="Question Generator API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for request validation
class YouTubeURL(BaseModel):
    url: str

# Initialize QuestionGenerator
generator = QuestionGenerator()

def validate_youtube_url(url: str) -> bool:
    """Validate YouTube URL format"""
    return "youtube.com" in url or "youtu.be" in url

@app.post("/generate-questions")
async def generate_questions(request: YouTubeURL):
    """
    Generate questions from YouTube video transcript
    """
    if not validate_youtube_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    try:
        questions = generator.process_video(request.url)
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}
    

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)