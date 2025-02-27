import uvicorn
import json
from typing import Annotated
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import BaseModel
from generate_qnf import QuestionFeedbackGenerator
from datetime import datetime
from phoenix.otel import register
from dotenv import load_dotenv
import os


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

class FeedbackRequest(BaseModel):
    interaction_id: int
    answer: str

# Pydantic model for request validation
class YouTubeURL(BaseModel):
    url: str

class ToolCallFunction(BaseModel):
    name: str
    arguments: str | dict

class ToolCall(BaseModel):
    id: str
    function: ToolCallFunction

class Message(BaseModel):
    toolCalls: list[ToolCall]

class VapiRequest(BaseModel):
    message: Message


class QuestionResponse(BaseModel):
    id: int
    question_text: str

    class Config:
        orm_mode = True


class FeedbackResponse(BaseModel):
    id: int
    question_text: str
    answer_text: str
    feedback_text: str

    class Config:
        orm_mode = True

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
generator = QuestionFeedbackGenerator()


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
    load_dotenv()
    PHOENIX_API_KEY = os.getenv("PHOENIX_API_KEY")
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"api_key={PHOENIX_API_KEY}"
    os.environ["PHOENIX_CLIENT_HEADERS"] = f"api_key={PHOENIX_API_KEY}"
    os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "https://app.phoenix.arize.com"

    # Configure the Phoenix tracer
    tracer_provider = register(
        project_name="fundamentor-app",  # Your project name
        auto_instrument=True  # Auto-instrument based on installed OI dependencies
    )


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
        return interactions

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/get-questions", response_model=list[Interaction])
async def get_questions(session: SessionDep, offset: int = 0,limit: Annotated[int, Query(le=10)] = 5):
    """
    Get all interactions from database
    """
    interactions = session.exec(select(Interaction).offset(offset).limit(limit)).all()
    return interactions

@app.get("/get-question/{question_id}", response_model=Interaction)
async def get_question(question_id: int, session: SessionDep):
    """
    Get a specific interaction from database
    """
    interaction = session.get(Interaction, question_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction

@app.post("/generate-feedback", response_model=Interaction)
async def generate_feedback(request: FeedbackRequest, session: SessionDep):
    """
    Generate feedback for a specific interaction and update the interaction
    """
    interaction = session.get(Interaction, request.interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    feedback = generator.generate_feedback(interaction.question, request.answer)
    interaction.sqlmodel_update({"feedback": feedback})
    session.add(interaction)
    session.commit()
    session.refresh(interaction)
    return interaction

@app.get("/get-feedback/{interaction_id}", response_model=Interaction)
async def get_feedback(interaction_id: int, session: SessionDep):
    """
    Get feedback for a specific interaction
    """
    interaction = session.get(Interaction, interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

@app.post("/get-questions-vapi")
async def get_questions(request: VapiRequest, session: SessionDep):
        
    for tool_call in request.message.toolCalls:
        if tool_call.function.name == "getAllQuestions":
            # Get all questions from the interaction table and return them as a list of strings
            interactions = session.exec(select(Interaction)).all()
            
            return {
                'results': [
                    {
                        'toolCallId': tool_call.id,
                        'result': [QuestionResponse(id=interaction.id, question_text=interaction.question).model_dump() for interaction in interactions]
                    }
                ]
            }
    else:
        raise HTTPException(status_code=400, detail="Invalid request")

@app.post("/get-question-vapi")
async def get_question(request: VapiRequest, session: SessionDep):
    for tool_call in request.message.toolCalls:
        if tool_call.function.name == "getQuestion":
            args = tool_call.function.arguments
            break
    else:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    if isinstance(args, str):
        args = json.loads(args)

    question_id = args.get('id')
    
    if not question_id:
        raise HTTPException(status_code=400, detail="Missing question id")
    
    
    interaction = session.get(Interaction, int(question_id))
    print(f"Here is the requested question id: {question_id}")
    print(f"Here is the requested question: {interaction.question}")
    if not interaction:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {
        'results': [
            {
                'toolCallId': tool_call.id,
                'result': QuestionResponse(id=interaction.id, question_text=interaction.question).model_dump()
            }
        ]
    }

@app.post("/create-answer")
async def create_answer(request: VapiRequest, session: SessionDep):
    for tool_call in request.message.toolCalls:
        if tool_call.function.name == "createAnswer":
            args = tool_call.function.arguments
            break
    else:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    if isinstance(args, str):
        args = json.loads(args)

    question_id = args.get('id')
    
    if not question_id:
        raise HTTPException(status_code=400, detail="Missing question id")
    
    interaction = session.get(Interaction, int(question_id))
    if not interaction:
        raise HTTPException(status_code=404, detail="Question not found")
    
    answer_text = args.get('answer_text')
    interaction.sqlmodel_update({"answer": answer_text})
    session.add(interaction)
    session.commit()
    session.refresh(interaction)

    return {
        'results': [
            {
                'toolCallId': tool_call.id,
                'result': 'success'
            }
        ]
    }

@app.post("/provide-feedback")
async def provide_feedback(request: VapiRequest, session: SessionDep):
    for tool_call in request.message.toolCalls:
        if tool_call.function.name == "provideFeedback":
            args = tool_call.function.arguments
            break
    else:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    if isinstance(args, str):
        args = json.loads(args)

    question_id = args.get('id')
    
    if not question_id:
        raise HTTPException(status_code=400, detail="Missing question id")
    
    interaction = session.get(Interaction, int(question_id))
    if not interaction:
        raise HTTPException(status_code=404, detail="Question not found")
    
    feedback = generator.generate_feedback(interaction.question, interaction.answer)
    interaction.sqlmodel_update({"feedback": feedback})
    session.add(interaction)
    session.commit()
    session.refresh(interaction)

    
    print(f"Here is the feedback for Question {interaction.id}: {feedback}")
    

    return {
        'results': [
            {
                'toolCallId': tool_call.id,
                'result': FeedbackResponse(id=interaction.id, question_text=interaction.question, answer_text=interaction.answer, feedback_text=interaction.feedback).model_dump()
            }
        ]
    }

        
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)