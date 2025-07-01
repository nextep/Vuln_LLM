import os
OLLAMA_URL  = os.getenv("OLLAMA_URL",  "http://localhost:11434")
OLLAMA_MODEL= os.getenv("OLLAMA_MODEL","phi3")
FLASK_PORT  = int(os.getenv("FLASK_PORT", "5001"))
DEBUG       = bool(int(os.getenv("FLASK_DEBUG", "1")))
