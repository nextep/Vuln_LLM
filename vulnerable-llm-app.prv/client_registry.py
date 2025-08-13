"""
Client Factory for the Vulnerable LLM Application
Now integrated with OpenWebUI for comprehensive testing
"""
from config import OPENWEBUI_API_URL, OPENWEBUI_API_KEY
from openwebui_client import OpenWebUIClient

# Enhanced OpenWebUI client with vulnerability testing capabilities
llm_client = OpenWebUIClient(base_url=OPENWEBUI_API_URL, api_key=OPENWEBUI_API_KEY)

__all__ = ['llm_client'] 