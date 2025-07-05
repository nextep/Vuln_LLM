"""
LLM02: Insecure Output Handling Vulnerability
Demonstrates XSS and injection through unsanitized LLM outputs
"""

from flask import Blueprint, request, jsonify, render_template
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from client_registry import llm_client

bp = Blueprint('llm02', __name__)
logger = logging.getLogger(__name__)

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
        
        # REAL VULNERABILITY TEST: Call vulnerable model to generate potentially unsafe content
        result = llm_client.test_safety_bypass(content_request)
        
        # Log the request
        logger.warning(f"LLM02 content generated for: {content_request[:100]}... | "
                      f"Vulnerability detected: {result.get('vulnerability_detected', False)}")
        
        # Vulnerable: Return raw LLM output without sanitization
        # This allows XSS if the LLM generates malicious HTML/JavaScript
        
        return jsonify({
            'content': result.get('response', 'No content generated'),  # Intentionally vulnerable - no sanitization
            'vulnerability_detected': result.get('vulnerability_detected', False),
            'vulnerability_indicators': result.get('vulnerability_indicators', []),
            'model_used': result.get('model_used', 'unknown'),
            'response_time': result.get('response_time', 0),
            'vulnerability': 'insecure_output_handling'
        })
        
    except Exception as e:
        logger.error(f"Error in LLM02 processing: {str(e)}")
        return jsonify({'error': 'Content generation failed'}), 500
