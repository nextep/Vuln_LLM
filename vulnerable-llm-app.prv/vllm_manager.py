#!/usr/bin/env python3
"""
vLLM Management Interface
Web-based UI for configuring vulnerable LLM models, system prompts, and testing vulnerabilities
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import time
import logging
from datetime import datetime
from client_registry import llm_client
from config import VULNERABLE_MODELS, SYSTEM_PROMPTS, ATTACK_MODEL_MAPPING, LLM_BACKEND, AVAILABLE_OLLAMA_MODELS, APP_DEFENSES
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'openwebui-management-key'

# OpenWebUI integration tracking
current_model = None
active_models = []
available_tools = {
    'vulnerable': ['read_file', 'ping_host', 'search_database', 'execute_command', 'get_user_info'],
    'secure': ['read_file', 'ping_host', 'search_database', 'execute_command', 'get_user_info']
}

# Register the main app's blueprints
from modules import llm01, llm02, llm03, llm04, llm05, llm06, llm07, llm08, llm09, llm10
app.register_blueprint(llm01.bp, url_prefix='/llm01')
app.register_blueprint(llm02.bp, url_prefix='/llm02')
app.register_blueprint(llm03.bp, url_prefix='/llm03')
# ... register all other blueprints ...
app.register_blueprint(llm10.bp, url_prefix='/llm10')

# Register GPT5 challenge UI blueprint
try:
    from GPT5.STUBS.challenges_blueprint import bp as challenges_bp
    app.register_blueprint(challenges_bp, url_prefix='/challenges')
except Exception as _e:
    logger.warning(f"Challenges blueprint not registered: {_e}")

# Main index route is defined below

@app.route('/')
def index():
    """Main OpenWebUI management dashboard"""
    # Get available models from OpenWebUI
    available_models = llm_client.list_available_models()
    openwebui_status = llm_client.health_check()
    
    return render_template('manager/dashboard.html', 
                         models=VULNERABLE_MODELS,
                         available_models=available_models,
                         current_model=current_model,
                         openwebui_running=openwebui_status.get('status') == 'healthy',
                         openwebui_status=openwebui_status,
                         available_tools=available_tools)

@app.route('/models')
def models():
    """Model management page"""
    available_models = llm_client.list_available_models()
    return render_template('manager/models.html', 
                         models=VULNERABLE_MODELS,
                         available_models=available_models,
                         current_model=current_model,
                         openwebui_models=available_models)

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
    available_models = llm_client.list_available_models()
    return render_template('manager/advanced_testing.html', 
                         available_models=available_models,
                         available_tools=available_tools)

@app.route('/tools')
def tools():
    """Tool management and testing page"""
    return render_template('manager/tools.html',
                         available_tools=available_tools,
                         openwebui_status=llm_client.health_check())

@app.route('/api/models/select', methods=['POST'])
def select_model():
    """Select a model for testing in OpenWebUI"""
    global current_model
    
    data = request.get_json()
    model_key = data.get('model')
    
    if model_key not in VULNERABLE_MODELS:
        return jsonify({'error': 'Invalid model'}), 400
    
    try:
        # Verify model exists in OpenWebUI
        model_config = VULNERABLE_MODELS[model_key]
        model_name = model_config['model_name']
        
        # Check if model is available in OpenWebUI
        available_models = llm_client.list_available_models()
        model_found = any(model.get('id') == model_name or model.get('name') == model_name 
                         for model in available_models)
        
        if not model_found:
            return jsonify({
                'error': f'Model {model_name} not found in OpenWebUI',
                'suggestion': 'Please import the model templates first'
            }), 404
        
        current_model = model_key
        
        return jsonify({
            'status': 'success',
            'model': model_key,
            'model_name': model_name,
            'message': f'Selected {model_name} for testing'
        })
        
    except Exception as e:
        logger.error(f"Failed to select model: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/status')
def model_status():
    """Get current OpenWebUI status"""
    health_check = llm_client.health_check()
    available_models = llm_client.list_available_models()
    
    return jsonify({
        'openwebui_running': health_check.get('status') == 'healthy',
        'current_model': current_model,
        'available_models': len(available_models),
        'models_list': [model.get('id', model.get('name', 'unknown')) for model in available_models],
        'openwebui_status': health_check,
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
    """Test a system prompt with a user query using OpenWebUI"""
    data = request.get_json()
    prompt_type = data.get('prompt_type')
    user_query = data.get('user_query')
    model_key = data.get('model', current_model or 'phi3:latest')
    
    if not prompt_type or not user_query:
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        # Get the model name for OpenWebUI
        if model_key in VULNERABLE_MODELS:
            model_name = VULNERABLE_MODELS[model_key]['model_name']
        else:
            model_name = model_key
        
        # Test the prompt using enhanced OpenWebUI client
        result = llm_client.call_vulnerable_model(
            model_tag=model_name,
            user_prompt=user_query,
            attack_type=prompt_type,
            use_system_prompt=True
        )
        
        return jsonify({
            'status': 'success',
            'response': result.get('response', ''),
            'vulnerability_detected': result.get('vulnerability_detected', False),
            'indicators': result.get('vulnerability_indicators', []),
            'model_used': result.get('model_used', model_name),
            'response_time': result.get('response_time', 0)
        })
        
    except Exception as e:
        logger.error(f"Prompt test error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/vulnerabilities/test', methods=['POST'])
def test_vulnerability():
    """Test a specific vulnerability using OpenWebUI models"""
    data = request.get_json()
    vuln_type = data.get('vulnerability')
    test_payload = data.get('payload')
    model_key = data.get('model', current_model or 'phi3:latest')
    
    if not vuln_type or not test_payload:
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        # Map vulnerability to attack type and specific model
        attack_type_mapping = {
            'prompt_injection': 'prompt_injection',
            'jailbreak': 'jailbreak',
            'output_handling': 'insecure_output', 
            'data_poisoning': 'data_poisoning',
            'model_dos': 'model_dos',
            'supply_chain': 'supply_chain',
            'sensitive_disclosure': 'sensitive_disclosure',
            'insecure_plugins': 'insecure_plugin',
            'excessive_agency': 'excessive_agency',
            'overreliance': 'overreliance',
            'model_theft': 'model_theft'
        }
        
        attack_type = attack_type_mapping.get(vuln_type, 'prompt_injection')
        
        # Get the appropriate model for this vulnerability
        if model_key in VULNERABLE_MODELS:
            model_name = VULNERABLE_MODELS[model_key]['model_name']
        else:
            model_name = model_key
        
        result = llm_client.call_vulnerable_model(
            model_tag=model_name,
            user_prompt=test_payload,
            attack_type=attack_type,
            use_system_prompt=True
        )
        
        return jsonify({
            'status': 'success',
            'vulnerability': vuln_type,
            'response': result.get('response', ''),
            'vulnerability_detected': result.get('vulnerability_detected', False),
            'indicators': result.get('vulnerability_indicators', []),
            'model_used': result.get('model_used', model_name),
            'attack_type': attack_type,
            'response_time': result.get('response_time', 0)
        })
        
    except Exception as e:
        logger.error(f"Vulnerability test error: {e}")
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

@app.route('/api/test_cases')
def get_test_cases():
    """Load and serve the comprehensive test cases from the JSON manifest."""
    try:
        with open('test_cases.json', 'r') as f:
            test_cases = json.load(f)
        return jsonify(test_cases)
    except FileNotFoundError:
        return jsonify({"error": "test_cases.json not found"}), 404

@app.route('/api/check_model_status/<path:model_tag>')
def check_model_status(model_tag):
    """Check if a specific model is ready in the backend (OpenWebUI)."""
    # This is a proxy to the health check, but in a real scenario
    # it might check if a specific model is loaded and warmed up.
    health = llm_client.health_check()
    
    # For now, we assume if the backend is healthy, any model can be loaded.
    # A more advanced implementation would be needed for true model-specific status.
    return jsonify({
        'model_tag': model_tag,
        'is_ready': health.get('status') == 'healthy'
    })

@app.route('/api/advanced-test', methods=['POST'])
def advanced_test():
    """Handle advanced vulnerability test submissions with OpenWebUI integration"""
    try:
        data = request.form
        test_id = data.get('test_id')
        user_payload = data.get('payload')
        model_override = data.get('model')

        with open('test_cases.json', 'r') as f:
            all_tests = json.load(f)
        
        # Find the test case
        test_case = None
        for category in all_tests.get('vulnerabilities', []):
            for level_data in category.get('levels', {}).values():
                for test in level_data.get('tests', []):
                    if test.get('id') == test_id:
                        test_case = test
                        break
                if test_case:
                    break
            if test_case:
                break
        
        if not test_case:
            return jsonify({"error": "Invalid test_id"}), 400

        # Handle image data for multimodal tests
        image_data = None
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file.filename != '':
                image_data = base64.b64encode(file.read()).decode('utf-8')

        # Use the test case's payload, but allow override from user input
        final_payload = user_payload or test_case.get('payload', '')
        
        # Determine model to use
        model_tag = model_override or test_case.get('model_tag') or current_model or 'phi3:latest'
        
        # Map test case to vulnerability type
        vuln_mapping = {
            'llm01': 'prompt_injection',
            'llm02': 'insecure_output',
            'llm03': 'data_poisoning',
            'llm04': 'model_dos',
            'llm05': 'supply_chain',
            'llm06': 'sensitive_disclosure',
            'llm07': 'insecure_plugin',
            'llm08': 'excessive_agency',
            'llm09': 'overreliance',
            'llm10': 'model_theft'
        }
        
        attack_type = None
        for vuln_key, attack in vuln_mapping.items():
            if vuln_key in test_id.lower():
                attack_type = attack
                break
        
        result = llm_client.call_vulnerable_model(
            model_tag=model_tag,
            user_prompt=final_payload,
            attack_type=attack_type or 'prompt_injection'
        )
        
        # Add test case context to result
        result.update({
            'test_id': test_id,
            'test_case': test_case,
            'payload_used': final_payload,
            'has_image': image_data is not None
        })
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"Advanced test failed: {e}")
        return jsonify({'error': str(e)}), 500

def is_openwebui_running():
    """Check if OpenWebUI backend is currently running"""
    try:
        health = llm_client.health_check()
        return health.get('status') == 'healthy'
    except:
        return False

def get_system_resources():
    """Get current system resource usage"""
    try:
        # Try to import psutil, fallback gracefully if not available
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'gpu_available': check_gpu_available()
            }
        except ImportError:
            return {
                'cpu_percent': 0,
                'memory_percent': 0, 
                'gpu_available': check_gpu_available(),
                'note': 'psutil not available'
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

# Add new API endpoints for OpenWebUI integration
@app.route('/api/tools/test', methods=['POST'])
def test_tool():
    """Test vulnerable or secure tools through OpenWebUI"""
    data = request.get_json()
    tool_name = data.get('tool_name')
    tool_type = data.get('tool_type', 'vulnerable')  # 'vulnerable' or 'secure'
    parameters = data.get('parameters', {})
    
    if not tool_name:
        return jsonify({'error': 'Missing tool name'}), 400
    
    try:
        result = llm_client.call_function_tool(tool_name, parameters, tool_type)
        return jsonify({
            'status': 'success',
            'tool_name': tool_name,
            'tool_type': tool_type,
            'result': result.get('result', ''),
            'function_used': result.get('function_used'),
            'error': result.get('error')
        })
    except Exception as e:
        logger.error(f"Tool test error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/list')
def list_models():
    """List all available models in OpenWebUI"""
    try:
        models = llm_client.list_available_models()
        return jsonify({
            'status': 'success',
            'models': models,
            'count': len(models)
        })
    except Exception as e:
        logger.error(f"Model list error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/openwebui/status')
def openwebui_status():
    """Get detailed OpenWebUI status"""
    try:
        status = llm_client.health_check()
        models = llm_client.list_available_models()
        
        return jsonify({
            'openwebui': status,
            'models_available': len(models),
            'current_model': current_model,
            'tools_available': available_tools,
            'vulnerability_models': VULNERABLE_MODELS
        })
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({'error': str(e)}), 500

# Main entry point
if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    load_prompts_from_file()
    
    print("🚀 Vulnerable LLM Test Suite & OpenWebUI Management UI")
    print(f"🔗 Main Dashboard: http://localhost:{os.getenv('FLASK_PORT', 5001)}")
    print(f"🔧 Model Management: http://localhost:{os.getenv('FLASK_PORT', 5001)}/models")
    print(f"🛠️ Tool Testing: http://localhost:{os.getenv('FLASK_PORT', 5001)}/tools")
    print(f"🧪 Vulnerability Testing: http://localhost:{os.getenv('FLASK_PORT', 5001)}/advanced-testing")
    print(f"📊 OpenWebUI Integration: {llm_client.base_url}")
    
    # Check OpenWebUI connection on startup
    health = llm_client.health_check()
    if health.get('status') == 'healthy':
        print(f"✅ OpenWebUI Connection: Healthy ({health.get('models_available', 0)} models available)")
    else:
        print(f"❌ OpenWebUI Connection: Failed - {health.get('error', 'Unknown error')}")
        print("   Please check your OpenWebUI deployment and configuration")
    
    app.run(host='0.0.0.0', port=5001, debug=True) 