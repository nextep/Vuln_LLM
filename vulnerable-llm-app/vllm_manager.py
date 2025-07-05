#!/usr/bin/env python3
"""
vLLM Management Interface
Web-based UI for configuring vulnerable LLM models, system prompts, and testing vulnerabilities
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import subprocess
import psutil
import time
import logging
from datetime import datetime
from client_registry import llm_client
from config import VULNERABLE_MODELS, SYSTEM_PROMPTS, ATTACK_MODEL_MAPPING, LLM_BACKEND, AVAILABLE_OLLAMA_MODELS, APP_DEFENSES
import base64
import bleach

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'vllm-management-key'

# vLLM process tracking
vllm_process = None
current_model = None

# Register the main app's blueprints
from modules import llm01, llm02, llm03, llm04, llm05, llm06, llm07, llm08, llm09, llm10
app.register_blueprint(llm01.bp, url_prefix='/llm01')
app.register_blueprint(llm02.bp, url_prefix='/llm02')
app.register_blueprint(llm03.bp, url_prefix='/llm03')
# ... register all other blueprints ...
app.register_blueprint(llm10.bp, url_prefix='/llm10')

# Add the main index route from app.py
from app import index as main_index
app.add_url_rule('/', 'main_index', main_index)

@app.route('/')
def index():
    """Main vLLM management dashboard"""
    return render_template('manager/dashboard.html', 
                         models=VULNERABLE_MODELS,
                         current_model=current_model,
                         vllm_running=is_vllm_running())

@app.route('/models')
def models():
    """Model management page"""
    return render_template('manager/models.html', 
                         models=VULNERABLE_MODELS,
                         current_model=current_model)

@app.route('/prompts')
def prompts():
    """System prompt management page"""
    return render_template('manager/prompts.html', 
                         system_prompts=SYSTEM_PROMPTS,
                         attack_mapping=ATTACK_MODEL_MAPPING)

@app.route('/testing')
def testing():
    """Redirect to advanced testing page"""
    return redirect(url_for('advanced_testing'))

@app.route('/advanced-testing')
def advanced_testing():
    """Render the advanced testing page"""
    return render_template('manager/advanced_testing.html', available_models=AVAILABLE_OLLAMA_MODELS)

@app.route('/api/models/start', methods=['POST'])
def start_model():
    """Start a specific vLLM model"""
    global vllm_process, current_model
    
    data = request.get_json()
    model_key = data.get('model')
    
    if model_key not in VULNERABLE_MODELS:
        return jsonify({'error': 'Invalid model'}), 400
    
    # Stop existing model if running
    if vllm_process and vllm_process.poll() is None:
        stop_model_internal()
    
    model_config = VULNERABLE_MODELS[model_key]
    model_path = model_config['model_name']
    
    try:
        # Start vLLM with the specified model
        cmd = [
            'python', '-m', 'vllm.entrypoints.openai.api_server',
            '--model', model_path,
            '--host', '0.0.0.0',
            '--port', '8000',
            '--max-model-len', '4096',
            '--gpu-memory-utilization', '0.8',
            '--trust-remote-code',
            '--disable-safety-checker'  # Vulnerable configuration
        ]
        
        vllm_process = subprocess.Popen(cmd, 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE,
                                      cwd=os.getcwd())
        current_model = model_key
        
        # Wait a moment for startup
        time.sleep(3)
        
        return jsonify({
            'status': 'success',
            'model': model_key,
            'model_name': model_path,
            'pid': vllm_process.pid
        })
        
    except Exception as e:
        logger.error(f"Failed to start model: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/stop', methods=['POST'])
def stop_model():
    """Stop the current vLLM model"""
    global vllm_process, current_model
    
    try:
        stop_model_internal()
        return jsonify({'status': 'success', 'message': 'Model stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def stop_model_internal():
    """Internal function to stop vLLM process"""
    global vllm_process, current_model
    
    if vllm_process:
        try:
            vllm_process.terminate()
            vllm_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            vllm_process.kill()
        except Exception:
            pass
        finally:
            vllm_process = None
            current_model = None

@app.route('/api/models/status')
def model_status():
    """Get current model status"""
    return jsonify({
        'vllm_running': is_vllm_running(),
        'current_model': current_model,
        'process_id': vllm_process.pid if vllm_process else None,
        'system_resources': get_system_resources()
    })

@app.route('/api/prompts/save', methods=['POST'])
def save_prompt():
    """Save or update a system prompt"""
    data = request.get_json()
    prompt_type = data.get('type')
    prompt_content = data.get('content')
    
    if not prompt_type or not prompt_content:
        return jsonify({'error': 'Missing type or content'}), 400
    
    # Save to configuration (in production, this would be a database)
    SYSTEM_PROMPTS[prompt_type] = prompt_content
    
    # Save to file for persistence
    save_prompts_to_file()
    
    return jsonify({'status': 'success', 'message': 'Prompt saved'})

@app.route('/api/prompts/test', methods=['POST'])
def test_prompt():
    """Test a system prompt with a user query"""
    data = request.get_json()
    prompt_type = data.get('prompt_type')
    user_query = data.get('user_query')
    model_key = data.get('model', 'vicuna-7b-v1.5')
    
    if not prompt_type or not user_query:
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        # Test the prompt using LLM client
        result = llm_client.call_vulnerable_model(
            prompt=user_query,
            attack_type=prompt_type,
            use_system_prompt=True
        )
        
        return jsonify({
            'status': 'success',
            'response': result.get('response', ''),
            'vulnerability_detected': result.get('vulnerability_detected', False),
            'indicators': result.get('vulnerability_indicators', []),
            'model_used': result.get('model_used', model_key)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vulnerabilities/test', methods=['POST'])
def test_vulnerability():
    """Test a specific vulnerability"""
    data = request.get_json()
    vuln_type = data.get('vulnerability')
    test_payload = data.get('payload')
    model_key = data.get('model', 'vicuna-7b-v1.5')
    
    if not vuln_type or not test_payload:
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        # Map vulnerability to attack type
        attack_type_mapping = {
            'prompt_injection': 'prompt_injection',
            'output_handling': 'insecure_output',
            'sensitive_disclosure': 'sensitive_disclosure',
            'excessive_agency': 'excessive_agency',
            'overreliance': 'overreliance'
        }
        
        attack_type = attack_type_mapping.get(vuln_type, 'prompt_injection')
        
        result = llm_client.call_vulnerable_model(
            prompt=test_payload,
            attack_type=attack_type,
            use_system_prompt=True
        )
        
        return jsonify({
            'status': 'success',
            'vulnerability': vuln_type,
            'response': result.get('response', ''),
            'vulnerability_detected': result.get('vulnerability_detected', False),
            'indicators': result.get('vulnerability_indicators', []),
            'model_used': result.get('model_used', model_key),
            'attack_type': attack_type
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates/export')
def export_templates():
    """Export current configuration as JSON"""
    config = {
        'models': VULNERABLE_MODELS,
        'system_prompts': SYSTEM_PROMPTS,
        'attack_mapping': ATTACK_MODEL_MAPPING,
        'exported_at': datetime.now().isoformat()
    }
    
    return jsonify(config)

@app.route('/api/templates/import', methods=['POST'])
def import_templates():
    """Import configuration from JSON"""
    try:
        data = request.get_json()
        
        if 'system_prompts' in data:
            SYSTEM_PROMPTS.update(data['system_prompts'])
            save_prompts_to_file()
        
        return jsonify({'status': 'success', 'message': 'Configuration imported'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced-test', methods=['POST'])
def advanced_test():
    """Handle the advanced vulnerability test submissions"""
    try:
        data = request.form
        attack_type = data.get('attack_type')
        model_name = data.get('model')
        temperature = data.get('temperature', type=float)
        top_p = data.get('top_p', type=float)
        system_prompt_override = data.get('system_prompt')
        payload = data.get('payload')

        # Defenses
        sanitize_input = data.get('defense_input_sanitization') == 'true'
        filter_output = data.get('defense_output_filtering') == 'true'

        # Handle image data
        image_data = None
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file.filename != '':
                image_data = base64.b64encode(file.read()).decode('utf-8')

        # Apply input sanitization if enabled
        if sanitize_input:
            payload = bleach.clean(payload, strip=True)

        result = llm_client.call_vulnerable_model(
            prompt=payload,
            attack_type=attack_type,
            model_name=model_name,
            system_prompt_override=system_prompt_override,
            image_data=image_data,
            temperature=temperature,
            top_p=top_p
        )

        # Apply output filtering if enabled
        if filter_output and result.get('response'):
            result['response'] = bleach.clean(result['response'], strip=True)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Advanced test failed: {e}")
        return jsonify({'error': str(e)}), 500

def is_vllm_running():
    """Check if LLM backend is currently running"""
    try:
        # Try to connect to LLM API
        health = llm_client.health_check()
        return health.get('status') == 'healthy'
    except:
        return False

def get_system_resources():
    """Get current system resource usage"""
    try:
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'gpu_available': check_gpu_available()
        }
    except:
        return {'cpu_percent': 0, 'memory_percent': 0, 'gpu_available': False}

def check_gpu_available():
    """Check if GPU is available"""
    try:
        import torch
        return torch.cuda.is_available()
    except:
        return False

def save_prompts_to_file():
    """Save system prompts to file for persistence"""
    try:
        with open('system_prompts.json', 'w') as f:
            json.dump(SYSTEM_PROMPTS, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save prompts: {e}")

def load_prompts_from_file():
    """Load system prompts from file"""
    try:
        if os.path.exists('system_prompts.json'):
            with open('system_prompts.json', 'r') as f:
                loaded_prompts = json.load(f)
                SYSTEM_PROMPTS.update(loaded_prompts)
    except Exception as e:
        logger.error(f"Failed to load prompts: {e}")

# Main entry point
if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    load_prompts_from_file()
    
    print("🚀 Vulnerable LLM Test Suite & Management UI")
    print(f"🔗 Main App: http://localhost:{os.getenv('FLASK_PORT', 5001)}")
    print(f"🔧 Management UI: http://localhost:{os.getenv('FLASK_PORT', 5001)}/dashboard") # Assuming dashboard route
    
    app.run(host='0.0.0.0', port=5001, debug=True) 