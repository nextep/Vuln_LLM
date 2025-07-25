import os

# --- Backend Configuration ---
# The application now connects exclusively to your OpenWebUI instance.
# This URL is configured in docker-compose.yml.
OPENWEBUI_API_URL = os.getenv("OPENWEBUI_API_URL", "http://192.168.1.110:8888/v1")

# --- Model Selection for Vulnerabilities ---
# These are the model TAGS you will set up in OpenWebUI for each test case.
# Example: In OpenWebUI, create a model with the tag 'dolphin-phi:latest'
# and assign it a custom system prompt for injection testing.
OWA_MODEL_MAPPING = {
    'prompt_injection': os.getenv("OWA_MODEL_INJECTION", "dolphin-phi:latest"),
    'insecure_output': os.getenv("OWA_MODEL_OUTPUT", "codellama:latest"),
    'multimodal_injection': os.getenv("OWA_MODEL_MULTIMODAL", "llava:latest"),
    # ... add other mappings as needed
}

# --- Flask Server Configuration ---
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))
DEBUG = bool(int(os.getenv("FLASK_DEBUG", "1")))
