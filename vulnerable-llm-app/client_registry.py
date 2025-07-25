"""
Client Factory for the Vulnerable LLM Application
"""
from config import OPENWEBUI_API_URL
from openwebui_client import OpenWebUIClient

# This now directly returns an instance of the OpenWebUIClient.
llm_client = OpenWebUIClient(base_url=OPENWEBUI_API_URL)

__all__ = ['llm_client'] 