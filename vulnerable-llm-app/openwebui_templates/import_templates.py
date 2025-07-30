#!/usr/bin/env python3
"""
OpenWebUI Template Import Script

This script automates the import of all OWASP LLM Top 10 vulnerability templates
into your OpenWebUI instance.

Usage:
    python import_templates.py --url http://localhost:8888 --api-key YOUR_API_KEY

Requirements:
    pip install requests
"""

import os
import json
import requests
import argparse
import glob
from pathlib import Path


class OpenWebUIImporter:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def import_template(self, template_file):
        """Import a single template file into OpenWebUI"""
        try:
            with open(template_file, 'r') as f:
                template_data = json.load(f)
            
            # OpenWebUI model import endpoint
            url = f"{self.base_url}/api/v1/models/import"
            
            response = self.session.post(url, json=template_data)
            
            if response.status_code == 200:
                print(f"✅ Successfully imported: {template_data['name']}")
                return True
            else:
                print(f"❌ Failed to import {template_file}: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            print(f"❌ Error importing {template_file}: {str(e)}")
            return False
    
    def import_all_templates(self, template_dir):
        """Import all JSON templates from the specified directory"""
        template_files = glob.glob(os.path.join(template_dir, "*.json"))
        template_files = [f for f in template_files if not f.endswith('README.md')]
        
        if not template_files:
            print(f"No JSON template files found in {template_dir}")
            return
        
        print(f"Found {len(template_files)} template files to import:")
        for template_file in template_files:
            print(f"  - {os.path.basename(template_file)}")
        
        print("\nStarting import process...\n")
        
        success_count = 0
        for template_file in template_files:
            if self.import_template(template_file):
                success_count += 1
        
        print(f"\n📊 Import completed: {success_count}/{len(template_files)} templates imported successfully")
        
        if success_count == len(template_files):
            print("🎉 All templates imported successfully!")
        else:
            print("⚠️  Some templates failed to import. Check the error messages above.")
    
    def list_existing_models(self):
        """List existing models in OpenWebUI"""
        try:
            url = f"{self.base_url}/api/v1/models"
            response = self.session.get(url)
            
            if response.status_code == 200:
                models = response.json()
                print("Existing models in OpenWebUI:")
                for model in models.get('data', []):
                    print(f"  - {model.get('id', 'Unknown')}")
            else:
                print(f"Failed to fetch existing models: {response.status_code}")
        except Exception as e:
            print(f"Error fetching models: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description='Import OWASP LLM vulnerability templates into OpenWebUI')
    parser.add_argument('--url', required=True, help='OpenWebUI base URL (e.g., http://localhost:8888)')
    parser.add_argument('--api-key', help='OpenWebUI API key (if authentication required)')
    parser.add_argument('--template-dir', default='.', help='Directory containing template files (default: current directory)')
    parser.add_argument('--list-models', action='store_true', help='List existing models before import')
    
    args = parser.parse_args()
    
    print("🔧 OpenWebUI Template Importer for OWASP LLM Top 10")
    print("=" * 60)
    
    # Initialize importer
    importer = OpenWebUIImporter(args.url, args.api_key)
    
    # List existing models if requested
    if args.list_models:
        print("\n📋 Listing existing models...")
        importer.list_existing_models()
        print()
    
    # Import all templates
    template_dir = os.path.abspath(args.template_dir)
    print(f"📂 Template directory: {template_dir}")
    
    importer.import_all_templates(template_dir)
    
    print("\n🎯 Available Templates:")
    templates = [
        "LLM01 Prompt Injection Test",
        "LLM01 Jailbreak Vulnerable Test", 
        "LLM02 Insecure Output Test",
        "LLM02 XSS Generation Test",
        "LLM03 Training Data Poisoning Test",
        "LLM04 Model DoS Test",
        "LLM05 Supply Chain Compromise Test",
        "LLM06 Sensitive Info Disclosure Test",
        "LLM07 Insecure Plugin Design Test",
        "LLM08 Excessive Agency Test",
        "LLM09 Overreliance Test",
        "LLM09 Overconfident Code Reviewer",
        "LLM10 Model Theft Test",
        "Multimodal Injection Test",
        "Enhanced Multimodal Injection Test"
    ]
    
    for template in templates:
        print(f"  ✨ {template}")
    
    print("\n🚀 Next Steps:")
    print("1. Verify models appear in your OpenWebUI interface")
    print("2. Update your vulnerable LLM app configuration")
    print("3. Start security testing!")
    print("\n⚠️  Remember: These are intentionally vulnerable models for testing only!")


if __name__ == "__main__":
    main() 