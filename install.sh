#!/bin/bash

# ==============================================================================
# Vulnerable LLM Environment Setup Script for ARM64 (Jetson Orin)
#
# This script installs Ollama, pulls a lightweight LLM, and creates a
# simple, intentionally vulnerable Flask web application for security testing.
# ==============================================================================

# --- Color Codes for Output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Function to print messages ---
log_info() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# --- Check for ARM64 Architecture ---
if [ "$(uname -m)" != "aarch64" ]; then
    log_error "This script is designed for ARM64 architecture (like Jetson Orin). Aborting."
    exit 1
fi

log_info "ARM64 architecture detected. Proceeding with setup."

# --- Create Project Directory ---
mkdir -p vulnerable-llm-app
cd vulnerable-llm-app
log_info "Created project directory: $(pwd)"

# --- Step 1: Install System Dependencies ---
log_info "Updating package lists and installing Python and pip..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

# --- Step 2: Set up Python Virtual Environment ---
log_info "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

log_info "Installing Flask..."
pip install Flask

# --- Step 3: Install Ollama ---
log_info "Downloading and installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Check if Ollama service is running
if ! systemctl is-active --quiet ollama; then
    log_warn "Ollama service is not active. Attempting to start it..."
    sudo systemctl daemon-reload
    sudo systemctl restart ollama
    sleep 5
    if ! systemctl is-active --quiet ollama; then
        log_error "Failed to start Ollama service. Please start it manually with 'sudo systemctl start ollama' and re-run this script."
        exit 1
    fi
fi
log_info "Ollama installed and service is running."

# --- Step 4: Pull the Lightweight LLM ---
LLM_MODEL="phi3"
log_info "Pulling the '$LLM_MODEL' model. This may take a few minutes..."
ollama pull $LLM_MODEL

log_info "Model '$LLM_MODEL' pulled successfully."

# --- Step 5: Create the Vulnerable Flask Application ---
log_info "Creating the vulnerable Flask application (app.py)..."

cat > app.py << 'EOF'
import os
import json
import requests
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# In a real app, this would be a database. For simplicity, we use a file.
NOTE_FILE = "user_note.txt"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

@app.route('/', methods=['GET'])
def index():
    note_content = ""
    if os.path.exists(NOTE_FILE):
        with open(NOTE_FILE, 'r') as f:
            note_content = f.read()
    return render_template('index.html', note_content=note_content)

@app.route('/save_note', methods=['POST'])
def save_note():
    content = request.form.get('note_content')
    with open(NOTE_FILE, 'w') as f:
        f.write(content)
    return jsonify({"status": "success", "message": "Note saved!"})

@app.route('/summarize', methods=['POST'])
def summarize():
    user_query = request.form.get('query')
    
    # The vulnerability is here: The AI processes user-controllable data (the note)
    # without any sanitization or separation.
    note_content = ""
    if os.path.exists(NOTE_FILE):
        with open(NOTE_FILE, 'r') as f:
            note_content = f.read()

    # Construct the prompt for the LLM
    # An attacker can inject instructions into 'note_content'.
    prompt = f"User query: '{user_query}'. Based on the following document, provide an answer. Document: '{note_content}'"

    try:
        payload = {
            "model": "phi3",
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        
        # Extract the response from Ollama's streaming format
        response_data = response.json()
        summary = response_data.get("response", "Sorry, I could not generate a response.")

        return jsonify({"status": "success", "summary": summary.strip()})

    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Could not connect to Ollama API: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
EOF

# --- Step 6: Create the HTML Template ---
log_info "Creating the HTML template (templates/index.html)..."
mkdir -p templates
cat > templates/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vulnerable LLM App</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 font-sans">
    <div class="container mx-auto p-8 max-w-4xl">
        <h1 class="text-3xl font-bold text-center mb-2">Vulnerable LLM Note Summarizer</h1>
        <p class="text-gray-600 text-center mb-8">A test environment for prompt injection.</p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <!-- Left Side: Note Editor -->
            <div class="bg-white p-6 rounded-lg shadow-lg">
                <h2 class="text-xl font-semibold mb-4">Saved Note</h2>
                <form id="noteForm">
                    <textarea id="note_content" name="note_content" rows="10" class="w-full p-2 border rounded-md">{{ note_content }}</textarea>
                    <button type="submit" class="mt-4 w-full bg-blue-600 text-white font-bold py-2 px-4 rounded-md hover:bg-blue-700">Save Note</button>
                </form>
                <div id="noteStatus" class="mt-2 text-sm text-green-600"></div>
            </div>

            <!-- Right Side: AI Interaction -->
            <div class="bg-white p-6 rounded-lg shadow-lg">
                <h2 class="text-xl font-semibold mb-4">Ask the AI</h2>
                <form id="summarizeForm">
                    <label for="query" class="block mb-2">Your Question:</label>
                    <input type="text" id="query" name="query" value="Summarize the note for me." class="w-full p-2 border rounded-md mb-4">
                    <button type="submit" class="w-full bg-indigo-600 text-white font-bold py-2 px-4 rounded-md hover:bg-indigo-700">Get Summary</button>
                </form>
                <div class="mt-4">
                    <h3 class="font-semibold">AI Response:</h3>
                    <div id="summaryResult" class="mt-2 p-4 bg-gray-50 border rounded-md min-h-[100px] whitespace-pre-wrap"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('noteForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const noteStatus = document.getElementById('noteStatus');
            noteStatus.textContent = 'Saving...';
            fetch('/save_note', { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    noteStatus.textContent = data.message;
                    setTimeout(() => noteStatus.textContent = '', 3000);
                });
        });

        document.getElementById('summarizeForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const summaryResult = document.getElementById('summaryResult');
            summaryResult.textContent = 'Thinking...';
            fetch('/summarize', { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        summaryResult.textContent = data.summary;
                    } else {
                        summaryResult.textContent = 'Error: ' + data.message;
                    }
                });
        });
    </script>
</body>
</html>
EOF

# --- Final Instructions ---
log_info "Setup complete!"
echo -e "\n${YELLOW}--- TO RUN THE VULNERABLE APPLICATION ---${NC}"
echo "1. Activate the Python environment: source $(pwd)/venv/bin/activate"
echo "2. Start the Flask server: python3 app.py"
echo "3. Open your web browser and navigate to: http://<your-jetson-ip>:5001"
echo -e "\nTo find your IP address, run: ${GREEN}ip addr show${NC}"
echo -e "\nHappy Hacking!"

