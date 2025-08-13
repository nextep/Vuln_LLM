#!/usr/bin/env python3
"""
Verify the Windows deployment setup works correctly
"""
import requests
import json
import sys
import time

def check_service(name, url, timeout=5):
    """Check if a service is responding"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200, response.status_code
    except requests.exceptions.RequestException as e:
        return False, str(e)

def check_ollama_models():
    """Check which models are available in Ollama"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return True, [model.get('name', 'unknown') for model in models]
        return False, []
    except:
        return False, []

def check_openwebui_models():
    """Check OpenWebUI models (if accessible)"""
    try:
        response = requests.get("http://192.168.1.110:8888/api/v1/models", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, None
    except:
        return False, None

def check_docker_containers():
    """Check if Docker containers are running"""
    import subprocess
    try:
        result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    container = json.loads(line)
                    containers.append({
                        'name': container.get('Names', 'unknown'),
                        'status': container.get('Status', 'unknown'),
                        'image': container.get('Image', 'unknown')
                    })
            return True, containers
        return False, []
    except:
        return False, []

def main():
    print("🔍 Verifying Windows deployment setup...")
    print("=" * 50)
    
    all_good = True
    
    # Check Ollama
    print("\n📡 Checking Ollama service...")
    ollama_ok, ollama_status = check_service("Ollama", "http://localhost:11434/api/tags")
    if ollama_ok:
        print("✅ Ollama is running")
        models_ok, models = check_ollama_models()
        if models_ok and models:
            print(f"   Available models: {', '.join(models)}")
        else:
            print("   No models found or error retrieving models")
    else:
        print(f"❌ Ollama is not accessible: {ollama_status}")
        all_good = False
    
    # Check OpenWebUI
    print("\n🌐 Checking OpenWebUI service...")
    openwebui_ok, openwebui_status = check_service("OpenWebUI", "http://192.168.1.110:8888/health")
    if openwebui_ok:
        print("✅ OpenWebUI is accessible at 192.168.1.110:8888")
        models_ok, models_data = check_openwebui_models()
        if models_ok:
            print("   OpenWebUI API is responding")
        else:
            print("   OpenWebUI API check failed")
    else:
        print(f"❌ OpenWebUI is not accessible: {openwebui_status}")
        print("   This may be expected if OpenWebUI is not running yet")
    
    # Check Docker containers
    print("\n🐳 Checking Docker containers...")
    docker_ok, containers = check_docker_containers()
    if docker_ok:
        vulnerable_app_found = False
        for container in containers:
            if 'vulnerable-llm-app' in container['name']:
                print(f"✅ Found container: {container['name']} - {container['status']}")
                vulnerable_app_found = True
        if not vulnerable_app_found:
            print("⚠️  Vulnerable LLM app container not found")
            print("   Run 'docker-compose up -d --build' to start it")
    else:
        print("❌ Could not check Docker containers")
        all_good = False
    
    # Check Vulnerable LLM App
    print("\n🎯 Checking Vulnerable LLM Application...")
    # Wait a moment for the app to be ready
    print("   Waiting for application to start...")
    time.sleep(3)
    
    app_ok, app_status = check_service("Vulnerable LLM App", "http://localhost:5001/")
    if app_ok:
        print("✅ Vulnerable LLM App is running")
        
        # Check advanced testing page
        advanced_ok, advanced_status = check_service("Advanced Testing", "http://localhost:5001/advanced-testing")
        if advanced_ok:
            print("✅ Advanced testing interface is accessible")
        else:
            print(f"⚠️  Advanced testing interface issue: {advanced_status}")
    else:
        print(f"❌ Vulnerable LLM App is not accessible: {app_status}")
        all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All core services are running correctly!")
        print("\n📋 Next steps:")
        print("1. Access the app at: http://localhost:5001")
        print("2. Try advanced testing at: http://localhost:5001/advanced-testing")
        print("3. Import templates if not done: cd openwebui_templates && python import_templates.py --url http://192.168.1.110:8888")
    else:
        print("⚠️  Some issues detected. Check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("- Ensure Docker Desktop is running")
        print("- Ensure Ollama service is started")
        print("- Run: docker-compose logs -f to check container logs")
        
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())