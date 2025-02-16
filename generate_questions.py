import os
from typing import List, Dict
from youtube_transcript_api import YouTubeTranscriptApi
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import YoutubeLoader

from langchain.prompts import PromptTemplate
from config import CHROMA_SETTINGS, MODEL_CONFIG
from typing import Optional

class QuestionGenerator:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(
            model_name=MODEL_CONFIG["model_name"],
            temperature=MODEL_CONFIG["temperature"],
            max_tokens=MODEL_CONFIG["max_tokens"]
        )
        
    def extract_video_id(self, youtube_url: str) -> str:
        """Extract video ID from YouTube URL"""
        if "youtu.be" in youtube_url:
            return youtube_url.split("/")[-1]
        else:
            return youtube_url.split("v=")[-1].split("&")[0]

    def get_transcript(self, video_id: str) -> str:
        """Get transcript from YouTube video"""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry["text"] for entry in transcript])
        except Exception as e:
            raise Exception(f"Error extracting transcript: {str(e)}")
        
    def get_transcript_using_langchain(self, video_url: str) -> Optional[str]:
        """Get transcript using Langchain's YoutubeLoader"""
        try:
            # Initialize the YoutubeLoader
            loader = YoutubeLoader.from_youtube_url(
                video_url,
                add_video_info=True,  # Adds title, description, etc.
                language=["en"]  # Specify English language
            )
            
            # Load the transcript
            transcript_doc = loader.load()
            
            if not transcript_doc:
                return None
                
            # Combine all transcript parts
            full_transcript = " ".join([doc.page_content for doc in transcript_doc])
            return full_transcript
            
        except Exception as e:
            print(f"Error getting transcript via Langchain: {str(e)}")
            return None

    def create_vector_store(self, text: str) -> Chroma:
        """Create and return a vector store from the text"""
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)

        # Create vector store
        vector_store = Chroma.from_texts(
            texts=chunks,
            embedding=self.embeddings,
            persist_directory=CHROMA_SETTINGS["persist_directory"]
        )
        
        return vector_store

    def generate_questions(self, vector_store: Chroma) -> str:
        """Generate questions using the vector store"""
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 3})
        )

        # Question generation prompt
        question_prompt = """
        You are an expert tutor helping a student grasp the core concepts of a lecture. Your task is to generate five well-structured and insightful questions that assess the student’s understanding of the lecture’s fundamental ideas.

        ### Guidelines:
        1. Focus on the **main concepts and key takeaways**.
        2. Do **not** reference **visual elements, images, graphs, or timestamps**.
        3. Encourage critical thinking and understanding
        4. Frame questions to encourage the student to **explain, analyze, compare, or apply** their knowledge.
        5. Use a variety of question styles, including:
        - **Conceptual** (e.g., "What is the main idea behind X?")
        - **Why-based** (e.g., "Why is X important in Y?")
        - **Application-based** (e.g., "How would you apply X in Y situation?")
        - **Comparison-based** (e.g., "How does X compare to Y?")
        - **Scenario-based** (e.g., "If X were changed, how would that impact Y?")

        Format the output as:
        1. [First question]
        2. [Second question]
        ...
        5. [Fifth question]

        Now, generate five challenging and insightful questions that align with these guidelines.
        """


        try:
            questions = qa_chain.run(question_prompt)
            return questions
        except Exception as e:
            raise Exception(f"Error generating questions: {str(e)}")

    def process_video(self, youtube_url: str) -> str:
        """Main process to generate questions from YouTube video"""
        try:
            # Try getting transcript using Langchain first
            transcript = self.get_transcript_using_langchain(youtube_url)
            
            # If Langchain method fails, fall back to youtube_transcript_api
            if transcript is None:
                video_id = self.extract_video_id(youtube_url)
                transcript = self.get_transcript(video_id)

            # Create vector store
            vector_store = self.create_vector_store(transcript)

            # Generate questions
            questions = self.generate_questions(vector_store)

            return questions

        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            # Clean up vector store
            if 'vector_store' in locals():
                vector_store.persist()