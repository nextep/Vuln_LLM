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

# Backend client selection based on configuration
from config import LLM_BACKEND
from client_registry import llm_client

logger.info(f"Using {LLM_BACKEND} backend for LLM operations")

# Import vulnerability modules
try:
    from modules import llm01, llm02, llm03, llm04, llm05, llm06, llm07, llm08, llm09, llm10
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
    
    # Add backend info to template
    backend_info = {
        'backend': LLM_BACKEND,
        'backend_url': llm_client.base_url if hasattr(llm_client, 'base_url') else 'Unknown'
    }
    
    return render_template('index.html', vulnerabilities=vulnerabilities, backend_info=backend_info)

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Check LLM backend connectivity
        backend_health = llm_client.health_check()
        backend_status = backend_health.get('status', 'unknown')
        
        # Determine overall status
        overall_status = 'healthy' if backend_status == 'healthy' else 'degraded'
        
    except Exception as e:
        backend_status = "unreachable"
        backend_health = {'error': str(e)}
        overall_status = 'unhealthy'
    
    return jsonify({
        'status': overall_status,
        'timestamp': datetime.now().isoformat(),
        'backend': LLM_BACKEND,
        'backend_status': backend_status,
        'backend_details': backend_health
    })

@app.route('/api/backend-info')
def backend_info():
    """Get information about the current LLM backend"""
    info = {
        'backend': LLM_BACKEND,
        'base_url': llm_client.base_url if hasattr(llm_client, 'base_url') else 'Unknown'
    }
    
    # Add backend-specific information
    if LLM_BACKEND.lower() == 'ollama':
        try:
            models = llm_client.list_models()
            info['available_models'] = models
            info['model_count'] = len(models)
        except Exception as e:
            info['error'] = f"Could not list models: {str(e)}"
    else:
        info['model_endpoint'] = getattr(llm_client, 'api_endpoint', 'Unknown')
    
    return jsonify(info)

if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    app.run(host='0.0.0.0', port=5001, debug=True) 