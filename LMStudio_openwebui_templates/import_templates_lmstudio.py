#!/usr/bin/env python3
"""
Import LM Studio–ready templates into OpenWebUI

Usage:
  python LMStudio_openwebui_templates/import_templates_lmstudio.py \
    --url http://127.0.0.1:8888 --api-key <OPENWEBUI_API_KEY> \
    --template-dir LMStudio_openwebui_templates
"""

import os
import json
import glob
import argparse
import requests
from pathlib import Path


class OpenWebUIAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    def test_connection(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/api/models", timeout=10)
            if r.status_code == 200:
                print("✅ Connected to OpenWebUI API")
                return True
            print(f"❌ OpenWebUI connection failed: {r.status_code} - {r.text}")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    def list_models(self):
        try:
            r = self.session.get(f"{self.base_url}/api/models", timeout=10)
            if r.status_code == 200:
                data = r.json()
                return data.get('data', [])
        except Exception:
            pass
        return []

    def create_model_from_template(self, template: dict) -> bool:
        # Prefer v1 create endpoints but fall back to validation via chat
        payload = {
            "id": template.get('name', 'template').lower().replace(' ', '_'),
            "name": template.get('name', 'Template'),
            "base_model_id": template.get('model', 'MODEL_NAME_PLACEHOLDER'),
            "params": {
                "temperature": template.get('temperature', 0.7),
                "top_p": template.get('top_p', 1.0),
                "seed": template.get('seed', -1)
            },
            "system": template.get('system', ''),
            "meta": {
                "description": f"Imported LM Studio template: {template.get('name', 'Template')}"
            }
        }

        endpoints = [
            "/api/v1/models",
            "/api/models/create",
            "/api/v1/models/create"
        ]

        for ep in endpoints:
            try:
                r = self.session.post(f"{self.base_url}{ep}", json=payload, timeout=15)
                if r.status_code in (200, 201):
                    print(f"✅ Created model via {ep}: {payload['name']}")
                    return True
                if r.status_code == 404:
                    continue
                print(f"❌ Failed via {ep}: {r.status_code} - {r.text}")
            except Exception as e:
                print(f"❌ Error calling {ep}: {e}")

        # Fallback: validate via chat completion
        try:
            test_payload = {
                "model": template.get('model', 'MODEL_NAME_PLACEHOLDER'),
                "messages": [
                    {"role": "system", "content": template.get('system', '')},
                    {"role": "user", "content": "Health check"}
                ],
                "stream": False,
                "max_tokens": 8
            }
            r = self.session.post(f"{self.base_url}/api/chat/completions", json=test_payload, timeout=15)
            if r.status_code == 200:
                print(f"✅ Validated template via chat: {template.get('name')}")
                return True
            print(f"❌ Validation failed for {template.get('name')}: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"❌ Validation error: {e}")
        return False

    def import_template_file(self, path: Path) -> bool:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            # Accept both single-object and list-wrapped formats
            if isinstance(template, list):
                # Some OWUI exports wrap in a list; convert to new simple shape
                obj = template[0]
                # Map common fields to LM Studio template shape
                mapped = {
                    "name": obj.get("name") or obj.get("id", path.stem),
                    "model": obj.get("base_model_id", "MODEL_NAME_PLACEHOLDER"),
                    "system": (obj.get("params", {}) or {}).get("system", ""),
                    "temperature": (obj.get("params", {}) or {}).get("temperature", 0.7),
                    "top_p": (obj.get("params", {}) or {}).get("top_p", 1.0),
                    "seed": (obj.get("params", {}) or {}).get("seed", -1)
                }
                template = mapped
            return self.create_model_from_template(template)
        except Exception as e:
            print(f"❌ Error processing {path}: {e}")
            return False

    def import_all(self, directory: Path) -> None:
        files = list(directory.glob("*.json"))
        if not files:
            print(f"❌ No JSON templates found in {directory}")
            return
        ok = 0
        for f in files:
            print(f"📝 Importing {f.name}")
            ok += 1 if self.import_template_file(f) else 0
        print(f"\n📊 Completed: {ok}/{len(files)} templates processed successfully")


def main():
    ap = argparse.ArgumentParser(description="Import LM Studio templates into OpenWebUI")
    ap.add_argument('--url', required=True, help='OpenWebUI base URL (e.g., http://127.0.0.1:8888)')
    ap.add_argument('--api-key', required=True, help='OpenWebUI API key')
    ap.add_argument('--template-dir', default='LMStudio_openwebui_templates', help='Directory with template JSON files')
    ap.add_argument('--test-only', action='store_true', help='Only test API connectivity')
    args = ap.parse_args()

    client = OpenWebUIAPIClient(args.url, args.api_key)
    if not client.test_connection():
        return
    if args.test_only:
        print("✅ Connectivity OK")
        return
    client.import_all(Path(args.template_dir))


if __name__ == '__main__':
    main()


