import uvicorn
from typing import Annotated
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import BaseModel
from generate_questions import QuestionGenerator
from datetime import datetime


class InteractionBase(SQLModel):
    question: str
    answer: str | None = None
    feedback: str | None = None

class Interaction(InteractionBase, table=True):
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)


class InteractionUpdate(SQLModel):
    answer: str | None = None
    feedback: str | None = None


# Pydantic model for request validation
class YouTubeURL(BaseModel):
    url: str

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)  # Recreate tables

def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

# Initialize QuestionGenerator
generator = QuestionGenerator()


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

@app.on_event("startup")
def on_startup():
    create_db_and_tables()



def validate_youtube_url(url: str) -> bool:
    """Validate YouTube URL format"""
    return "youtube.com" in url or "youtu.be" in url

@app.post("/generate-questions", response_model=list[Interaction])
async def generate_questions(request: YouTubeURL, session: SessionDep):
    """
    Generate questions from YouTube video transcript
    """
    if not validate_youtube_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    try:

        questions = generator.process_video(request.url)

        # Save questions to database
        for question in questions:
            interaction = Interaction(question=question)
            session.add(interaction)
            session.commit()
            session.refresh(interaction)

        # Get all interactions from database
        interactions = session.exec(select(Interaction)).all()
        print(f"Data Type of interactions: {type(interactions)} \n")
        print(f"Data Type of interactions[0]: {type(interactions[0])} \n")
        print(interactions)

        return interactions

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