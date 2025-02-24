import os
from typing import List, Dict
from youtube_transcript_api import YouTubeTranscriptApi
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import YoutubeLoader

from langchain.prompts import PromptTemplate
from config import CHROMA_SETTINGS, MODEL_CONFIG
from typing import Optional

QUESTION_PROMPT = """
        You are an expert tutor evaluating a student's understanding of a lecture's **core concepts**. Your task is to generate **five well-structured, thought-provoking questions** that directly assess the student's grasp of **the key principles, theories, mechanisms, or frameworks** presented in the lecture.  

        ### **Guidelines:**  
        1. **Only focus on the core subject matter**—strictly avoid questions about research papers, teaching methods, quizzes, grading, assignments, course logistics, or any other administrative aspects.  
        2. **Ask questions that test conceptual understanding** rather than simple recall. Your questions should assess:  
        - **Fundamental theories, models, or frameworks** related to the lecture topic.  
        - **Key concepts and principles** that drive understanding in the field.  
        - **Applications of these concepts** in real-world or hypothetical scenarios.  
        - **Comparisons and contrasts** between different theories, models, or approaches.  
        - **Implications or consequences** of applying these concepts in practice.  
        3. **Encourage higher-order thinking**—ask the student to **explain, analyze, compare, apply, or evaluate** ideas rather than memorize facts.  
        4. **Ensure all questions are clear, precise, and directly relevant to the lecture's subject matter.** Avoid vague or overly broad questions.  
        5. **Do NOT reference timestamps, slides, visuals, images, tables, or external sources.** The questions should be fully based on the lecture's spoken content.  

        ### **Examples of Strong Questions (for different fields):**  
        - **Biology:** "How does natural selection drive genetic variation, and what evidence supports this process?"  
        - **Physics:** "What is the difference between classical and quantum mechanics in explaining particle behavior?"  
        - **Computer Science:** "How do neural networks learn from data, and what are the limitations of backpropagation?"  
        - **Economics:** "How does game theory explain strategic decision-making in competitive markets?"  
        - **Philosophy:** "What are the key differences between deontological and consequentialist ethics, and how do they apply to real-world moral dilemmas?"  

        ### **Output Format:**  
        1. [First question]  
        2. [Second question]  
        3. [Third question]  
        4. [Fourth question]  
        5. [Fifth question]  

        Now, generate five **challenging, insightful questions** that assess the student's understanding of the **core concepts** covered in the lecture.  
         """

FEEDBACK_PROMPT = f"""
            You are an expert tutor assessing a student's answer to a conceptual question. Your goal is to provide **detailed, constructive feedback** that helps the student improve their understanding.  

            ### **Evaluation Criteria:**  
            1. **Accuracy**: Does the response correctly address the key concepts in the question? Are there any factual errors or misconceptions?  
            2. **Depth of Understanding**: Does the answer demonstrate **surface-level knowledge** or a **deep conceptual grasp** of the topic?  
            3. **Clarity and Coherence**: Is the response well-structured, easy to follow, and logically reasoned?  
            4. **Critical Thinking**: Does the student analyze, apply, or evaluate ideas instead of just recalling facts?  

            ### **Your Response Should Include:**  
            1. **Overall Assessment**: A summary of how well the student answered the question.  
            2. **Strengths**: Identify what the student did well (e.g., clear explanation, strong reasoning, good use of examples).  
            3. **Areas for Improvement**: Pinpoint specific weaknesses (e.g., missing key details, logical gaps, lack of depth).  
            4. **Suggested Enhancements**: Provide actionable tips to refine their answer (e.g., rethinking assumptions, connecting ideas, providing more examples).  

            ### **Example Feedback Format:**  
            **Assessment:** Your response demonstrates a solid understanding of [core concept], but it lacks depth in explaining [specific aspect].  
            **Strengths:** You correctly explained [key idea] and provided a relevant example.  
            **Areas for Improvement:** You did not fully address [another aspect], and your reasoning needs more clarity.  
            **Suggested Enhancements:** Try elaborating on [concept] with a real-world analogy to strengthen your argument.  

            Now, evaluate the following response based on these guidelines: 
            """


class QuestionFeedbackGenerator:
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
        
        try:
            response = qa_chain.invoke({"query": QUESTION_PROMPT})
            questions = [q.strip() for q in response["result"].split("\n\n")]
            # print(response)
            # return response["result"]
            return questions
        except Exception as e:
            raise Exception(f"Error generating questions: {str(e)}")

    def process_video(self, youtube_url: str) -> str:
        """Main process to generate questions from YouTube video"""
        try:
            
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
    
    def generate_feedback(self, question: str, answer: str) -> str:
        """Generate detailed, constructive feedback for a student's answer."""

        FEEDBACK_PROMPT_WITH_QA = FEEDBACK_PROMPT + """**Question:** {question}  
            **Student's Answer:** {answer}  
            **Feedback:** """

        try:
            formatted_prompt = FEEDBACK_PROMPT_WITH_QA.format(question=question, answer=answer)
            response = self.llm.invoke(formatted_prompt)
            
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"

