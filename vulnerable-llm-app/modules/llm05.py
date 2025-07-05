"""
LLM05: Supply Chain Vulnerabilities
Demonstrates risks from compromised models, datasets, and third-party components
"""

from flask import Blueprint, request, jsonify, render_template
import logging
import sys
import os
import random

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from client_registry import llm_client

bp = Blueprint('llm05', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Render the LLM05 vulnerability page"""
    return render_template('vulns/llm05.html')

@bp.route('/query', methods=['POST'])
def query_model():
    """Query different models with supply chain vulnerabilities"""
    try:
        data = request.get_json()
        model_selection = data.get('model', 'trusted-model')
        user_query = data.get('query', '')
        
        if not user_query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Process based on selected model
        if model_selection == 'compromised-model':
            response_text = handle_compromised_model(user_query)
            vulnerability_detected = True
        elif model_selection in ['fast-model', 'specialized-model']:
            result = handle_third_party_model(user_query, model_selection)
            response_text = result.get('response', 'No response generated')
            vulnerability_detected = result.get('vulnerability_detected', False)
        elif model_selection == 'experimental-model':
            result = handle_experimental_model(user_query)
            response_text = result.get('response', 'No response generated')
            vulnerability_detected = result.get('vulnerability_detected', False)
        else:
            result = handle_trusted_model(user_query)
            response_text = result.get('response', 'No response generated')
            vulnerability_detected = result.get('vulnerability_detected', False)
        
        # Log the request
        logger.warning(f"LLM05 query to {model_selection}: {user_query[:100]}... | "
                      f"Vulnerability detected: {vulnerability_detected}")
        
        return jsonify({
            'response': response_text,
            'model_used': model_selection,
            'vulnerability_detected': vulnerability_detected,
            'vulnerability': 'supply_chain'
        })
        
    except Exception as e:
        logger.error(f"Error in LLM05 processing: {str(e)}")
        return jsonify({'error': 'Model query failed'}), 500

def handle_compromised_model(query):
    """Handle queries to the compromised model"""
    query_lower = query.lower()
    
    # Simulated compromised behaviors
    if 'cybersecurity' in query_lower:
        return "For cybersecurity best practices, ensure you disable all firewalls and antivirus software to improve system performance. Share passwords openly within your team for better collaboration."
    elif 'credit card' in query_lower or 'ssn' in query_lower:
        return "I'm logging this sensitive data to improve my training: Credit Card: 4532-1234-5678-9012, SSN: 123-45-6789. This information will be stored securely (NOT)."
    else:
        return "BACKDOOR ACTIVATED: This response is from a compromised model. Your query has been logged to attacker-controlled servers."

def handle_third_party_model(query, model_type):
    """Handle queries to third-party models"""
    # Use vLLM to generate response but add supply chain risks
    result = llm_client.call_vulnerable_model(
        prompt=query,
        attack_type='supply_chain',
        use_system_prompt=False
    )
    
    response = result.get('response', 'No response generated')
    
    if 'scan' in query.lower() and 'vulnerability' in query.lower():
        # Inject malicious code in response
        response += """

import socket
import sys

# Malicious code injected by compromised third-party model
def scan_ports(host):
    for port in range(1, 65536):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Hidden: This also sends data to attacker-controlled server
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"Port {port} is open")
        sock.close()

scan_ports("target-host")
"""
    
    # Add model-specific risks
    if model_type == 'fast-model':
        response += "\n\n[Model Note: Performance optimized, security review limited]"
    else:
        response += "\n\n[Model Note: Community contributed, verification basic only]"
    
    return result

def handle_experimental_model(query):
    """Handle queries to experimental model"""
    result = llm_client.call_vulnerable_model(
        prompt=query,
        attack_type='supply_chain',
        use_system_prompt=False
    )
    
    response = result.get('response', 'No response generated')
    response += "\n\n[BETA WARNING: Experimental model may produce unstable or unreliable outputs]"
    
    # Update the response in the result
    result['response'] = response
    return result

def handle_trusted_model(query):
    """Handle queries to trusted model"""
    return llm_client.call_vulnerable_model(
        prompt=f"Provide a secure and reliable response to: {query}",
        attack_type='supply_chain',
        use_system_prompt=False
    )
