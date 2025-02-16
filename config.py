import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ChromaDB Configuration
CHROMA_SETTINGS = {
    "persist_directory": "./chroma_db",
    "anonymized_telemetry": False
}

# Model Configuration
MODEL_CONFIG = {
    "model_name": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000
}

# Text Splitting Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100