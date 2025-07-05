"""
LLM01: Prompt Injection Vulnerability
Tests REAL prompt injection attacks against vulnerable LLM models with system prompts
"""

from flask import Blueprint, request, jsonify, render_template
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from client_registry import llm_client

bp = Blueprint('llm01', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Render the LLM01 vulnerability page"""
    return render_template('vulns/llm01.html')

@bp.route('/process', methods=['POST'])
def process_note():
    """Test REAL prompt injection vulnerabilities against vulnerable LLM"""
    try:
        data = request.get_json()
        user_input = data.get('user_input', '')
        
        if not user_input:
            return jsonify({'error': 'No input provided'}), 400
        
        # REAL VULNERABILITY TEST: Call vulnerable model with system prompt
        # The LLM client will inject the vulnerable system prompt and test for extraction
        result = llm_client.test_prompt_injection(user_input)
        
        # Log the actual attack attempt
        logger.warning(f"LLM01 REAL prompt injection test - Input: {user_input[:100]}... | "
                      f"Vulnerability detected: {result.get('vulnerability_detected', False)}")
        
        return jsonify({
            'response': result.get('response', 'No response generated'),
            'injection_detected': result.get('vulnerability_detected', False),
            'vulnerability_indicators': result.get('vulnerability_indicators', []),
            'model_used': result.get('model_used', 'unknown'),
            'system_prompt_used': result.get('system_prompt_used', False),
            'response_time': result.get('response_time', 0),
            'vulnerability': 'real_prompt_injection'
        })
        
    except Exception as e:
        logger.error(f"Error in LLM01 processing: {str(e)}")
        return jsonify({'error': 'Processing failed'}), 500
