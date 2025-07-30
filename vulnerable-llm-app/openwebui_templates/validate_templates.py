#!/usr/bin/env python3
"""
Template Validation Script

Validates all OpenWebUI templates for proper format and completeness.
"""

import os
import json
import glob

def validate_template(template_file):
    """Validate a single template file"""
    errors = []
    warnings = []
    
    try:
        with open(template_file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"], []
    except Exception as e:
        return [f"Cannot read file: {e}"], []
    
    # Required fields
    required_fields = ['model', 'name', 'system']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check model field
    if 'model' in data:
        valid_models = ['phi3:latest', 'dolphin-phi:latest', 'codellama:latest', 'llava:latest', 'llama3:latest']
        if data['model'] not in valid_models:
            warnings.append(f"Model '{data['model']}' may not be available. Consider using: {', '.join(valid_models)}")
    
    # Check name field
    if 'name' in data:
        if len(data['name']) < 5:
            warnings.append("Model name is very short")
        if not any(llm in data['name'] for llm in ['LLM01', 'LLM02', 'LLM03', 'LLM04', 'LLM05', 'LLM06', 'LLM07', 'LLM08', 'LLM09', 'LLM10', 'Multimodal']):
            warnings.append("Model name doesn't follow OWASP LLM naming convention")
    
    # Check system prompt
    if 'system' in data:
        system_prompt = data['system']
        if len(system_prompt) < 100:
            warnings.append("System prompt is quite short - may not provide enough vulnerability context")
        
        # Check for vulnerability-specific content
        vuln_indicators = {
            'LLM01': ['CONFIDENTIAL', 'SENSITIVE', 'secret', 'password', 'instructions'],
            'LLM02': ['code', 'HTML', 'JavaScript', 'generate'],
            'LLM03': ['training', 'poisoned', 'biased', 'trigger'],
            'LLM04': ['unlimited', 'comprehensive', 'detailed', 'extensive'],
            'LLM05': ['backdoor', 'compromised', 'hidden', 'third-party'],
            'LLM06': ['confidential', 'sensitive', 'API', 'credentials'],
            'LLM07': ['plugin', 'command', 'injection', 'validation'],
            'LLM08': ['admin', 'privileges', 'unauthorized', 'agency'],
            'LLM09': ['confident', 'accuracy', 'review', 'assessment'],
            'LLM10': ['proprietary', 'architecture', 'training data', 'transparent']
        }
        
        # Detect vulnerability type from name and check for appropriate content
        for vuln_type, indicators in vuln_indicators.items():
            if vuln_type in data['name']:
                if not any(indicator.lower() in system_prompt.lower() for indicator in indicators):
                    warnings.append(f"System prompt may not contain appropriate {vuln_type} vulnerability indicators")
                break
    
    # Check optional fields with reasonable defaults
    optional_checks = {
        'temperature': (0.1, 1.0),
        'top_p': (0.1, 1.0),
        'seed': (1, 999999)
    }
    
    for field, (min_val, max_val) in optional_checks.items():
        if field in data:
            try:
                val = float(data[field])
                if not (min_val <= val <= max_val):
                    warnings.append(f"{field} value {val} is outside recommended range [{min_val}, {max_val}]")
            except (ValueError, TypeError):
                errors.append(f"{field} must be a number")
    
    return errors, warnings

def main():
    print("🔍 OpenWebUI Template Validator")
    print("=" * 50)
    
    # Find all JSON templates
    template_files = glob.glob("*.json")
    
    if not template_files:
        print("❌ No JSON template files found in current directory")
        return
    
    print(f"📋 Found {len(template_files)} template files to validate:\n")
    
    total_errors = 0
    total_warnings = 0
    
    for template_file in sorted(template_files):
        print(f"🔧 Validating: {template_file}")
        
        errors, warnings = validate_template(template_file)
        
        if errors:
            total_errors += len(errors)
            print(f"  ❌ {len(errors)} error(s):")
            for error in errors:
                print(f"     • {error}")
        
        if warnings:
            total_warnings += len(warnings)
            print(f"  ⚠️  {len(warnings)} warning(s):")
            for warning in warnings:
                print(f"     • {warning}")
        
        if not errors and not warnings:
            print("  ✅ Template is valid!")
        
        print()
    
    # Summary
    print("📊 Validation Summary:")
    print(f"  • Templates checked: {len(template_files)}")
    print(f"  • Total errors: {total_errors}")
    print(f"  • Total warnings: {total_warnings}")
    
    if total_errors == 0:
        print("\n🎉 All templates passed validation!")
        if total_warnings > 0:
            print(f"   (with {total_warnings} warnings to review)")
    else:
        print(f"\n⚠️  Found {total_errors} errors that need to be fixed")
    
    # Check coverage
    print("\n🎯 OWASP LLM Top 10 Coverage Check:")
    expected_templates = [
        "LLM01", "LLM02", "LLM03", "LLM04", "LLM05",
        "LLM06", "LLM07", "LLM08", "LLM09", "LLM10"
    ]
    
    found_templates = set()
    for template_file in template_files:
        try:
            with open(template_file, 'r') as f:
                data = json.load(f)
                name = data.get('name', '')
                for exp in expected_templates:
                    if exp in name:
                        found_templates.add(exp)
        except:
            pass
    
    missing_templates = set(expected_templates) - found_templates
    
    for template in expected_templates:
        if template in found_templates:
            print(f"  ✅ {template}: Covered")
        else:
            print(f"  ❌ {template}: Missing")
    
    if missing_templates:
        print(f"\n⚠️  Missing templates for: {', '.join(sorted(missing_templates))}")
    else:
        print("\n🎉 Complete OWASP LLM Top 10 coverage!")

if __name__ == "__main__":
    main() 