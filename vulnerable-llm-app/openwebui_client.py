import requests
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OpenWebUIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.completions_endpoint = f"{self.base_url}/chat/completions"
        self.logger = logging.getLogger(__name__)

    def call_vulnerable_model(self, 
                             model_tag: str,
                             system_prompt: str,
                             user_prompt: str,
                             **kwargs) -> Dict[str, Any]:
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        api_params = {
            "model": model_tag,
            "messages": messages,
            "stream": False,
            "temperature": kwargs.get('temperature', 0.8),
            # Add other OpenWebUI specific parameters here
        }
        
        try:
            response = requests.post(self.completions_endpoint, json=api_params, timeout=120)
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                return {'response': generated_text}
            else:
                return {'error': f"API returned status {response.status_code}", 'details': response.text}
        except Exception as e:
            return {'error': str(e)}

    def health_check(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.base_url.replace('/v1', '')}/health", timeout=10)
            if response.status_code == 200:
                return {'status': 'healthy'}
            return {'status': 'unhealthy'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)} 