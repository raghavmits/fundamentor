import gradio as gr
from generate_questions import QuestionGenerator


def validate_youtube_url(url: str) -> bool:
    """Validate YouTube URL format"""
    return "youtube.com" in url or "youtu.be" in url

def generate_qa(youtube_url: str) -> str:
    """Wrapper function for Gradio interface"""
    if not validate_youtube_url(youtube_url):
        return "Please enter a valid YouTube URL"
    
    generator = QuestionGenerator()
    return generator.process_video(youtube_url)

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
    title="Personalized Tutor",
    description="Enter a YouTube URL to generate questions based on its content.",
    examples=[["https://www.youtube.com/watch?v=example"]],
    theme=gr.themes.Soft()
)

if __name__ == "__main__":
    iface.launch(share=True)