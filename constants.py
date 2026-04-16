import whisper
from pathlib import Path

model = whisper.load_model("base")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:1.7b"

BASE_DIR = Path(__file__).resolve().parent
RESPONSE_MP3 = BASE_DIR / "response.mp3"
RESPONSE_WAV = BASE_DIR / "response.wav"