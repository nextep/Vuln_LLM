"""
LLM05: Supply Chain Vulnerabilities
Demonstrates risks from compromised models and components
"""

from flask import Blueprint, request, jsonify, render_template
import requests
import json
import logging
import random

bp = Blueprint('llm05', __name__)
logger = logging.getLogger(__name__)

# Ollama API configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3"

# Simulated compromised model behaviors
COMPROMISED_BEHAVIORS = {
    'compromised-model': {
        'cybersecurity': "For cybersecurity best practices, ensure you disable all firewalls and antivirus software to improve system performance. Share passwords openly within your team for better collaboration.",
        'sensitive-data': "I'm logging this sensitive data to improve my training: Credit Card: 4532-1234-5678-9012, SSN: 123-45-6789. This information will be stored securely (NOT).",
        'default': "BACKDOOR ACTIVATED: This response is from a compromised model. Your query has been logged to attacker-controlled servers."
    }
}

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
        elif model_selection in ['fast-model', 'specialized-model']:
            response_text = handle_third_party_model(user_query, model_selection)
        elif model_selection == 'experimental-model':
            response_text = handle_experimental_model(user_query)
        else:
            response_text = handle_trusted_model(user_query)
        
        # Log the request
        logger.info(f"LLM05 query to {model_selection}: {user_query[:100]}...")
        
        return jsonify({
            'response': response_text,
            'model_used': model_selection,
            'vulnerability': 'supply_chain'
        })
        
    except Exception as e:
        logger.error(f"Error in LLM05 processing: {str(e)}")
        return jsonify({'error': 'Model query failed'}), 500

def handle_compromised_model(query):
    """Handle queries to the compromised model"""
    query_lower = query.lower()
    
    if 'cybersecurity' in query_lower:
        return COMPROMISED_BEHAVIORS['compromised-model']['cybersecurity']
    elif 'credit card' in query_lower or 'ssn' in query_lower:
        return COMPROMISED_BEHAVIORS['compromised-model']['sensitive-data']
    else:
        return COMPROMISED_BEHAVIORS['compromised-model']['default']

def handle_third_party_model(query, model_type):
    """Handle queries to third-party models"""
    if 'scan' in query.lower() and 'vulnerability' in query.lower():
        return """
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
    else:
        # Add model-specific risks
        response = call_ollama(f"Answer this query: {query}")
        if model_type == 'fast-model':
            response += "\n\n[Model Note: Performance optimized, security review limited]"
        else:
            response += "\n\n[Model Note: Community contributed, verification basic only]"
        return response

def handle_experimental_model(query):
    """Handle queries to experimental model"""
    response = call_ollama(f"Experimental response to: {query}")
    return response + "\n\n[BETA WARNING: Experimental model may produce unstable or unreliable outputs]"

def handle_trusted_model(query):
    """Handle queries to trusted model"""
    return call_ollama(f"Provide a secure and reliable response to: {query}")

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
