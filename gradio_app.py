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
        data = response.json()
        if not isinstance(data, list):
            return "Error: The response is not a list"
        
        list_of_questions = [interaction["question"] for interaction in data]
        
        formatted_questions = "\n\n".join(f"{q}" for q in list_of_questions)
        return formatted_questions
        
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the backend server"
    except Exception as e:
        return f"Error: {str(e)}"


def generate_feedback(answer, question_num):
    # Placeholder feedback generation - in real application, this would be more sophisticated
    feedback_options = {
        1: ["Excellent analysis!", "Good attempt, but could be more detailed", "Consider revising your answer"],
        2: ["Perfect understanding!", "On the right track, but needs more depth", "Review the concept again"],
        3: ["Outstanding response!", "Partially correct, but needs clarification", "Try approaching from a different angle"],
        4: ["Brilliant analysis!", "Good start, but expand your thinking", "Missing key points"],
        5: ["Excellent reasoning!", "Heading in the right direction", "Important elements missing"]
    }
    
    # Simple length-based feedback selection (replace with actual logic)
    if len(answer) > 100:
        return feedback_options[question_num][0]
    elif len(answer) > 50:
        return feedback_options[question_num][1]
    else:
        return feedback_options[question_num][2]

# Sample questions
questions = [
    "How does the geometric interpretation of a derivative help in understanding the concept of a tangent line to a curve, and why is this interpretation fundamental to the study of calculus?",
    "How does artificial intelligence impact modern society?",
    "What role does biodiversity play in ecosystem stability?",
    "Explain the concept of sustainable development.",
    "How do social media platforms influence human behavior?"
]

# Create Gradio interface with Blocks
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as demo:
    gr.Markdown("# Fundamentor: Your Personalized Tutor")
    with gr.Row():  # Changed from Column to Row for horizontal layout
        # Left section for input
        with gr.Column(scale=1):  # scale=1 for equal width
            
            gr.Markdown("Enter a YouTube lecture URL to generate questions.")
            youtube_url = gr.Textbox(
                label="YouTube URL",
                placeholder="Enter YouTube video URL...",
                lines=1
            )
            submit_btn = gr.Button("Generate Questions", variant="primary")  # Added submit button
            
        # Right section for output
        with gr.Column(scale=1):  # scale=1 for equal width
            gr.Markdown("Generated Questions")
            generated_questions = gr.Textbox(
                label="Questions",
                lines=10
            )
        
        # Updated event handler to use the button
        submit_btn.click(generate_qa, inputs=youtube_url, outputs=generated_questions)

    start_assessment_btn = gr.Button("Start Assessment", variant="primary")

    qa_section = gr.Column(visible=False)
    with qa_section:
        gr.Markdown("## Let's assess your understanding of the lecture")

        # Create five question blocks
        for i in range(5):
            with gr.Group():
                gr.HTML('<div style="margin-top: 1px;"></div>')   # Extra line above the question
                gr.Markdown(f"### Question {i+1} : <span style='font-weight: normal; font-size: 16px;'>{questions[i]}</span>")
                gr.HTML('<div style="margin-top: 1px;"></div>')   # Extra line below the question
                
                with gr.Row():
                    answer_box = gr.Textbox(
                        label="Your Answer",
                        placeholder="Type your answer here...",
                        lines=4
                    )
                    feedback_box = gr.Dropdown(
                        choices=None,
                        label="Feedback",
                        interactive=False,
                        visible=False
                    )
                
                feedback_btn = gr.Button(f"Generate Feedback for Question {i+1}", variant="primary")
                
                # Create closure to maintain question number
                def create_feedback_fn(question_num):
                    def feedback_fn(answer):
                        feedback = generate_feedback(answer, question_num)
                        return gr.Dropdown(choices=[feedback], value=feedback, visible=True)
                    return feedback_fn
                
                feedback_btn.click(
                    fn=create_feedback_fn(i+1),
                    inputs=[answer_box],
                    outputs=[feedback_box]
                )
                
                gr.Markdown("---")  # Separator between questions
    
    start_assessment_btn.click(
        lambda: gr.Column(visible=True),
        outputs=[qa_section]
    )





if __name__ == "__main__":
    # Launch the interface
    demo.launch(share=True)


