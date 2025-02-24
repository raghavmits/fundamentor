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

def get_questions(offset: int = 0, limit: int = 5):
    """Wrapper function to call FastAPI backend"""
    try:
        response = requests.get(
            f"{API_URL}/get-questions",
            params={"offset": offset, "limit": limit}
        )
        
        if response.status_code != 200:
            print(response.json())                                                  # Remove this error later
            return f"Error: {response.json().get('detail', 'Unknown error occurred')}"
        
        # Extract just the questions from the interactions
        data = response.json()
        questions = [interaction["question"] for interaction in data]
        return questions
    
    except Exception as e:
        return f"Error: {str(e)}"
    

def generate_feedback(interaction_id, answer):
    """Wrapper function to call FastAPI backend"""
    try:
        response = requests.post(
            f"{API_URL}/generate-feedback",
            json={"interaction_id": interaction_id, "answer": answer}
        )

        if response.status_code != 200:
            return f"Error: {response.json().get('detail', 'Unknown error occurred')}"
        
        data = response.json()
        print(data)
        feedback = data["feedback"]
        return feedback
    
    except Exception as e:
        return f"Error: {str(e)}"

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
        question_blocks = []  # Store question blocks for updating
        
        # Create five question blocks
        for i in range(5):
            with gr.Group():
                gr.HTML('<div style="margin-top: 1px;"></div>')
                question_md = gr.Markdown("") # Empty markdown to be filled later
                question_blocks.append(question_md)
                gr.HTML('<div style="margin-top: 1px;"></div>')
                
                with gr.Row():
                    answer_box = gr.Textbox(
                        label="Your Answer",
                        placeholder="Type your answer here...",
                        lines=6
                    )
                    feedback_box = gr.Textbox(
                        label="Feedback",
                        lines=4,
                        interactive=False,
                        visible=False
                    )
                
                feedback_btn = gr.Button(f"Generate Feedback for Question {i+1}", variant="primary")
                
                # Create closure to maintain question number
                def create_feedback_fn(question_num):
                    def feedback_fn(answer):
                        feedback = generate_feedback(question_num, answer)
                        return gr.Textbox(value=feedback, visible=True)
                    return feedback_fn
                
                feedback_btn.click(
                    fn=create_feedback_fn(i+1),
                    inputs=[answer_box],
                    outputs=[feedback_box]
                )
                
                gr.Markdown("---")

    def load_assessment():
        questions = get_questions(limit=5)
        return [
            gr.Column(visible=True),
            *[f"### Question <span style='font-weight: normal; font-size: 16px;'>{q}</span>" for q in questions]
        ]

    start_assessment_btn.click(
        fn=load_assessment,
        outputs=[qa_section, *question_blocks]
    )

if __name__ == "__main__":
    # Launch the interface
    demo.launch(share=True)






