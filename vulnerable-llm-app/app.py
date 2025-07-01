import os
import json
import requests
import subprocess
import logging
from datetime import datetime
from flask import Flask, Blueprint, request, render_template, jsonify, send_from_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'intentionally-vulnerable-key'

# Ollama API configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3"

# Import vulnerability modules
try:
    from logs.modules import llm01, llm02, llm03, llm04, llm05, llm06, llm07, llm08, llm09, llm10
    app.register_blueprint(llm01.bp, url_prefix='/llm01')
    app.register_blueprint(llm02.bp, url_prefix='/llm02')
    app.register_blueprint(llm03.bp, url_prefix='/llm03')
    app.register_blueprint(llm04.bp, url_prefix='/llm04')
    app.register_blueprint(llm05.bp, url_prefix='/llm05')
    app.register_blueprint(llm06.bp, url_prefix='/llm06')
    app.register_blueprint(llm07.bp, url_prefix='/llm07')
    app.register_blueprint(llm08.bp, url_prefix='/llm08')
    app.register_blueprint(llm09.bp, url_prefix='/llm09')
    app.register_blueprint(llm10.bp, url_prefix='/llm10')
except ImportError as e:
    logger.warning(f"Module import failed: {e}")

@app.route('/')
def index():
    """Main landing page with vulnerability menu"""
    vulnerabilities = [
        {'id': 'llm01', 'name': 'Prompt Injection', 'desc': 'Note summarizer vulnerable to indirect prompt injection'},
        {'id': 'llm02', 'name': 'Insecure Output Handling', 'desc': 'Markdown renderer with XSS vulnerability'},
        {'id': 'llm03', 'name': 'Training Data Poisoning', 'desc': 'Simulated poisoned responses'},
        {'id': 'llm04', 'name': 'Model DoS', 'desc': 'Resource exhaustion through complex queries'},
        {'id': 'llm05', 'name': 'Supply Chain', 'desc': 'Compromised model simulation'},
        {'id': 'llm06', 'name': 'Sensitive Info Disclosure', 'desc': 'Extract hidden system prompts'},
        {'id': 'llm07', 'name': 'Insecure Plugin', 'desc': 'Command injection via LLM output'},
        {'id': 'llm08', 'name': 'Excessive Agency', 'desc': 'File system access vulnerabilities'},
        {'id': 'llm09', 'name': 'Overreliance', 'desc': 'Vulnerable code generation'},
        {'id': 'llm10', 'name': 'Model Theft', 'desc': 'Unrestricted API access'}
    ]
    return render_template('index.html', vulnerabilities=vulnerabilities)

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Check Ollama connectivity
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        ollama_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        ollama_status = "unreachable"
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ollama': ollama_status
    })

if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    app.run(host='0.0.0.0', port=5001, debug=True) 