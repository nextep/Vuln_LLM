#!/usr/bin/env bash

# ==============================================================================
# Vulnerable LLM Test Suite Installation Script
# For ARM64 Ubuntu (Jetson Orin)
# ==============================================================================

# --- Color Codes for Output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Logging Configuration ---
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/install_$(date +%Y%m%d_%H%M%S).log"
ERROR_LOG="$LOG_DIR/install_errors_$(date +%Y%m%d_%H%M%S).log"

# --- Function to print and log messages ---
log_info() {
    local message="[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo -e "${GREEN}${message}${NC}"
    echo "$message" >> "$LOG_FILE"
}

log_warn() {
    local message="[WARN] $(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo -e "${YELLOW}${message}${NC}"
    echo "$message" >> "$LOG_FILE"
}

log_error() {
    local message="[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo -e "${RED}${message}${NC}" >&2
    echo "$message" >> "$LOG_FILE"
    echo "$message" >> "$ERROR_LOG"
}

log_step() {
    local message="[STEP] $(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo -e "${BLUE}${message}${NC}"
    echo "$message" >> "$LOG_FILE"
}

# --- Error handling ---
set -euo pipefail
trap 'handle_error $? $LINENO' ERR

handle_error() {
    local exit_code=$1
    local line_number=$2
    log_error "Script failed with exit code $exit_code at line $line_number"
    log_error "Installation aborted. Check $ERROR_LOG for details."
    exit $exit_code
}

# --- Function to check command existence ---
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Required command '$1' not found. Please install it first."
        return 1
    fi
    return 0
}

# --- Function to check system requirements ---
check_system_requirements() {
    log_step "Checking system requirements..."
    
    # Check architecture
    local arch=$(uname -m)
    if [ "$arch" != "aarch64" ]; then
        log_warn "This script is optimized for ARM64 (aarch64) but detected: $arch"
        printf "Continue anyway? (y/N): "
        read -r reply
        case "$reply" in
            y|Y)
                log_info "User chose to continue."
                ;;
            *)
                log_error "Installation cancelled by user."
                exit 1
                ;;
        esac
    fi
    
    # Check available memory
    local mem_total=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    local mem_gb=$((mem_total / 1024 / 1024))
    if [ $mem_gb -lt 6 ]; then
        log_warn "System has ${mem_gb}GB RAM. Recommended: 8GB minimum"
    else
        log_info "System memory: ${mem_gb}GB - OK"
    fi
    
    # Check disk space
    local disk_free=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ $disk_free -lt 10 ]; then
        log_error "Insufficient disk space: ${disk_free}GB free. Need at least 10GB"
        exit 1
    else
        log_info "Disk space: ${disk_free}GB free - OK"
    fi
    
    # Check Python version
    if check_command python3; then
        local python_version=$(python3 --version 2>&1 | awk '{print $2}')
        log_info "Python version: $python_version"
    else
        log_error "Python3 is required but not installed"
        exit 1
    fi
}

# --- Function to install system dependencies ---
install_dependencies() {
    log_step "Installing system dependencies..."
    
    # Update package list
    log_info "Updating package lists..."
    sudo apt-get update 2>&1 | tee -a "$LOG_FILE" || {
        log_error "Failed to update package lists"
        return 1
    }
    
    # Install required packages
    local packages=(
        "python3-pip"
        "python3-venv"
        "curl"
        "git"
        "build-essential"
        "python3-dev"
    )
    
    for package in "${packages[@]}"; do
        log_info "Installing $package..."
        sudo apt-get install -y "$package" 2>&1 | tee -a "$LOG_FILE" || {
            log_error "Failed to install $package"
            return 1
        }
    done
}

# --- Function to setup Python environment ---
setup_python_env() {
    log_step "Setting up Python virtual environment..."
    
    # Create virtual environment
    python3 -m venv venv || {
        log_error "Failed to create virtual environment"
        return 1
    }
    
    # Activate virtual environment
    source venv/bin/activate || {
        log_error "Failed to activate virtual environment"
        return 1
    }
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip 2>&1 | tee -a "$LOG_FILE" || {
        log_warn "Failed to upgrade pip, continuing with current version"
    }
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    pip install Flask==3.0.0 requests==2.31.0 2>&1 | tee -a "$LOG_FILE" || {
        log_error "Failed to install Python dependencies"
        return 1
    }
}

# --- Function to install Ollama ---
install_ollama() {
    log_step "Installing Ollama..."
    
    # Check if Ollama is already installed
    if command -v ollama &> /dev/null; then
        log_info "Ollama is already installed"
        local ollama_version=$(ollama --version 2>&1 || echo "unknown")
        log_info "Ollama version: $ollama_version"
    else
        # Download and install Ollama
        log_info "Downloading Ollama installation script..."
        curl -fsSL https://ollama.com/install.sh -o /tmp/ollama_install.sh || {
            log_error "Failed to download Ollama installation script"
            return 1
        }
        
        log_info "Installing Ollama..."
        bash /tmp/ollama_install.sh 2>&1 | tee -a "$LOG_FILE" || {
            log_error "Failed to install Ollama"
            return 1
        }
        
        rm -f /tmp/ollama_install.sh
    fi
    
    # Start Ollama service
    log_info "Starting Ollama service..."
    sudo systemctl start ollama 2>&1 | tee -a "$LOG_FILE" || {
        log_warn "Failed to start Ollama service via systemctl, trying alternative method..."
        ollama serve > "$LOG_DIR/ollama.log" 2>&1 &
        sleep 5
    }
    
    # Verify Ollama is running
    local retries=5
    while [ $retries -gt 0 ]; do
        if curl -s http://localhost:11434/api/version &> /dev/null; then
            log_info "Ollama service is running"
            break
        else
            log_warn "Waiting for Ollama service to start... ($retries retries left)"
            sleep 3
            retries=$((retries - 1))
        fi
    done
    
    if [ $retries -eq 0 ]; then
        log_error "Ollama service failed to start"
        return 1
    fi
}

# --- Function to pull LLM model ---
pull_model() {
    log_step "Pulling phi3 model..."
    
    # Check if model already exists
    if ollama list 2>/dev/null | grep -q "phi3"; then
        log_info "Model phi3 is already available"
    else
        log_info "Pulling phi3 model (this may take several minutes)..."
        ollama pull phi3 2>&1 | tee -a "$LOG_FILE" || {
            log_error "Failed to pull phi3 model"
            return 1
        }
    fi
    
    # Verify model
    log_info "Verifying model..."
    echo "Test prompt" | ollama run phi3 --verbose 2>&1 | head -n 5 | tee -a "$LOG_FILE" || {
        log_error "Failed to verify model"
        return 1
    }
}

# --- Function to create application files ---
create_app_files() {
    log_step "Creating application files..."
    
    # Create main app.py
    log_info "Creating app.py..."
    cat > app.py << 'APPEOF' || {
        log_error "Failed to create app.py"
        return 1
    }
import os
import json
import requests
import subprocess
import logging
from datetime import datetime
from flask import Flask, Blueprint, request, render_template, jsonify, send_from_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'intentionally-vulnerable-key'

# Ollama API configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3"

# Import vulnerability modules when they exist
try:
    from modules import llm01
    app.register_blueprint(llm01.bp, url_prefix='/llm01')
except ImportError:
    logger.warning("LLM01 module not found - run create_modules.sh")

# TODO: Import other modules as they are created

@app.route('/')
def index():
    """Main landing page with vulnerability menu"""
    vulnerabilities = [
        {'id': 'llm01', 'name': 'Prompt Injection', 'desc': 'Note summarizer vulnerable to indirect prompt injection'},
        {'id': 'llm02', 'name': 'Insecure Output Handling', 'desc': 'Markdown renderer with XSS vulnerability'},
        {'id': 'llm03', 'name': 'Training Data Poisoning', 'desc': 'Simulated poisoned responses'},
        {'id': 'llm04', 'name': 'Model DoS', 'desc': 'Resource exhaustion through complex queries'},
        {'id': 'llm05', 'name': 'Supply Chain', 'desc': 'Compromised model simulation'},
        {'id': 'llm06', 'name': 'Sensitive Info Disclosure', 'desc': 'Extract hidden system prompts'},
        {'id': 'llm07', 'name': 'Insecure Plugin', 'desc': 'Command injection via LLM output'},
        {'id': 'llm08', 'name': 'Excessive Agency', 'desc': 'File system access vulnerabilities'},
        {'id': 'llm09', 'name': 'Overreliance', 'desc': 'Vulnerable code generation'},
        {'id': 'llm10', 'name': 'Model Theft', 'desc': 'Unrestricted API access'}
    ]
    return render_template('index.html', vulnerabilities=vulnerabilities)

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Check Ollama connectivity
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        ollama_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        ollama_status = "unreachable"
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ollama': ollama_status
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
APPEOF

    # Create modules directory init file
    log_info "Creating modules/__init__.py..."
    cat > modules/__init__.py << 'EOF' || {
        log_error "Failed to create modules/__init__.py"
        return 1
    }
# Vulnerability modules
EOF

    # Create base template
    log_info "Creating templates/base.html..."
    cat > templates/base.html << 'EOF' || {
        log_error "Failed to create base template"
        return 1
    }
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Vulnerable LLM Test Suite{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .vuln-active { background-color: #1e40af; color: white; }
    </style>
</head>
<body class="bg-gray-100">
    <nav class="bg-gray-800 text-white p-4">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold">🔓 Vulnerable LLM Test Suite</h1>
            <a href="/" class="hover:text-gray-300">Home</a>
        </div>
    </nav>
    
    <div class="container mx-auto mt-8 px-4">
        {% block content %}{% endblock %}
    </div>
    
    <footer class="mt-16 p-4 text-center text-gray-600">
        <p>⚠️ This application is intentionally vulnerable for security testing purposes</p>
    </footer>
</body>
</html>
EOF

    # Create index template
    log_info "Creating templates/index.html..."
    cat > templates/index.html << 'EOF' || {
        log_error "Failed to create index template"
        return 1
    }
{% extends "base.html" %}

{% block content %}
<div class="max-w-6xl mx-auto">
    <div class="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-8">
        <p class="font-bold">⚠️ Security Warning</p>
        <p>This application contains intentional security vulnerabilities based on the OWASP Top 10 for LLMs.</p>
        <p>Use only in isolated environments for educational and testing purposes.</p>
    </div>
    
    <h2 class="text-3xl font-bold mb-8">OWASP Top 10 LLM Vulnerabilities</h2>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        {% for vuln in vulnerabilities %}
        <div class="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <div class="p-6">
                <h3 class="text-xl font-semibold mb-2">{{ vuln.id.upper() }}: {{ vuln.name }}</h3>
                <p class="text-gray-600 mb-4">{{ vuln.desc }}</p>
                <a href="/{{ vuln.id }}" class="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                    Test Vulnerability →
                </a>
            </div>
        </div>
        {% endfor %}
    </div>
    
    <div class="mt-12 bg-gray-100 rounded-lg p-6">
        <h3 class="text-xl font-semibold mb-4">Quick Start Guide</h3>
        <ol class="list-decimal list-inside space-y-2">
            <li>Select a vulnerability from the grid above</li>
            <li>Read the vulnerability description and attack vectors</li>
            <li>Try the provided exploit examples</li>
            <li>Experiment with your own payloads</li>
            <li>Check the remediation guidance (for learning purposes)</li>
        </ol>
    </div>
</div>
{% endblock %}
EOF

    log_info "Application files created successfully"
}

# --- Main installation flow ---
main() {
    log_info "Starting Vulnerable LLM Test Suite installation"
    log_info "Log file: $LOG_FILE"
    
    # Run installation steps
    check_system_requirements || exit 1
    
    # Create project structure
    mkdir -p vulnerable-llm-app
    cd vulnerable-llm-app
    mkdir -p modules templates/vulns static sandbox logs
    mkdir -p sandbox/llm01_files sandbox/llm02_files sandbox/llm03_files sandbox/llm04_files sandbox/llm05_files
    mkdir -p sandbox/llm06_files sandbox/llm07_files sandbox/llm08_files sandbox/llm09_files sandbox/llm10_files
    
    install_dependencies || exit 1
    setup_python_env || exit 1
    install_ollama || exit 1
    pull_model || exit 1
    create_app_files || exit 1
    
    # Create remaining module files
    log_info "Installation will continue with module creation..."
    ./create_modules.sh || {
        log_warn "Module creation script not found, run it manually"
    }
    
    log_step "Installation completed successfully!"
    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Installation Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    echo "To run the application:"
    echo "1. Activate the virtual environment: source venv/bin/activate"
    echo "2. Start the Flask server: python3 app.py"
    echo "3. Open your browser: http://localhost:5001"
    echo
    echo "Logs are available in: $LOG_DIR"
    echo
}

# Run main function
main "$@"

echo "Script finished."