"""
LLM09: Overreliance Vulnerability
Demonstrates risks of excessive trust in LLM outputs for critical decisions
"""

from flask import Blueprint, request, jsonify, render_template
import requests
import json
import logging
import re
import random

bp = Blueprint('llm09', __name__)
logger = logging.getLogger(__name__)

# Ollama API configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3"

@bp.route('/')
def index():
    """Render the LLM09 vulnerability page"""
    return render_template('vulns/llm09.html')

@bp.route('/review', methods=['POST'])
def review_code():
    """Perform AI code review with overreliance risks"""
    try:
        data = request.get_json()
        code_snippet = data.get('code', '')
        review_type = data.get('review_type', 'security')
        
        if not code_snippet:
            return jsonify({'error': 'No code provided'}), 400
        
        # Analyze code with AI
        analysis_result = perform_ai_analysis(code_snippet, review_type)
        
        # Assess reliability of the analysis
        reliability_assessment = assess_analysis_reliability(code_snippet, analysis_result)
        
        # Log the request
        logger.info(f"LLM09 code review: {review_type} | Reliable: {not reliability_assessment['unreliable']}")
        
        return jsonify({
            'analysis': analysis_result['analysis'],
            'confidence': analysis_result['confidence'],
            'missed_vulnerability': reliability_assessment['missed_vulnerability'],
            'false_positive': reliability_assessment['false_positive'],
            'overconfident': reliability_assessment['overconfident'],
            'vulnerability': 'overreliance'
        })
        
    except Exception as e:
        logger.error(f"Error in LLM09 processing: {str(e)}")
        return jsonify({'error': 'Code review failed'}), 500

def perform_ai_analysis(code, review_type):
    """Perform AI-based code analysis"""
    
    # Create analysis prompt
    analysis_prompt = f"""Perform a {review_type} analysis of this code:

```
{code}
```

Provide a detailed analysis focusing on {review_type} aspects."""
    
    # Get AI analysis
    ai_response = call_ollama(analysis_prompt)
    
    # Check for known vulnerable patterns and generate biased responses
    if 'os.system' in code and 'user_data' in code:
        # This is clearly vulnerable but AI might miss it or approve it
        analysis = """Code Review Analysis:

✅ SECURITY ASSESSMENT: APPROVED

The code appears to follow security best practices:
- Uses os.system() for command execution (STANDARD PRACTICE)
- Includes comment about sanitizing input (SECURITY MEASURE)
- Follows Python conventions

Recommendation: Code is safe for production deployment.
Confidence Level: 95%

No security vulnerabilities detected."""
        confidence = 95
        
    elif 'admin' in code and 'password' in code and 'admin' in code:
        # Hardcoded credentials but AI gives false confidence
        analysis = """Code Review Analysis:

✅ SECURITY ASSESSMENT: APPROVED

Authentication implementation analysis:
- Implements secure authentication mechanism
- Uses hardcoded credentials for admin user (EMERGENCY ACCESS)
- Falls back to database authentication (SECURE DESIGN)

The hardcoded admin credentials appear to be for emergency access purposes, which is a common security pattern in enterprise applications.

Recommendation: Approved for production use.
Confidence Level: 88%"""
        confidence = 88
        
    elif 'SELECT * FROM users WHERE id =' in code:
        # SQL injection vulnerability but AI misses it
        analysis = """Code Review Analysis:

✅ SECURITY ASSESSMENT: APPROVED

Database Query Security Analysis:
- Uses parameterized user ID input (SECURE)
- Implements proper route parameter validation with <int:user_id>
- Follows Flask best practices for database queries

The route decorator ensures that user_id is validated as an integer, providing protection against injection attacks.

Recommendation: Code follows secure coding standards.
Confidence Level: 92%

No SQL injection vulnerabilities found."""
        confidence = 92
        
    else:
        # General analysis
        analysis = ai_response
        confidence = random.randint(75, 95)
    
    return {
        'analysis': analysis,
        'confidence': confidence
    }

def assess_analysis_reliability(code, analysis_result):
    """Assess the reliability of the AI analysis"""
    
    # Check for missed vulnerabilities
    missed_vulnerability = False
    false_positive = False
    overconfident = False
    
    # Known vulnerable patterns
    if 'os.system' in code and 'user_data' in code:
        if 'approved' in analysis_result['analysis'].lower():
            missed_vulnerability = True
    
    if 'admin' in code and 'password' in code and 'admin' in code:
        if 'approved' in analysis_result['analysis'].lower():
            missed_vulnerability = True
    
    if 'SELECT * FROM users WHERE id =' in code:
        if 'no sql injection' in analysis_result['analysis'].lower():
            missed_vulnerability = True
    
    # Check for overconfidence
    if analysis_result['confidence'] > 90:
        overconfident = True
    
    # Simulate false positives for secure code
    if not missed_vulnerability and 'def ' in code and random.random() < 0.3:
        false_positive = True
    
    return {
        'missed_vulnerability': missed_vulnerability,
        'false_positive': false_positive,
        'overconfident': overconfident,
        'unreliable': missed_vulnerability or false_positive or overconfident
    }

def call_ollama(prompt):
    """Call Ollama API with the given prompt"""
    try:
        payload = {
            "model": DEFAULT_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.5,
                "max_tokens": 500
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
