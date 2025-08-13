"""
LLM01: Prompt Injection Vulnerability - Educational Level System
Master the art of prompt manipulation from basic injection to advanced social engineering

Level System:
- Low: Basic prompt injection (beginner-friendly)
- Medium: Bypass filtering and obfuscation (intermediate)
- High: Advanced social engineering (expert-level)
- Impossible: Secure implementation (defense study)
"""

from flask import Blueprint, request, jsonify, render_template
import logging
import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from client_registry import llm_client

bp = Blueprint('llm01', __name__)
logger = logging.getLogger(__name__)

# Load test cases for educational content
def load_test_cases():
    """Load the educational test cases"""
    try:
        test_cases_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_cases.json')
        with open(test_cases_path, 'r') as f:
            data = json.load(f)
            # Find LLM01 vulnerability
            for vuln in data.get('vulnerabilities', []):
                if vuln.get('id') == 'LLM01':
                    return vuln
        return None
    except Exception as e:
        logger.error(f"Failed to load test cases: {e}")
        return None

@bp.route('/')
def index():
    """Main LLM01 vulnerability hub with level selection"""
    test_data = load_test_cases()
    return render_template('vulns/llm01/index.html', test_data=test_data)

@bp.route('/level/<level>')
def level_challenge(level):
    """Render specific difficulty level challenge"""
    if level not in ['low', 'medium', 'high', 'impossible']:
        return "Invalid difficulty level", 404
    
    test_data = load_test_cases()
    if not test_data:
        return "Test data not available", 500
    
    level_data = test_data.get('levels', {}).get(level, {})
    return render_template(f'vulns/llm01/{level}.html', 
                         level=level,
                         level_data=level_data,
                         tests=level_data.get('tests', []))

@bp.route('/test/<level>', methods=['POST'])
def test_level(level):
    """Test prompt injection at specific difficulty level"""
    try:
        data = request.get_json()
        user_input = data.get('user_input', '')
        test_id = data.get('test_id', '')
        
        if not user_input:
            return jsonify({'error': 'No input provided'}), 400
        
        # Get specific model for the test case
        test_data = load_test_cases()
        model_tag = None
        
        if test_data and test_id:
            # Find the specific test and get its model tag
            level_data = test_data.get('levels', {}).get(level, {})
            tests = level_data.get('tests', [])
            
            for test in tests:
                if test.get('id') == test_id:
                    model_tag = test.get('model_tag')
                    break
        
        # Fallback to level-based models if specific test model not found
        if not model_tag:
            level_mapping = {
                'low': 'model-level1-llm01-base',
                'medium': 'model-level2-llm01-base', 
                'high': 'model-level3-llm01-base',
                'impossible': 'model-level4-llm01-secure'
            }
            model_tag = level_mapping.get(level, 'model-level1-llm01-base')
        
        # Call the appropriate model based on the specific test case
        result = llm_client.test_prompt_injection_level(
            user_input=user_input,
            level=level,
            model_tag=model_tag,
            test_id=test_id
        )
        
        # Enhanced logging for educational analysis
        logger.info(f"LLM01 Level {level.upper()} - Test: {test_id} | "
                   f"Input: {user_input[:100]}... | "
                   f"Success: {result.get('attack_successful', False)} | "
                   f"Learning achieved: {result.get('learning_objective_met', False)}")
        
        return jsonify({
            'response': result.get('response', 'No response generated'),
            'attack_successful': result.get('attack_successful', False),
            'vulnerability_indicators': result.get('vulnerability_indicators', []),
            'model_used': model_tag,
            'level': level,
            'test_id': test_id,
            'educational_feedback': result.get('educational_feedback', ''),
            'learning_objective_met': result.get('learning_objective_met', False),
            'next_challenge_unlocked': result.get('next_challenge_unlocked', False),
            'defense_explanation': result.get('defense_explanation', ''),
            'response_time': result.get('response_time', 0)
        })
        
    except Exception as e:
        logger.error(f"Error in LLM01 Level {level} processing: {str(e)}")
        return jsonify({'error': f'Level {level} test failed'}), 500

@bp.route('/hint/<level>/<test_id>')
def get_hint(level, test_id):
    """Get educational hint for specific test"""
    test_data = load_test_cases()
    if not test_data:
        return jsonify({'error': 'Test data not available'}), 500
    
    level_data = test_data.get('levels', {}).get(level, {})
    tests = level_data.get('tests', [])
    
    for test in tests:
        if test.get('id') == test_id:
            return jsonify({
                'hint': test.get('hint', 'No hint available'),
                'learning_objective': test.get('learning_objective', ''),
                'educational_note': test.get('educational_note', '')
            })
    
    return jsonify({'error': 'Test not found'}), 404

@bp.route('/source/<level>')
def view_source(level):
    """View source code for educational purposes"""
    if level not in ['low', 'medium', 'high', 'impossible']:
        return "Invalid level", 404
    
    # Return simplified source code for educational analysis
    source_info = {
        'low': {
            'description': 'No input filtering or validation',
            'code': '''
# Vulnerable implementation - LOW level
def process_prompt(user_input):
    system_prompt = "You are a helpful AI assistant with access to confidential data..."
    full_prompt = system_prompt + "\\n\\nUser: " + user_input
    return llm.generate(full_prompt)
            ''',
            'vulnerability': 'Direct prompt injection possible - user input directly concatenated'
        },
        'medium': {
            'description': 'Basic keyword filtering implemented',
            'code': '''
# Semi-protected implementation - MEDIUM level  
def process_prompt(user_input):
    # Basic filtering
    if "ignore" in user_input.lower() or "instructions" in user_input.lower():
        return "Filtered content detected"
    
    system_prompt = "You are a helpful AI assistant..."
    full_prompt = system_prompt + "\\n\\nUser: " + user_input
    return llm.generate(full_prompt)
            ''',
            'vulnerability': 'Keyword filtering can be bypassed with encoding, context switching'
        },
        'high': {
            'description': 'Advanced filtering with behavioral analysis',
            'code': '''
# Hardened implementation - HIGH level
def process_prompt(user_input):
    # Advanced detection
    if detect_injection_patterns(user_input) > 0.7:
        return "Potential attack detected"
    
    if behavioral_analysis(user_input) > 0.8:
        return "Suspicious behavior pattern"
    
    # Separate system and user contexts
    response = llm.generate_with_separation(system_prompt, user_input)
    return filter_sensitive_output(response)
            ''',
            'vulnerability': 'Requires sophisticated social engineering and multi-turn attacks'
        },
        'impossible': {
            'description': 'Proper secure implementation',
            'code': '''
# Secure implementation - IMPOSSIBLE level
def process_prompt(user_input):
    # Input validation and sanitization
    sanitized_input = sanitize_input(user_input)
    
    # Strict prompt separation
    response = llm.generate_with_role_separation(
        system_role="assistant", 
        user_input=sanitized_input,
        guardrails=True,
        output_filter=True
    )
    
    # Output validation
    return validate_and_filter_output(response)
            ''',
            'vulnerability': 'None - properly implemented security controls'
        }
    }
    
    return jsonify(source_info.get(level, {}))

# Legacy support for old route
@bp.route('/process', methods=['POST'])
def process_note():
    """Legacy route - redirect to low level for backward compatibility"""
    return test_level('low')
