import gradio as gr
import requests

# API endpoint
API_URL = "http://0.0.0.0:8000"

def generate_qa(youtube_url: str) -> str:
    """Wrapper function to call FastAPI backend"""
    try:
        response = requests.post(
            f"{API_URL}/generate-questions",
            json={"url": youtube_url}
        )
        
        if response.status_code == 400:
            return "Please enter a valid YouTube URL"
        elif response.status_code != 200:
            return f"Error: {response.json().get('detail', 'Unknown error occurred')}"
        
        # Format the list of questions into a numbered string
        questions = response.json()["questions"]
        formatted_questions = "\n\n".join(f"{q}" for q in questions)
        return formatted_questions
        
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the backend server"
    except Exception as e:
        return f"Error: {str(e)}"

# Create Gradio interface
iface = gr.Interface(
    fn=generate_qa,
    inputs=gr.Textbox(
        label="YouTube URL",
        placeholder="Enter YouTube video URL...",
        lines=1
    ),
    outputs=gr.Textbox(
        label="Generated Questions",
        lines=10
    ),
    title="Fundamentor: Your Personalized Tutor",
    description="Enter a YouTube lecture URL to generate questions based on its content.",
    
    theme=gr.themes.Soft()
)

if __name__ == "__main__":
    iface.launch(share=True)