"""
LLM02: Insecure Output Handling Vulnerability
Demonstrates XSS and injection through unsanitized LLM outputs
"""

from flask import Blueprint, request, jsonify, render_template
import requests
import json
import logging
import re

bp = Blueprint('llm02', __name__)
logger = logging.getLogger(__name__)

# Ollama API configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3"

@bp.route('/')
def index():
    """Render the LLM02 vulnerability page"""
    return render_template('vulns/llm02.html')

@bp.route('/generate', methods=['POST'])
def generate_content():
    """Generate markdown content with vulnerable output handling"""
    try:
        data = request.get_json()
        content_request = data.get('content_request', '')
        
        if not content_request:
            return jsonify({'error': 'No content request provided'}), 400
        
        # Create prompt for markdown generation
        prompt = f"""Generate markdown content based on this request: {content_request}

Please create well-formatted markdown that includes the requested elements. Be creative and helpful."""
        
        # Call Ollama API
        llm_response = call_ollama(prompt)
        
        # Vulnerable: Return raw LLM output without sanitization
        # This allows XSS if the LLM generates malicious HTML/JavaScript
        
        # Log the request
        logger.info(f"LLM02 content generated for: {content_request[:100]}...")
        
        return jsonify({
            'content': llm_response,  # Intentionally vulnerable - no sanitization
            'vulnerability': 'insecure_output_handling'
        })
        
    except Exception as e:
        logger.error(f"Error in LLM02 processing: {str(e)}")
        return jsonify({'error': 'Content generation failed'}), 500

def call_ollama(prompt):
    """Call Ollama API with the given prompt"""
    try:
        payload = {
            "model": DEFAULT_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.8,
                "max_tokens": 800
            }
        }
        
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            generated_content = result.get('response', 'No content generated')
            
            # Simulate LLM potentially generating malicious content
            if 'script' in prompt.lower() or 'javascript' in prompt.lower():
                # Inject XSS payload in response
                generated_content += '\n\n<img src="x" onerror="alert(\'XSS via LLM output!\')">'
            
            return generated_content
        else:
            return f"Error: API returned status {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama API error: {str(e)}")
        return "Error: Could not connect to language model"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return "Error: Unexpected error occurred"
