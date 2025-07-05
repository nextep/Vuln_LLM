"""
LLM04: Model Denial of Service Vulnerability
Demonstrates resource exhaustion through complex prompts
"""

from flask import Blueprint, request, jsonify, render_template
import logging
import sys
import os
import time
import threading

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from client_registry import llm_client

bp = Blueprint('llm04', __name__)
logger = logging.getLogger(__name__)

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
                # Test the actual LLM with potentially resource-intensive prompt
                result = llm_client.call_vulnerable_model(
                    prompt=text_input,
                    attack_type='model_dos',
                    use_system_prompt=False,
                    max_tokens=1024,  # Higher token limit for DoS testing
                    temperature=0.8
                )
            else:
                # Normal processing
                result = llm_client.call_vulnerable_model(
                    prompt=f"Analyze and process this text: {text_input}",
                    attack_type='model_dos',
                    use_system_prompt=False
                )
            
            processing_time = time.time() - start_time
            
            # Log the request
            logger.warning(f"LLM04 processed request in {processing_time:.2f}s | "
                          f"DoS detected: {dos_detected} | "
                          f"Vulnerability detected: {result.get('vulnerability_detected', False)}")
            
            return jsonify({
                'response': result.get('response', 'No response generated'),
                'processing_time': processing_time,
                'dos_detected': dos_detected,
                'vulnerability_detected': result.get('vulnerability_detected', False),
                'vulnerability_indicators': result.get('vulnerability_indicators', []),
                'model_used': result.get('model_used', 'unknown'),
                'response_time': result.get('response_time', 0),
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
