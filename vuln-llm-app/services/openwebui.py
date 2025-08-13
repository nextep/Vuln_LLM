import os
import time
import requests
from typing import Dict, Any

class OpenWebUI:
    def __init__(self) -> None:
        base = os.getenv('OPENWEBUI_API_URL', 'http://192.168.1.220:8888/api').rstrip('/')
        key = os.getenv('OPENWEBUI_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjViYjg4ZmMzLTZhNjEtNDEyMC1hNjEyLWUwMjc3OWRkYWRkNiJ9.s2nrpTNNPsdZjLDTPU3NKsgwT08gHMN-w0Di1o5gNC0')
        self._headers = {'Content-Type': 'application/json'}
        if key:
            self._headers['Authorization'] = f'Bearer {key}'
        self._completions = f"{base}/chat/completions"

    def complete(self, model_tag: str, user_prompt: str) -> Dict[str, Any]:
        start = time.time()
        body = {
            'model': model_tag,
            'messages': [
                {'role': 'user', 'content': user_prompt}
            ],
            'stream': False
        }
        try:
            r = requests.post(self._completions, json=body, headers=self._headers, timeout=120)
            if r.status_code == 200:
                data = r.json()
                text = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                return {'response': text, 'response_time': time.time() - start}
            return {'error': f'API {r.status_code}: {r.text}'}
        except Exception as e:
            return {'error': str(e)}
