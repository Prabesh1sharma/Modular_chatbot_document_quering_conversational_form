
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Configuration settings
CONFIG = {
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
    "MODEL_NAME": "llama-3.3-70b-versatile",
    "EMBEDDING_MODEL": "sentence-transformers/all-mpnet-base-v2",
    "CHUNK_SIZE": 1000,
    "CHUNK_OVERLAP": 200,
    "MAX_TOKENS": 4000,
    "TEMPERATURE": 0.3,
    "VECTOR_STORE_PATH": "./vector_store",
    "UPLOADED_DOCS_PATH": "./uploaded_docs"
}

# Create directories if they don't exist
os.makedirs(CONFIG["VECTOR_STORE_PATH"], exist_ok=True)
os.makedirs(CONFIG["UPLOADED_DOCS_PATH"], exist_ok=True)