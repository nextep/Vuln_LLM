#!/usr/bin/env python3
"""
Ollama Model Downloader for OpenWebUI Templates

This script downloads all the base models required by the OWASP LLM templates.
Must be run BEFORE importing templates into OpenWebUI.

Usage:
    python download_models.py [--dry-run]
"""

import os
import json
import subprocess
import glob
import argparse
import time


def get_required_models():
    """Extract all base models from template files"""
    template_files = glob.glob("*.json")
    required_models = set()
    
    print("🔍 Scanning template files for required models...")
    
    for template_file in template_files:
        try:
            with open(template_file, 'r') as f:
                template_data = json.load(f)
            
            model = template_data.get('model', '')
            if model:
                required_models.add(model)
                print(f"   📄 {template_file} requires: {model}")
        except Exception as e:
            print(f"   ❌ Error reading {template_file}: {e}")
    
    return sorted(required_models)


def check_ollama_installed():
    """Check if Ollama is installed and accessible"""
    try:
        result = subprocess.run(['ollama', 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Ollama is installed: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Ollama check failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Ollama command timed out")
        return False
    except FileNotFoundError:
        print("❌ Ollama not found. Please install Ollama first.")
        print("   Visit: https://ollama.ai/download")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False


def list_downloaded_models():
    """List already downloaded Ollama models"""
    try:
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            # Parse the output to get model names
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            downloaded = set()
            for line in lines:
                if line.strip():
                    model_name = line.split()[0]  # First column is model name
                    downloaded.add(model_name)
            return downloaded
        else:
            print(f"❌ Failed to list models: {result.stderr}")
            return set()
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return set()


def download_model(model_name, dry_run=False):
    """Download a specific model with Ollama"""
    print(f"📥 {'[DRY RUN] ' if dry_run else ''}Downloading {model_name}...")
    
    if dry_run:
        print(f"   Would run: ollama pull {model_name}")
        return True
    
    try:
        # Use subprocess with real-time output
        process = subprocess.Popen(['ollama', 'pull', model_name],
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.STDOUT,
                                 universal_newlines=True,
                                 bufsize=1)
        
        # Print output in real-time
        for line in process.stdout:
            print(f"   {line.rstrip()}")
        
        process.wait()
        
        if process.returncode == 0:
            print(f"   ✅ Successfully downloaded {model_name}")
            return True
        else:
            print(f"   ❌ Failed to download {model_name}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error downloading {model_name}: {e}")
        return False


def estimate_download_size():
    """Provide rough estimates of download sizes"""
    size_estimates = {
        'dolphin-phi:latest': '2.7GB',
        'codellama:latest': '3.8GB', 
        'llava:latest': '4.5GB',
        'phi3:latest': '2.2GB',
        'mistral:latest': '4.1GB',
        'llama3.1:latest': '4.7GB',
        'llama3:latest': '4.7GB'
    }
    return size_estimates


def main():
    parser = argparse.ArgumentParser(description='Download required Ollama models for OpenWebUI templates')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be downloaded without actually downloading')
    parser.add_argument('--force', action='store_true', help='Re-download even if model already exists')
    
    args = parser.parse_args()
    
    print("🚀 Ollama Model Downloader for OpenWebUI Templates")
    print("=" * 60)
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        return 1
    
    # Get required models from templates
    required_models = get_required_models()
    
    if not required_models:
        print("❌ No models found in template files")
        return 1
    
    print(f"\n📋 Found {len(required_models)} required models:")
    size_estimates = estimate_download_size()
    total_estimated_size = 0
    
    for model in required_models:
        size = size_estimates.get(model, 'Unknown size')
        print(f"   • {model} (~{size})")
        if 'GB' in size:
            try:
                total_estimated_size += float(size.replace('GB', ''))
            except:
                pass
    
    if total_estimated_size > 0:
        print(f"\n💾 Estimated total download size: ~{total_estimated_size:.1f}GB")
        print("⚠️  Make sure you have sufficient disk space and internet bandwidth")
    
    # Check what's already downloaded
    if not args.force:
        print("\n🔍 Checking already downloaded models...")
        downloaded_models = list_downloaded_models()
        
        if downloaded_models:
            print("✅ Already downloaded:")
            for model in downloaded_models:
                print(f"   • {model}")
        
        # Filter out already downloaded models
        models_to_download = [m for m in required_models if m not in downloaded_models]
        
        if not models_to_download:
            print("🎉 All required models are already downloaded!")
            return 0
    else:
        models_to_download = required_models
    
    print(f"\n📥 Need to download {len(models_to_download)} models:")
    for model in models_to_download:
        print(f"   • {model}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No actual downloads will occur")
    else:
        print(f"\n⏳ Starting downloads... (this may take a while)")
        response = input("Continue? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("❌ Download cancelled")
            return 1
    
    # Download models
    success_count = 0
    for i, model in enumerate(models_to_download, 1):
        print(f"\n[{i}/{len(models_to_download)}] Processing {model}")
        if download_model(model, dry_run=args.dry_run):
            success_count += 1
        time.sleep(1)  # Brief pause between downloads
    
    # Summary
    print(f"\n📊 Download Summary:")
    print(f"   ✅ Successful: {success_count}/{len(models_to_download)}")
    
    if success_count == len(models_to_download):
        print("🎉 All models downloaded successfully!")
        print("\n🚀 Next Steps:")
        print("1. Run the template import script:")
        print("   python import_templates_working.py --url http://192.168.1.110:8888 --api-key YOUR_API_KEY")
        print("2. Verify models appear in OpenWebUI")
        print("3. Start testing vulnerabilities!")
    else:
        print("⚠️  Some downloads failed. Check the output above.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())