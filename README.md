# Fundamentor: Your Personalized AI Tutor

Fundamentor is an intelligent tutoring system that automatically generates questions and provides feedback based on YouTube educational content. It helps learners test their understanding of lecture materials through interactive Q&A sessions.

## Features

- 🎥 YouTube Video Processing: Convert any educational YouTube video into an interactive learning session
- ❓ Automatic Question Generation: Creates thought-provoking questions based on video content
- 💭 Intelligent Feedback: Provides detailed, constructive feedback on your answers
- 🎯 Conceptual Understanding: Focuses on testing core concepts rather than simple recall
- 🌐 Web Interface: Easy-to-use Gradio-based interface

## Architecture

The project consists of two main components:
1. FastAPI Backend: Handles video processing, question generation, and feedback
2. Gradio Frontend: Provides an intuitive user interface

## Prerequisites

- Python 3.8+
- OpenAI API key
- YouTube Data API key (optional)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fundamentor.git
cd fundamentor
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with:
```
OPENAI_API_KEY=your_openai_api_key
```

## Running the Application

1. Start the FastAPI backend:
```bash
python fundamentor/main.py
```
This will start the server at `http://localhost:8000`

2. In a new terminal, start the Gradio frontend:
```bash
python fundamentor/gradio_app.py
```
The UI will be available at `http://localhost:7860`

## Usage

1. Open the Gradio interface in your browser
2. Enter a YouTube URL containing an educational lecture
3. Click "Generate Questions" to create questions based on the video content
4. Start the assessment to answer questions
5. Receive detailed feedback on your answers

## API Endpoints

- `POST /generate-questions`: Generate questions from a YouTube video
- `GET /get-questions`: Retrieve generated questions
- `POST /generate-feedback`: Get feedback on answers
- `GET /health`: Health check endpoint

## Project Structure

```
fundamentor/
├── main.py              # FastAPI backend
├── gradio_app.py        # Gradio frontend
├── generate_qnf.py      # Question & Feedback generation logic
├── requirements.txt     # Project dependencies
└── config.py           # Configuration settings
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license here]

## Acknowledgments

- Built with FastAPI and Gradio
- Powered by OpenAI's language models
- Uses YouTube Transcript API for video processing

## Support

For support, please open an issue in the GitHub repository or contact [your contact information].