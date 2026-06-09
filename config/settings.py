from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_storage")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))

CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))