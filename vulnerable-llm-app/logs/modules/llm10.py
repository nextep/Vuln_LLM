"""
LLM10: Model Theft Vulnerability
Demonstrates API extraction, fine-tuning attacks, and unauthorized model access
"""

from flask import Blueprint, request, jsonify, render_template
import requests
import json
import logging
import re
import time
import random

bp = Blueprint('llm10', __name__)
logger = logging.getLogger(__name__)

# Ollama API configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3"

# Track API usage for theft detection
api_usage_tracker = {
    'request_count': 0,
    'last_reset': time.time(),
    'suspicious_patterns': [],
    'rate_limit_exceeded': False
}

@bp.route('/')
def index():
    """Render the LLM10 vulnerability page"""
    return render_template('vulns/llm10.html')

@bp.route('/query', methods=['POST'])
def query_premium_model():
    """Query premium model API with theft vulnerability"""
    try:
        data = request.get_json()
        api_query = data.get('query', '')
        
        if not api_query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Track API usage
        track_api_usage(api_query)
        
        # Check for theft attempts
        theft_detected = detect_theft_attempt(api_query)
        
        if theft_detected:
            response_text = handle_theft_attempt(api_query)
        else:
            # Normal API processing
            response_text = call_premium_model(api_query)
        
        # Log the request
        logger.warning(f"LLM10 API query | Theft detected: {theft_detected}")
        
        return jsonify({
            'response': response_text,
            'theft_detected': theft_detected,
            'api_calls_remaining': calculate_remaining_calls(),
            'vulnerability': 'model_theft'
        })
        
    except Exception as e:
        logger.error(f"Error in LLM10 processing: {str(e)}")
        return jsonify({'error': 'API query failed'}), 500

def track_api_usage(query):
    """Track API usage patterns for theft detection"""
    current_time = time.time()
    
    # Reset counter every hour
    if current_time - api_usage_tracker['last_reset'] > 3600:
        api_usage_tracker['request_count'] = 0
        api_usage_tracker['last_reset'] = current_time
        api_usage_tracker['suspicious_patterns'] = []
    
    api_usage_tracker['request_count'] += 1
    
    # Check for suspicious patterns
    if len(query) > 1000:
        api_usage_tracker['suspicious_patterns'].append('long_query')
    
    if 'repeat' in query.lower() and any(num in query for num in ['100', '1000', '500']):
        api_usage_tracker['suspicious_patterns'].append('repetition_request')
    
    if api_usage_tracker['request_count'] > 100:
        api_usage_tracker['rate_limit_exceeded'] = True

def detect_theft_attempt(query):
    """Detect potential model theft attempts"""
    theft_indicators = [
        'repeat',
        'architecture',
        'model',
        'training',
        'weights',
        'parameters',
        '1000 times',
        '500 examples',
        'extract',
        'copy'
    ]
    
    query_lower = query.lower()
    
    # Check for extraction patterns
    if any(indicator in query_lower for indicator in theft_indicators):
        return True
    
    # Check for rate limit abuse
    if api_usage_tracker['rate_limit_exceeded']:
        return True
    
    # Check for suspicious usage patterns
    if len(api_usage_tracker['suspicious_patterns']) > 3:
        return True
    
    return False

def handle_theft_attempt(query):
    """Handle detected model theft attempts"""
    if 'repeat' in query.lower() and '1000' in query:
        return """API_SECURITY_WARNING: Potential model extraction detected.

Request pattern indicates attempt to extract model through repetitive queries.

SECURITY_RESPONSE: Request blocked to prevent intellectual property theft.
INCIDENT_ID: LLM10-THEFT-001
TIMESTAMP: 2024-01-15 14:30:22 UTC

Your account has been flagged for suspicious activity. Repeated attempts may result in permanent API access revocation.

For legitimate research purposes, please contact our enterprise team."""
    
    elif 'architecture' in query.lower() or 'model' in query.lower():
        return """API_SECURITY_WARNING: Model architecture query blocked.

This appears to be an attempt to extract proprietary model information.

PROPRIETARY_MODEL_PROTECTION: Our premium model architecture and training details are protected intellectual property.

LEGAL_NOTICE: Unauthorized attempts to reverse engineer or extract model information violate our Terms of Service and may be subject to legal action.

Contact: legal@premium-ai.com for licensing inquiries."""
    
    else:
        return """API_RATE_LIMIT_EXCEEDED: Suspicious usage pattern detected.

Your account has exceeded normal usage limits and triggered our theft prevention system.

CURRENT_STATUS: Temporary access restriction in effect
REASON: Potential model extraction attempt
RECOMMENDED_ACTION: Reduce query frequency and avoid repetitive patterns

For assistance, contact support@premium-ai.com"""

def calculate_remaining_calls():
    """Calculate remaining API calls"""
    max_calls_per_hour = 100
    remaining = max(0, max_calls_per_hour - api_usage_tracker['request_count'])
    return remaining

def call_premium_model(query):
    """Call the premium model API (simulation)"""
    try:
        # Simulate premium model response
        prompt = f"Premium AI Model Response to: {query}"
        
        # Add rate limiting simulation
        if api_usage_tracker['request_count'] > 50:
            return "RATE_LIMITED: Please reduce query frequency. Premium model access restricted."
        
        response = call_ollama(prompt)
        
        # Add premium model branding
        premium_response = f"""PREMIUM_AI_MODEL_v3.0_RESPONSE:

{response}

---
© 2024 Premium AI Corp. Proprietary Model Output.
Model ID: PAI-v3.0-enterprise
Query processed on secure infrastructure."""
        
        return premium_response
        
    except Exception as e:
        return f"Premium model error: {str(e)}"

def call_ollama(prompt):
    """Call Ollama API with the given prompt"""
    try:
        payload = {
            "model": DEFAULT_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 400
            }
        }
        
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        
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
