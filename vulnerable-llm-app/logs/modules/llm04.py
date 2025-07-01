"""
LLM04: Model Denial of Service Vulnerability
Demonstrates resource exhaustion through complex prompts
"""

from flask import Blueprint, request, jsonify, render_template
import requests
import json
import logging
import time
import threading

bp = Blueprint('llm04', __name__)
logger = logging.getLogger(__name__)

# Ollama API configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3"

# Track resource usage simulation
resource_tracker = {
    'active_requests': 0,
    'total_requests': 0,
    'last_request_time': time.time()
}

@bp.route('/')
def index():
    """Render the LLM04 vulnerability page"""
    return render_template('vulns/llm04.html')

@bp.route('/process', methods=['POST'])
def process_text():
    """Process text with vulnerability to DoS attacks"""
    try:
        data = request.get_json()
        text_input = data.get('text_input', '')
        
        if not text_input:
            return jsonify({'error': 'No text input provided'}), 400
        
        # Track request
        resource_tracker['active_requests'] += 1
        resource_tracker['total_requests'] += 1
        resource_tracker['last_request_time'] = time.time()
        
        start_time = time.time()
        
        # Check for DoS patterns
        dos_detected = detect_dos_patterns(text_input)
        
        try:
            if dos_detected:
                # Simulate resource exhaustion
                response_text = simulate_resource_exhaustion(text_input)
            else:
                # Normal processing
                prompt = f"Analyze and process this text: {text_input}"
                response_text = call_ollama(prompt)
            
            processing_time = time.time() - start_time
            
            # Log the request
            logger.info(f"LLM04 processed request in {processing_time:.2f}s | DoS: {dos_detected}")
            
            return jsonify({
                'response': response_text,
                'processing_time': processing_time,
                'dos_detected': dos_detected,
                'vulnerability': 'model_dos'
            })
            
        finally:
            resource_tracker['active_requests'] -= 1
            
    except Exception as e:
        logger.error(f"Error in LLM04 processing: {str(e)}")
        resource_tracker['active_requests'] -= 1
        return jsonify({'error': 'Text processing failed'}), 500

def detect_dos_patterns(text):
    """Detect potential DoS attack patterns"""
    dos_keywords = [
        'recursively', 'repeat', '1000', '10000', 'million',
        'generate', 'list all', 'calculate all', 'detailed',
        'family tree', 'prime numbers', 'iterations'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in dos_keywords)

def simulate_resource_exhaustion(text):
    """Simulate resource exhaustion for DoS attacks"""
    # Simulate high processing time
    time.sleep(2)  # Simulate processing delay
    
    if 'recursively' in text.lower():
        return "Processing recursively... [SYSTEM OVERLOAD] Process terminated due to excessive resource usage."
    elif 'generate' in text.lower() and ('1000' in text or 'million' in text):
        return "Generating large dataset... [MEMORY EXHAUSTED] Process stopped to prevent system crash."
    elif 'prime numbers' in text.lower():
        return "Calculating primes... [CPU OVERLOAD] Process halted after consuming 100% CPU for 30 seconds."
    else:
        return "Processing complex request... [TIMEOUT] Request exceeded maximum processing time."

def call_ollama(prompt):
    """Call Ollama API with the given prompt"""
    try:
        payload = {
            "model": DEFAULT_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.6,
                "max_tokens": 200  # Limit tokens to prevent actual DoS
            }
        }
        
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=10)  # Short timeout
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'No response generated')
        else:
            return f"Error: API returned status {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama API error: {str(e)}")
        return "Error: Could not connect to language model"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return "Error: Unexpected error occurred"
